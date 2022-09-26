from __future__ import annotations

from collections import deque
from contextlib import asynccontextmanager
from importlib import resources
import asyncio
import json

import aiodocker
import attrs

from bowtie import _commands


@attrs.define
class InvalidResponse:
    """
    An implementation sent an invalid response to a command.
    """

    succeeded = False

    exc_info: Exception
    response: dict


@attrs.define
class GotStderr(Exception):

    stderr: bytes


@attrs.define
class BackingOff:
    """
    An implementation has failed too many times.
    """

    succeeded = False

    implementation: str

    def report(self, reporter):
        reporter.backoff(implementation=self.implementation)


@attrs.define
class UncaughtError:
    """
    An implementation spewed to its stderr.
    """

    implementation: str
    stderr: bytes

    succeeded = False

    def report(self, reporter):
        reporter.errored_uncaught(
            implementation=self.implementation,
            stderr=self.stderr,
        )


@attrs.define
class Empty:
    """
    We didn't get a response.
    """

    implementation: str

    succeeded = False

    def report(self, reporter):
        reporter.errored_uncaught(
            implementation=self.implementation,
            reason="Empty response.",
        )


@attrs.define
class Stream:
    """
    Wrapper to make aiodocker's Stream more pleasant to use.
    """

    _stream: aiodocker.stream.Stream
    _buffer: deque[bytes] = attrs.field(factory=deque)
    _last: bytes = b""

    @classmethod
    def attached_to(cls, container):
        stream = container.attach(stdin=True, stdout=True, stderr=True)
        return cls(stream=stream)

    def _read_with_timeout(self, timeout_sec=2.0):
        return asyncio.wait_for(self._stream.read_out(), timeout=timeout_sec)

    def send(self, message):
        as_bytes = f"{json.dumps(message)}\n".encode("utf-8")
        return self._stream.write_in(as_bytes)

    async def receive(self):
        if self._buffer:
            return json.loads(self._buffer.popleft())

        message = None
        while message is None:
            message = await self._read_with_timeout()

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


@attrs.define(hash=True, slots=False)
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    _maybe_validate: callable

    _docker: aiodocker.Docker = attrs.field(repr=False)
    _restarts: int = attrs.field(default=20 + 1, repr=False)

    _container: aiodocker.containers.DockerContainer = attrs.field(
        default=None, repr=False,
    )
    _stream: aiodocker.stream.Stream = attrs.field(default=None, repr=False)

    metadata: dict = {}

    _dialect = None

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name, validate_implementations):
        if validate_implementations:
            from jsonschema.validators import RefResolver, validator_for

            text = resources.read_text("bowtie.schemas", "io-schema.json")
            root_schema = json.loads(text)
            resolver = RefResolver.from_schema(root_schema)
            Validator = validator_for(root_schema)
            Validator.check_schema(root_schema)

            def validate(instance, schema):
                resolver.store["urn:current-dialect"] = {"$ref": self._dialect}
                Validator(schema, resolver=resolver).validate(instance)
        else:
            def validate(instance, schema):
                pass

        self = cls(name=image_name, docker=docker, maybe_validate=validate)
        try:
            await self._restart_container()
            yield self
            await self._stop()
        finally:
            try:
                await self._container.delete(force=True)
            except aiodocker.exceptions.DockerError:
                pass

    async def _restart_container(self):
        self._restarts -= 1

        if self._container is not None:
            await self._container.delete(force=True)
        self._container = await self._docker.containers.create(
            config=dict(Image=self.name, OpenStdin=True),
        )
        await self._container.start()
        self._stream = Stream.attached_to(self._container)
        self.metadata = await self._send(_commands.START_V1)

    def supports_dialect(self, dialect):
        return dialect in self.metadata.get("dialects", [])

    async def start_speaking(self, dialect):
        self._dialect = dialect
        return await self._send(_commands.Dialect(dialect=dialect))

    async def run_case(self, seq, case):
        if self._restarts <= 0:
            return BackingOff(implementation=self.name)

        command = _commands.Run(seq=seq, case=case.without_expected_results())
        try:
            response = await self._send(command)
            expected = [test.valid for test in case.tests]
            return response(implementation=self.name, expected=expected)
        except GotStderr as error:
            return UncaughtError(implementation=self.name, stderr=error.stderr)

    async def _stop(self):
        if self._restarts > 0:
            await self._send(_commands.STOP, retry=0)

    async def _send(self, cmd, retry=3):
        request = _commands.to_request(cmd)
        schema = {"$ref": f"#/$defs/command/$defs/{cmd.cmd}"}
        self._maybe_validate(instance=request, schema=schema)

        try:
            await self._stream.send(request)
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.send(request)

        for _ in range(retry):
            try:
                data = await self._stream.receive()
            except asyncio.exceptions.TimeoutError:
                continue

            pointer = f"#/$defs/command/$defs/{cmd.cmd}/$defs/response"
            self._maybe_validate(instance=data, schema={"$ref": pointer})
            return cmd.succeed(cmd.Response(**data))
        return lambda *args, **kwargs: Empty(implementation=self.name)
