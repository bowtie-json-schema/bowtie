from __future__ import annotations

from collections import deque
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Protocol
import asyncio
import json

from attrs import field, frozen, mutable
import aiodocker.containers
import aiodocker.docker
import aiodocker.exceptions
import aiodocker.stream

from bowtie import _commands, exceptions

if TYPE_CHECKING:
    from bowtie._report import Reporter


@frozen
class GotStderr(Exception):
    stderr: bytes


@frozen
class StartupFailed(Exception):
    name: str
    stderr: str = ""
    data: Any = None

    def __str__(self) -> str:
        if self.stderr:
            return f"{self.name}'s stderr contained: {self.stderr}"
        return self.name


@frozen
class NoSuchImage(Exception):
    name: str
    data: Any = None


class StreamClosed(Exception):
    pass


@mutable
class Stream:
    """
    Wrapper to make aiodocker's Stream more pleasant to use.
    """

    _stream: aiodocker.stream.Stream = field(alias="stream")
    _container: aiodocker.containers.DockerContainer = field(alias="container")
    _read_timeout_sec: float | None = field(alias="read_timeout_sec")
    _buffer: deque[bytes] = field(factory=deque, alias="buffer")
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

    def send(self, message: dict[str, Any]) -> Awaitable[None]:
        as_bytes = f"{json.dumps(message)}\n".encode()
        return self._stream.write_in(as_bytes)

    async def receive(self) -> bytes:
        if self._buffer:
            return self._buffer.popleft()

        while True:
            message: aiodocker.stream.Message | None = (
                await self._read_with_timeout()
            )
            if message is not None:
                break
            info: dict[str, Any] = await self._container.show()  # type: ignore[reportUnknownMemberType]  # noqa: E501
            if info["State"]["FinishedAt"]:
                raise StreamClosed(self)

        if message.stream == 2:  # type: ignore[reportUnknownMemberType]
            data: list[bytes] = []

            while message.stream == 2:  # type: ignore[reportUnknownMemberType]  # noqa: E501
                data.append(message.data)  # type: ignore[reportUnknownMemberType]  # noqa: E501
                message = await self._read_with_timeout()
                if message is None:
                    raise GotStderr(b"".join(data))

        line: bytes
        rest: list[bytes]
        while True:
            line, *rest = message.data.split(b"\n")  # type: ignore[reportUnknownMemberType]  # noqa: E501
            if rest:
                line, self._last = self._last + line, rest.pop()  # type: ignore[reportUnknownVariableType]  # noqa: E501
                self._buffer.extend(rest)
                return line  # type: ignore[reportUnknownVariableType]  # noqa: E501

            message = None
            while message is None:
                message = await self._read_with_timeout()
            self._last += line


@frozen
class DialectRunner:
    _name: str = field(alias="name")
    _dialect: str = field(alias="dialect")
    _send: Callable[[_commands.Command[Any]], Awaitable[Any]] = field(
        alias="send",
    )
    _start_response: _commands.StartedDialect = field(alias="start_response")

    @classmethod
    async def start(
        cls,
        send: Callable[[_commands.Command[Any]], Awaitable[Any]],
        dialect: str,
        name: str,
    ) -> DialectRunner:
        return cls(
            name=name,
            send=send,
            dialect=dialect,
            start_response=await send(_commands.Dialect(dialect=dialect)),  # type: ignore[reportGeneralTypeIssues]  # noqa: E501  uh?? no idea what's going on here.
        )

    def warn_if_unacknowledged(self, reporter: Reporter):
        if self._start_response != _commands.StartedDialect.OK:
            reporter.unacknowledged_dialect(
                implementation=self._name,
                dialect=self._dialect,
                response=self._start_response,
            )

    async def run_case(
        self,
        seq: int,
        case: _commands.TestCase,
    ) -> _commands.ReportableResult:
        command = _commands.Run(seq=seq, case=case.without_expected_results())
        try:
            expected = [test.valid for test in case.tests]
            response = await self._send(command)  # type: ignore[reportGeneralTypeIssues]  # noqa: E501  uh?? no idea what's going on here.
            if response is None:
                return _commands.Empty(implementation=self._name)
            return response(implementation=self._name, expected=expected)
        except GotStderr as error:
            return _commands.CaseErrored.uncaught(
                seq=seq,
                implementation=self._name,
                stderr=error.stderr.decode("utf-8"),
            )


