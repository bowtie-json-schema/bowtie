from __future__ import annotations

from collections import deque
from contextlib import asynccontextmanager
import asyncio
import json

from attrs import field, frozen, mutable
import aiodocker

from bowtie import _commands, exceptions


@frozen
class GotStderr(Exception):

    stderr: bytes


@frozen
class StartupFailed(Exception):

    name: str


class StreamClosed(Exception):
    pass


@mutable
class Stream:
    """
    Wrapper to make aiodocker's Stream more pleasant to use.
    """

    _stream: aiodocker.stream.Stream
    _container: aiodocker.containers.DockerContainer
    _buffer: deque[bytes] = field(factory=deque)
    _last: bytes = b""

    @classmethod
    def attached_to(cls, container):
        stream = container.attach(stdin=True, stdout=True, stderr=True)
        return cls(stream=stream, container=container)

    def _read_with_timeout(self, timeout_sec=2.0):
        return asyncio.wait_for(self._stream.read_out(), timeout=timeout_sec)

    def send(self, message):
        as_bytes = f"{json.dumps(message)}\n".encode()
        return self._stream.write_in(as_bytes)

    async def receive(self):
        if self._buffer:
            return json.loads(self._buffer.popleft())

        while True:
            message = await self._read_with_timeout()
            if message is not None:
                break
            info = await self._container.show()
            if info["State"]["FinishedAt"]:
                raise StreamClosed(self)

        if message.stream == 2:
            data = []

            while message.stream == 2:
                data.append(message.data)
                message = await self._read_with_timeout()
                if message is None:
                    raise GotStderr(b"".join(data))

        while True:
            line, *rest = message.data.split(b"\n")
            if rest:
                line, self._last = self._last + line, rest.pop()
                self._buffer.extend(rest)
                return json.loads(line)

            message = None
            while message is None:
                message = await self._read_with_timeout()
            self._last += line


@frozen
class DialectRunner:

    _name: str
    _dialect: str
    _send: callable
    _start_response: _commands.StartedDialect

    @classmethod
    async def start(cls, send, dialect, name):
        return cls(
            name=name,
            send=send,
            dialect=dialect,
            start_response=await send(_commands.Dialect(dialect=dialect)),
        )

    def warn_if_unacknowledged(self, reporter):
        if self._start_response == _commands.StartedDialect.OK:
            return
        reporter.unacknowledged_dialect(
            implementation=self._name,
            dialect=self._dialect,
            response=self._start_response,
        )

    async def run_case(self, seq, case):
        command = _commands.Run(seq=seq, case=case.without_expected_results())
        try:
            expected = [test.valid for test in case.tests]
            response = await self._send(command)
            if response is None:
                return _commands.Empty(implementation=self._name)
            return response(implementation=self._name, expected=expected)
        except GotStderr as error:
            return _commands.CaseErrored.uncaught(
                seq=seq,
                implementation=self._name,
                stderr=error.stderr.decode("utf-8"),
            )


@mutable
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    _make_validator: callable
    _maybe_validate: callable
    _reporter: object

    _docker: aiodocker.Docker = field(repr=False)
    _restarts: int = field(default=20, repr=False)
    _container: aiodocker.containers.DockerContainer = field(
        default=None,
        repr=False,
    )
    _stream: Stream = field(default=None, repr=False)

    metadata: dict | None = None

    _dialect: DialectRunner | None = None

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name, make_validator, reporter):
        self = cls(
            name=image_name,
            docker=docker,
            make_validator=make_validator,
            maybe_validate=make_validator(),
            reporter=reporter,
        )

        try:
            await self._start_container()
        except (aiodocker.exceptions.DockerError, StreamClosed):
            raise StartupFailed(name=image_name)

        yield self
        try:
            await self._stop()
        except GotStderr:
            # XXX: Log this too?
            pass
        finally:
            try:
                await self._container.delete(force=True)
            except aiodocker.exceptions.DockerError:
                pass

    async def _start_container(self):
        self._container = await self._docker.containers.run(
            config=dict(
                Image=self.name,
                OpenStdin=True,
                HostConfig=dict(NetworkMode="none"),
            ),
        )
        self._stream = Stream.attached_to(self._container)
        started = await self._send(_commands.START_V1)
        if started is None:
            return
        self.metadata = started.implementation

    async def _restart_container(self):
        self._restarts -= 1
        await self._container.delete(force=True)
        await self._start_container()
        await self.start_speaking(dialect=self._dialect)

    @property
    def dialects(self):
        if self.metadata is None:
            raise StartupFailed(name=self.name)
        return self.metadata.get("dialects", [])

    def start_speaking(self, dialect):
        self._dialect = dialect
        self._maybe_validate = self._make_validator(dialect)
        return DialectRunner.start(
            name=self.name,
            send=self._send,
            dialect=dialect,
        )

    async def _stop(self):
        await self._send_no_response(_commands.STOP)

    async def _send_no_response(self, cmd):
        request = cmd.to_request(validate=self._maybe_validate)

        try:
            await self._stream.send(request)
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.send(request)

    async def _send(self, cmd, retry=3):
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
            except exceptions._ProtocolError as error:
                self._reporter.invalid_response(
                    error=error,
                    implementation=self,
                    response=response,
                    request=cmd,
                )
