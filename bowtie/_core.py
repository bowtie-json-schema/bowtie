from contextlib import asynccontextmanager
from textwrap import indent
import asyncio
import json
import sys

from attrs import define, field
import aiodocker
import structlog


class StartError(Exception):
    """
    An implementation failed to start properly.
    """


class UnsupportedDialect(Exception):
    """
    An implementation doesn't support the dialect in use for test cases.
    """

    def __init__(self, implementation, dialect):
        super().__init__(implementation, dialect)
        self.implementation = implementation
        self.dialect = dialect

    def __str__(self):
        return f"{self.implementation.name} does not support {self.dialect}."


@define
class Response:
    """
    An implementation sent a response, though it may still indicate an error.
    """

    implementation: str
    contents: dict

    succeeded = True

    def report(self, reporter):
        if "errored" in self.contents:
            report = reporter.errored
        else:
            report = reporter.got_results

        report(self.implementation, self.contents)


@define
class BackingOff:
    """
    An implementation has failed too many times.
    """

    succeeded = False

    implementation: str

    def report(self, reporter):
        reporter.backoff(implementation=self.implementation)


@define
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


@define
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


@define
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


@define(hash=True)
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    _docker: aiodocker.Docker = field(repr=False)
    _restarts: int = field(default=20 + 1, repr=False)
    _read_timeout_sec: float = field(default=2.0, repr=False)

    _container: aiodocker.containers.DockerContainer = field(
        default=None, repr=False,
    )
    _stream: aiodocker.stream.Stream = field(default=None, repr=False)

    metadata: dict = {}

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name, dialect):
        try:
            self = cls(name=image_name, docker=docker)
            metadata = await self._restart_container()
            if dialect not in metadata["dialects"]:
                raise UnsupportedDialect(implementation=self, dialect=dialect)
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
        self.metadata = await self._start()
        return self.metadata

    async def _start(self):
        response = await self._send(cmd="start", version=1)

        if not response.succeeded:
            raise StartError(
                f"{self.name} failed on startup. Stderr contained:\n\n"
                f"{indent(response.get('stderr', b'').decode(), '  ')}",
            )

        if not response.contents.get("ready"):
            raise StartError(f"{self.name} is not ready!")
        elif response.contents.get("version") != 1:
            raise StartError(f"{self.name} did not speak version 1!")

        return response.contents.get("implementation", {})

    async def run_case(self, seq, case):
        if self._restarts <= 0:
            return BackingOff(implementation=self.name)
        return await self._send(cmd="run", seq=seq, case=case)

    async def _stop(self):
        if self._restarts > 0:
            await self._send(cmd="stop")

    async def _send(self, **kwargs):
        cmd = f"{json.dumps(kwargs)}\n"
        try:
            await self._stream.write_in(cmd.encode("utf-8"))
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            await self._restart_container()
            await self._stream.write_in(cmd.encode("utf-8"))
        return await self._recv()

    async def _recv(self, retry=3):
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
                return UncaughtError(
                    implementation=self.name,
                    stderr=b"".join(data),
                )

            data = message.data
            assert b"\n" not in message[:-1]
            while not data.endswith(b"\n"):
                try:
                    message = await self._read_with_timeout()
                except asyncio.exceptions.TimeoutError:
                    return BadFraming(
                        implementation=self.name,
                        data=b"".join(data),
                    )
                data += message.data
            try:
                return Response(
                    implementation=self.name,
                    contents=json.loads(data),
                )
            except json.JSONDecodeError:
                return BadFraming(
                    implementation=self.name,
                    data=b"".join(data),
                )
        return Empty(implementation=self.name)

    def _read_with_timeout(self):
        return asyncio.wait_for(
            self._stream.read_out(),
            timeout=self._read_timeout_sec,
        )


def writer(file=sys.stdout):
    return lambda **result: file.write(f"{json.dumps(result)}\n")


@define
class Reporter:

    _write = field(default=writer())
    _log: structlog.BoundLogger = field(factory=structlog.get_logger)

    def run_starting(self, implementations):
        pass

    def unsupported_dialect(self, exc_info):
        self._log.warn("Unsupported dialect", exc_info=exc_info)

    def ready(self, implementations):
        metadata = {
            implementation.name: dict(
                implementation.metadata, image=implementation.name,
            ) for implementation in implementations
        }
        self._write(implementations=metadata)

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
            log=self._log.bind(seq=seq, case=case),
        )


@define
class _CaseReporter:

    _write: callable
    _log: structlog.BoundLogger

    @classmethod
    def case_started(cls, log, write, case, seq):
        self = cls(log=log, write=write)
        self._write(case=case, seq=seq)
        return self

    def got_results(self, implementation, results):
        self._write(implementation=implementation, **results)

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
        for result, (_, seen) in zip(each["results"], case["results"]):
            seen[implementation] = result

    return dict(
        implementations=implementations.values(),
        results=[(v, k) for k, v in sorted(combined.items())],
    )
