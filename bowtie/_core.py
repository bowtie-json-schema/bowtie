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
class GotStderr(Exception):

    stderr: bytes


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


@attrs.define
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
            return _commands.UncaughtError(
                implementation=self._name,
                stderr=error.stderr,
            )


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
    _stream: Stream = attrs.field(default=None, repr=False)

    metadata: dict = {}

    _dialect: DialectRunner | None = None

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
        started = await self._send(_commands.START_V1)
        self.metadata = started.implementation

    def supports_dialect(self, dialect):
        return dialect in self.metadata.get("dialects", [])

    async def start_speaking(self, dialect):
        self._dialect = dialect
        return await DialectRunner.start(
            name=self.name,
            send=self._send,
            dialect=dialect,
        )

    async def _stop(self):
        await self._send(_commands.STOP, retry=0)

    async def _send(self, cmd, retry=3):
        request = cmd.to_request(validate=self._maybe_validate)

        try:
            await self._stream.send(request)
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.send(request)

        for _ in range(retry):
            try:
                return cmd.from_response(
                    response=await self._stream.receive(),
                    validate=self._maybe_validate,
                )
            except asyncio.exceptions.TimeoutError:
                continue
