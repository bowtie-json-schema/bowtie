"""
Speaking to harnesses which run inside containers.

The awkward parts of actually driving a container engine live in
`imaged`, which knows nothing of Bowtie.
What's left here is Bowtie's own concerns -- when to restart a
container, when to retry a request, and what to make of a harness which
writes to standard error.
"""

from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from os import environ
from typing import TYPE_CHECKING
import json

from attrs import field, frozen, mutable
from imaged import (
    Engine,
    EngineError,
    EngineNotRunning,
    NoSuchEngine,
    NoSuchImage,
    Session,
    SessionClosed,
    Unsupported,
)
import anyio

from bowtie._core import InvalidResponse, Restarted
from bowtie.exceptions import (
    CannotConnect,
    GotStderr,
    NoSuchImplementation,
    StartupFailed,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Awaitable, Callable

    from bowtie._commands import Message


IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"

_NO_ENGINE = (
    "Bowtie couldn't find a container engine. "
    "Install docker, podman or container, and ensure a container "
    "successfully starts if you run one directly outside of Bowtie."
)


def _not_running(engine: str) -> str:
    return (
        f"Bowtie found {engine}, but it doesn't seem to be running. "
        "Start it -- along with whatever VM or service it needs, if "
        "you're on macOS -- and check that a container starts if you "
        "run one directly outside of Bowtie."
    )


@mutable
class Connection:
    """
    A connection with a restartable container over stdio.

    Requests and responses are JSON-serializable messages, with
    serialization handled here.
    """

    _new_session: Callable[[], Awaitable[Session]] = field(
        repr=False,
        alias="new_session",
    )

    #: An explicit timeout to wait for the harness to respond to each
    #: request, or `None` to wait forever -- though note that this does
    #: mean ... forever!
    _read_timeout_sec: float | None = field(
        default=2.0,
        repr=False,
        alias="read_timeout_sec",
    )

    # Maybe second versions of these will be useful also at the
    # Implementation level again, to control for non-protocol-related
    # flakiness or slowness
    _restarts: int = field(default=10, repr=False, alias="restarts")

    #: A per-request number of retries, before giving up
    _retry: int = field(default=3, repr=False)

    _connected_to: Session | None = None

    @property
    async def _session(self) -> Session:
        if self._connected_to is None:
            self._connected_to = await self._new_session()
        return self._connected_to

    async def request(self, message: Message) -> Message | None:
        session = await self._session

        try:
            await session.send(json.dumps(message))
        except SessionClosed:
            self._restarts -= 1
            self._connected_to = None
            raise Restarted() from None

        for _ in range(self._retry):
            try:
                with anyio.fail_after(self._read_timeout_sec):
                    response = await session.receive()
            except TimeoutError:
                # A harness which has said something on standard error
                # and then gone quiet is telling us why it won't answer.
                stderr = session.stderr()
                if stderr:
                    raise GotStderr(stderr)
                continue
            except SessionClosed as err:
                if err.stderr:
                    raise GotStderr(err.stderr)
                return

            try:
                return json.loads(response)
            except json.JSONDecodeError as err:
                raise InvalidResponse(contents=response) from err


def _float_or_none(value: str | float | None) -> float | None:
    """
    Coerce 0 to None, otherwise return a float.
    """
    if value is None:
        return value
    value = float(value)
    if value:
        return value
    return None


def engine() -> Engine:
    """
    The container engine to speak to.

    `BOWTIE_ENGINE` names which one to use, which matters when more than
    one is installed, and which is how we check that Bowtie behaves the
    same way on all of them.
    """
    chosen = environ.get("BOWTIE_ENGINE")
    return Engine.named(chosen) if chosen else Engine.detect()


def _engine(kind: str, id: str) -> Engine:
    """
    Find something able to run containers, or explain that we couldn't.
    """
    try:
        return engine()
    except NoSuchEngine as err:
        raise CannotConnect(kind=kind, id=id, hint=_NO_ENGINE) from err


@frozen(kw_only=True)
class ConnectableImage:
    _id: str = field(
        converter=lambda value: (
            value if "/" in value else f"{IMAGE_REPOSITORY}/{value}"
        ),
        alias="id",
    )

    #: An explicit timeout to wait for each implementation to respond
    #: to *each* instance being validated. Set this to 0 if you wish
    #: to wait forever, though note that this means you may end up waiting
    #: ... forever!
    _read_timeout_sec: float | None = field(
        default=2.0,
        converter=_float_or_none,
        repr=False,
        alias="read_timeout_sec",
    )

    kind = "image"

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[Connection]:
        engine = _engine(kind=self.kind, id=self._id)

        async with AsyncExitStack() as stack:
            # Whatever we're speaking to right now, closed and replaced
            # on each restart so that dead containers don't pile up for
            # the lifetime of the connection.
            current = await stack.enter_async_context(AsyncExitStack())

            async def new_session():
                await current.aclose()

                try:
                    id = await engine.create_pulling_if_needed(
                        self._id,
                        network=False,
                    )
                except NoSuchImage as err:
                    raise NoSuchImplementation(self._id) from err
                except EngineNotRunning as err:
                    raise CannotConnect(
                        kind=self.kind,
                        id=self._id,
                        hint=_not_running(engine.name),
                    ) from err
                except EngineError as err:
                    # Anything else the engine couldn't manage is still a
                    # failure to start, which Bowtie knows how to show.
                    raise StartupFailed(id=self._id, data=str(err)) from err

                current.push_async_callback(engine.remove, id)
                return await current.enter_async_context(engine.start(id))

            yield Connection(
                new_session=new_session,
                read_timeout_sec=self._read_timeout_sec,
            )


@frozen(kw_only=True)
class ConnectableContainer:
    _id: str = field(alias="id")

    #: An explicit timeout to wait for each implementation to respond
    #: to *each* instance being validated. Set this to 0 if you wish
    #: to wait forever, though note that this means you may end up waiting
    #: ... forever!
    _read_timeout_sec: float | None = field(
        default=2.0,
        converter=_float_or_none,
        repr=False,
        alias="read_timeout_sec",
    )

    kind = "container"

    @asynccontextmanager
    async def connect(self) -> AsyncGenerator[Connection]:
        engine = _engine(kind=self.kind, id=self._id)

        if not engine.attaches:
            raise CannotConnect(
                kind=self.kind,
                id=self._id,
                hint=str(
                    Unsupported(
                        engine=engine.name,
                        operation="speak to an already running container",
                    ),
                ),
            )

        try:
            exists = await engine.exists(self._id)
        except EngineNotRunning as err:
            raise CannotConnect(
                kind=self.kind,
                id=self._id,
                hint=_not_running(engine.name),
            ) from err

        if not exists:
            raise CannotConnect(kind=self.kind, id=self._id)

        async with AsyncExitStack() as stack:
            # As above -- detach from the previous session before we go
            # making another one.
            current = await stack.enter_async_context(AsyncExitStack())

            async def new_session():
                await current.aclose()
                return await current.enter_async_context(
                    engine.attach(self._id),
                )

            yield Connection(
                new_session=new_session,
                read_timeout_sec=self._read_timeout_sec,
            )
