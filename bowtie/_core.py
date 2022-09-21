from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import resources
import asyncio
import json
import sys

import aiodocker
import attrs
import structlog

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


@attrs.define
class Test:

    description: str
    instance: object
    valid: bool | None = None


@attrs.define
class TestCase:

    description: str
    schema: object
    tests: list[Test]
    comment: str | None = None

    @classmethod
    def from_dict(cls, data):
        data["tests"] = [Test(**test) for test in data["tests"]]
        return cls(**data)

    def without_expected_results(self):
        as_dict = {
            "tests": [
                attrs.asdict(test, filter=lambda k, _: k.name != "valid")
                for test in self.tests
            ],
        }
        as_dict.update(
            attrs.asdict(
                self,
                filter=lambda k, v: k.name != "tests" and (
                    k.name != "comment" or v is not None
                ),
            ),
        )
        return as_dict


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


def writer(file=sys.stdout):
    return lambda **result: file.write(f"{json.dumps(result)}\n")


@attrs.define
class Reporter:

    _write = attrs.field(default=writer())
    _log: structlog.BoundLogger = attrs.field(factory=structlog.get_logger)

    def unsupported_dialect(self, implementation, dialect):
        self._log.warn(
            "Unsupported dialect, skipping implementation.",
            logger_name=implementation.name,
            dialect=dialect,
        )

    def unacknowledged_dialect(self, implementation, dialect, response):
        self._log.warn(
            (
                "Implicit dialect not acknowledged. "
                "Proceeding, but implementation may not have configured "
                "itself to handle schemas without $schema."
            ),
            logger_name=implementation.name,
            dialect=dialect,
            response=response,
        )

    def ready(self, implementations, dialect):
        metadata = {
            implementation.name: dict(
                implementation.metadata, image=implementation.name,
            ) for implementation in implementations
        }
        self._write(implementations=metadata)

    def will_speak(self, dialect):
        self._log.info("Will speak dialect", dialect=dialect)

    def finished(self, count):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)

    def case_started(self, seq, case):
        return _CaseReporter.case_started(
            case=case,
            seq=seq,
            write=self._write,
            log=self._log.bind(
                seq=seq,
                case=case.description,
                schema=case.schema,
            ),
        )


@attrs.define
class _CaseReporter:

    _write: callable
    _log: structlog.BoundLogger

    @classmethod
    def case_started(cls, log, write, case: TestCase, seq: int):
        self = cls(log=log, write=write)
        self._write(case=attrs.asdict(case), seq=seq)
        return self

    def got_results(self, results):
        self._write(**attrs.asdict(results))

    def backoff(self, implementation):
        self._log.warn("backing off", logger_name=implementation)

    def errored(self, implementation, response):
        self._log.error("", logger_name=implementation, **response)

    def errored_uncaught(self, implementation, **response):
        self._log.error("uncaught", logger_name=implementation, **response)


def report_on(input):
    """
    Create a structure suitable for the report template from an input file.
    """

    lines = (json.loads(line) for line in input)
    header = next(lines)
    implementations = header["implementations"]

    combined = {}

    for each in lines:
        if "case" in each:
            combined[each["seq"]] = {
                "case": each["case"],
                "results": [(test, {}) for test in each["case"]["tests"]],
            }
            continue

        implementation = each.pop("implementation")
        case = combined[each["seq"]]

        for result, expected, (_, seen) in zip(
            each["results"],
            each["expected"],
            case["results"],
        ):
            incorrect = expected is not None and result["valid"] != expected
            seen[implementation] = result, incorrect

    return dict(
        implementations=implementations.values(),
        results=[(v, k) for k, v in sorted(combined.items())],
    )