class _MakeValidator(Protocol):
    def __call__(self, dialect: str | None = None) -> Callable[..., None]:
        ...


@mutable
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    _make_validator: _MakeValidator = field(alias="make_validator")
    _maybe_validate: Callable[..., None] = field(alias="maybe_validate")
    _reporter: Reporter = field(alias="reporter")

    _docker: aiodocker.docker.Docker = field(repr=False, alias="docker")
    _restarts: int = field(default=20, repr=False, alias="restarts")
    _container: aiodocker.containers.DockerContainer = field(
        default=None,
        repr=False,
        alias="container",
    )
    _stream: Stream = field(default=None, repr=False, alias="stream")
    _read_timeout_sec: float | None = field(
        default=2.0,
        converter=lambda value: value or None,  # type: ignore[reportUnknownArgumentType]  # noqa: E501
        repr=False,
    )

    metadata: dict[str, Any] | None = None

    # FIXME: Still some refactoring into DialectRunner needed.
    _dialect: str = None  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        image_name: str,
        make_validator: _MakeValidator,
        **kwargs: Any,
    ) -> AsyncIterator[Implementation]:
        self = cls(
            name=image_name,
            make_validator=make_validator,
            maybe_validate=make_validator(),
            **kwargs,
        )

        try:
            await self._start_container()
        except GotStderr as error:
            raise StartupFailed(name=image_name, stderr=error.stderr.decode())
        except StreamClosed:
            raise StartupFailed(name=image_name)
        except aiodocker.exceptions.DockerError as error:
            status, data, *_ = error.args  # :/
            if data.get("cause") == "image not known" or status == 500:
                raise NoSuchImage(name=image_name, data=data)
            raise StartupFailed(name=image_name, data=data)

        yield self
        with suppress(GotStderr):  # XXX: Log this too?
            await self._stop()
        with suppress(aiodocker.exceptions.DockerError):
            await self._container.delete(force=True)  # type: ignore[reportUnknownMemberType]  # noqa: E501

    async def _start_container(self):
        self._container = await self._docker.containers.run(  # type: ignore[reportUnknownMemberType]  # noqa: E501
            config=dict(
                Image=self.name,
                OpenStdin=True,
                HostConfig=dict(NetworkMode="none"),  # type: ignore[reportUnknownArgumentType]  # noqa: E501
            ),
        )
        self._stream = Stream.attached_to(
            self._container,
            read_timeout_sec=self._read_timeout_sec,
        )
        started = await self._send(_commands.START_V1)  # type: ignore[reportGeneralTypeIssues]  # noqa: E501  uh?? no idea what's going on here.
        if started is None:
            return
        self.metadata = started.implementation

    async def _restart_container(self):
        self._restarts -= 1
        await self._container.delete(force=True)  # type: ignore[reportUnknownMemberType]  # noqa: E501
        await self._start_container()
        await self.start_speaking(dialect=self._dialect)

    @property
    def dialects(self):
        if self.metadata is None:
            raise StartupFailed(name=self.name)
        return self.metadata.get("dialects", [])

    def start_speaking(self, dialect: str) -> Awaitable[DialectRunner]:
        self._dialect = dialect
        self._maybe_validate = self._make_validator(dialect)
        return DialectRunner.start(
            name=self.name,
            send=self._send,
            dialect=dialect,
        )

    async def _stop(self):
        await self._send_no_response(_commands.STOP)  # type: ignore[reportGeneralTypeIssues]  # noqa: E501  uh?? no idea what's going on here.

    async def _send_no_response(self, cmd: _commands.Command[Any]):
        request = cmd.to_request(validate=self._maybe_validate)

        try:
            await self._stream.send(request)
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.send(request)

    async def _send(self, cmd: _commands.Command[Any], retry: int = 3) -> Any:
        await self._send_no_response(cmd)
        for _ in range(retry):
            try:
                response = await self._stream.receive()
            except asyncio.exceptions.TimeoutError:
                continue

            try:
                return cmd.from_response(
                    response=response,
                    validate=self._maybe_validate,
                )
            except exceptions._ProtocolError as error:  # type: ignore[reportPrivateUsage]  # noqa: E501
                self._reporter.invalid_response(
                    error=error,
                    implementation=self,
                    response=response,
                    cmd=cmd,
                )
