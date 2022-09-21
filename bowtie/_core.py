from __future__ import annotations

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
class BadFraming:
    """
    We're confused about line endings.
    """

    data: bytes

    succeeded = False

    def report(self, reporter):
        reporter.errored_uncaught(
            implementation=self.implementation,
            data=self.data,
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


@attrs.define(hash=True, slots=False)
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    _maybe_validate: callable

    _docker: aiodocker.Docker = attrs.field(repr=False)
    _restarts: int = attrs.field(default=20 + 1, repr=False)
    _read_timeout_sec: float = attrs.field(default=2.0, repr=False)

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
        self._stream = self._container.attach(
            stdin=True,
            stdout=True,
            stderr=True,
        )
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
        response = await self._send(command)
        expected = [test.valid for test in case.tests]
        return response(implementation=self.name, expected=expected)

    async def _stop(self):
        if self._restarts > 0:
            await self._send(_commands.STOP)

    async def _send(self, cmd, retry=3):
        request = _commands.to_request(cmd)
        pointer = f"#/$defs/command/$defs/{cmd.cmd}"
        self._maybe_validate(instance=request, schema={"$ref": pointer})
        as_bytes = f"{json.dumps(request)}\n".encode("utf-8")

        try:
            await self._stream.write_in(as_bytes)
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.write_in(as_bytes)

        for _ in range(retry):
            try:
                message = await self._read_with_timeout()
                if message is None:
                    continue
            except asyncio.exceptions.TimeoutError:
                continue

            if message.stream == 2:
                data = []
                while message is not None and message.stream == 2:
                    data.append(message.data)
                    try:
                        message = await self._read_with_timeout()
                    except asyncio.exceptions.TimeoutError:
                        break
                return lambda *args, **kwargs: UncaughtError(
                    implementation=self.name,
                    stderr=b"".join(data),  # noqa: B023
                )

            data = message.data
            assert b"\n" not in message[:-1]
            while not data.endswith(b"\n"):
                try:
                    message = await self._read_with_timeout()
                except asyncio.exceptions.TimeoutError:
                    return lambda *args, **kwargs: BadFraming(  # noqa: B023
                        implementation=self.name,
                        data=b"".join(data),  # noqa: B023
                    )
                data += message.data
            try:
                data = json.loads(data)
            except json.JSONDecodeError:
                return lambda *args, **kwargs: BadFraming(
                    implementation=self.name,
                    data=b"".join(data),  # noqa: B023
                )
            else:
                pointer = f"#/$defs/command/$defs/{cmd.cmd}/$defs/response"
                self._maybe_validate(instance=data, schema={"$ref": pointer})
                return cmd.succeed(cmd.Response(**data))
        return lambda *args, **kwargs: Empty(implementation=self.name)

    def _read_with_timeout(self):
        return asyncio.wait_for(
            self._stream.read_out(),
            timeout=self._read_timeout_sec,
        )
