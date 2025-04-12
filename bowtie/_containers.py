"""
Clunky pepperings-over of communication with containers.

Some of this is warts from aiodocker, but mixed in with fun
special-to-this-package logic occasionally.
"""

from __future__ import annotations

from collections import deque
from contextlib import AsyncExitStack, asynccontextmanager
from typing import TYPE_CHECKING
import asyncio
import json

from aiodocker import Docker
from attrs import field, frozen, mutable
import aiodocker.exceptions

from bowtie._core import InvalidResponse, Restarted
from bowtie.exceptions import (
    CannotConnect,
    GotStderr,
    NoSuchImplementation,
    StartupFailed,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable
    from typing import Any

    import aiodocker.containers
    import aiodocker.stream  # noqa: TC004 ??? no it's not?

    from bowtie._commands import Message


IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"


@frozen
class _ClosedStream(Exception):
    """
    The stream is closed, and we tried to send something on it.

    This exception should never bubble out of this module, it should be handled
    by the connection.
    """

    container: aiodocker.containers.DockerContainer


@mutable
class Stream:
    """
    Wrapper to make aiodocker's Stream more pleasant to use.
    """

    _stream: aiodocker.stream.Stream = field(repr=False, alias="stream")
    _container: aiodocker.containers.DockerContainer = field(
        repr=False,
        alias="container",
    )
    _read_timeout_sec: float | None = field(
        repr=False,
        alias="read_timeout_sec",
    )
    _buffer: deque[bytes] = field(factory=deque[bytes], alias="buffer")
    _last: bytes = b""

    @classmethod
    def attached_to(
        cls,
        container: aiodocker.containers.DockerContainer,
        **kwargs: Any,
    ) -> Stream:
        stream = container.attach(stdin=True, stdout=True, stderr=True)
        return cls(stream=stream, container=container, **kwargs)

    def _read_with_timeout(self) -> Awaitable[aiodocker.stream.Message | None]:
        read = self._stream.read_out()
        return asyncio.wait_for(read, timeout=self._read_timeout_sec)

    async def send(self, message: str) -> None:
        try:  # aiodocker doesn't appear to properly report stream closure
            await self._stream.write_in(message.encode())
        except aiodocker.exceptions.DockerError as err:
            raise _ClosedStream(self._container) from err
        except (AssertionError, AttributeError):
            raise _ClosedStream(self._container) from None

    async def receive(self) -> str:
        if self._buffer:
            return self._buffer.popleft().decode()

        while True:
            try:
                message = await self._read_with_timeout()
            except asyncio.exceptions.TimeoutError:
                info: dict[str, Any] = await self._container.show()  # type: ignore[reportUnknownMemberType]
                if not info["State"]["Running"]:
                    raise _ClosedStream(self._container)
                raise

            if message is not None:
                break
            info: dict[str, Any] = await self._container.show()  # type: ignore[reportUnknownMemberType]
            if not info["State"]["Running"]:
                raise _ClosedStream(self._container)

        if message.stream == 2:  # noqa: PLR2004
            data: list[bytes] = []

            while message.stream == 2:  # noqa: PLR2004
                data.append(message.data)
                try:
                    message = await self._read_with_timeout()
                except asyncio.exceptions.TimeoutError:
                    message = None
                if message is None:
                    raise GotStderr(b"".join(data))

        line: bytes
        rest: list[bytes]
        while True:
            line, *rest = message.data.split(b"\n")
            if rest:
                line, self._last = self._last + line, rest.pop()
                self._buffer.extend(rest)
                return line.decode()

            message = None
            while message is None:
                message = await self._read_with_timeout()
            self._last += line


@mutable
class Connection:
    """
    A connection with a restartable container over stdio via request/responses.

    Requests and responses are JSON-serializable messages, with serialization
    handled here.
    """

    _new_stream: Callable[[], Awaitable[Stream]] = field(
        repr=False,
        alias="new_stream",
    )

    # Maybe second versions of these will be useful also at the Implementation
    # level again, to control for non-protocol-related flakiness or slowness
    _restarts: int = field(default=10, repr=False, alias="restarts")

    #: A per-request number of retries, before giving up
    _retry: int = field(default=3, repr=False)

    _connected_to: Stream | None = None

    @property
    async def _stream(self) -> Stream:
        if self._connected_to is None:
            self._connected_to = await self._new_stream()
        return self._connected_to

    async def request(self, message: Message) -> Message | None:
        request = f"{json.dumps(message)}\n"

        try:
            await (await self._stream).send(request)
        except _ClosedStream:
            self._restarts -= 1
            self._connected_to = None
            raise Restarted() from None

        for _ in range(self._retry):
            try:
                response = await (await self._stream).receive()
            except asyncio.exceptions.TimeoutError:
                continue
            except _ClosedStream as err:
                stderr: list[str] = await err.container.log(stderr=True)  # type: ignore[reportUnknownVariableType]
                if stderr:
                    raise GotStderr("".join(stderr).encode())
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
    async def connect(self) -> AsyncIterator[Connection]:
        async with AsyncExitStack() as stack:
            docker = await stack.enter_async_context(Docker())
            create = start_container_maybe_pull

            async def new_stream():
                nonlocal create

                try:
                    container = await create(
                        docker=docker,
                        image_name=self._id,
                    )
                except aiodocker.exceptions.DockerError as err:
                    if err.status != 900:  # noqa: PLR2004
                        raise
                    raise CannotConnect(
                        kind=self.kind,
                        id=self._id,
                        hint=(
                            "Can't connect to your container runtime "
                            "(e.g. podman or docker). "
                            "Ensure you have one installed, that you have "
                            "set the DOCKER_HOST environment variable if "
                            "needed, and that containers successfully start "
                            "if you directly run one outside of Bowtie."
                        ),
                    ) from err

                stack.push_async_callback(container.delete, force=True)  # type: ignore[reportUnknownMemberType]
                create = start_container

                try:
                    return Stream.attached_to(
                        container,
                        read_timeout_sec=self._read_timeout_sec,
                    )
                except GotStderr as error:
                    err = StartupFailed(
                        id=self._id,
                        stderr=error.stderr.decode(),
                    )
                    raise err from None
                except _ClosedStream:
                    raise StartupFailed(id=self._id) from None

            yield Connection(new_stream=new_stream)


async def start_container_maybe_pull(docker: Docker, image_name: str):
    # You would think we would use aiodocker's container.start() function
    # which essentially does the below. You would think wrong.
    # That function will pull the *entire* image repository if it ends up
    # pulling our harness image -- so here we reimplement it, but only
    # pull :latest when the image is missing.
    try:
        return await start_container(docker=docker, image_name=image_name)
    except aiodocker.exceptions.DockerError as err:
        if err.status != 404:  # noqa: PLR2004
            raise

        try:
            tag = image_name.partition(":")[2] or "latest"
            await docker.pull(from_image=image_name, tag=tag)
        except aiodocker.exceptions.DockerError as err:
            # This craziness can go wrong in various ways, none of them
            # machine parseable.

            status, data, *_ = err.args
            if data.get("cause") == "image not known":
                raise NoSuchImplementation(image_name) from err

            message = ghcr = data.get("message", "")

            if status == 500:  # noqa: PLR2004
                try:
                    # GitHub Registry saying an image doesn't exist as
                    # reported within GitHub Actions' version of Podman...
                    # This is some crazy string like:
                    #   Head "https://ghcr.io/v2/bowtie-json-schema/image-name/manifests/latest": denied  # noqa: E501
                    # with seemingly no other indication elsewhere and
                    # obviously no good way to detect this specific case
                    no_image = message.endswith('/latest": denied')
                except Exception:  # noqa: BLE001, S110
                    pass
                else:
                    if no_image:
                        raise NoSuchImplementation(image_name)

                try:
                    # GitHub Registry saying an image doesn't exist as
                    # reported locally via podman on macOS...

                    # message will be ... a JSON string !?! ...
                    error = json.loads(ghcr).get("message", "")
                except Exception:  # noqa: BLE001, S110
                    pass  # nonJSON / missing key
                else:
                    if "403 (forbidden)" in error.casefold():
                        raise NoSuchImplementation(image_name)

            raise StartupFailed(id=image_name, data=data) from err
        return await start_container(docker=docker, image_name=image_name)


async def start_container(docker: Docker, image_name: str):
    config = dict(
        Image=image_name,
        OpenStdin=True,
        HostConfig=dict(NetworkMode="none"),
    )
    container = await docker.containers.create(config=config)
    await container.start()  # type: ignore[reportUnknownMemberType]
    return container


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
    async def connect(self) -> AsyncIterator[Connection]:
        async with Docker() as docker:
            try:
                container = await docker.containers.get(self._id)  # type: ignore[reportUnknownMemberType]
            except aiodocker.exceptions.DockerError as err:
                raise CannotConnect(kind=self.kind, id=self._id) from err

            async def new_stream():
                return Stream.attached_to(
                    container,
                    read_timeout_sec=self._read_timeout_sec,
                )

            yield Connection(new_stream=new_stream)
