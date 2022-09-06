from contextlib import asynccontextmanager
from textwrap import indent
from time import monotonic_ns
import asyncio
import json

from attrs import define, field
import aiodocker
import structlog


class StartError(Exception):
    """
    An implementation failed to start properly.
    """


@define(hash=True)
class Implementation:
    """
    A running implementation under test.
    """

    _name: str
    _docker: aiodocker.Docker
    _restarts: int = 20 + 1
    _read_timeout_sec: float = 2.0

    _container: aiodocker.containers.DockerContainer = None
    _stream: aiodocker.stream.Stream = None

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name):
        try:
            self = cls(name=image_name, docker=docker)
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
            config=dict(Image=self._name, OpenStdin=True),
        )
        await self._container.start()
        self._stream = self._container.attach(
            stdin=True,
            stdout=True,
            stderr=True,
        )
        await self._start()

    async def _start(self):
        response = await self._send(cmd="start", version=1)
        if not response["succeeded"]:
            raise StartError(
                f"{self._name} failed on startup. Stderr contained:\n\n"
                f"{indent(response['response']['stderr'].decode(), '  ')}",
            )
        if not response["response"].get("ready"):
            raise StartError(f"{self._name} is not ready!")
        elif response["response"].get("version") != 1:
            raise StartError(f"{self._name} did not speak version 1!")
        return self

    async def run_case(self, seq, case):
        if self._restarts <= 0:
            return dict(
                succeeded=False, backoff=True, implementation=self._name,
            )
        return await self._send(cmd="run", seq=seq, case=case)

    async def _stop(self):
        if self._restarts > 0:
            await self._send(cmd="stop")

    async def _send(self, **kwargs):
        started = monotonic_ns()
        cmd = f"{json.dumps(kwargs)}\n"
        try:
            await self._stream.write_in(cmd.encode("utf-8"))
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            info = await self._container.show()
            assert not info["State"]["Running"], info
            await self._restart_container()
            await self._stream.write_in(cmd.encode("utf-8"))
        succeeded, response = await self._recv()
        return {
            "succeeded": succeeded,
            "took_ns": monotonic_ns() - started,
            "response": response,
            "implementation": self._name,
        }

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
                    message = await self._read_with_timeout()
                return False, {
                    "stderr": b"".join(data),
                    "implementation": self._name,
                }
            else:
                if message.data.endswith(b"\n"):
                    return True, json.loads(message.data)

                data = [message.data]
                while message is not None:
                    try:
                        message = await self._read_with_timeout()
                    except asyncio.exceptions.TimeoutError:
                        break
                    data.append(message.data)
                return True, json.loads(b"".join(data))
        return False, {}

    def _read_with_timeout(self):
        return asyncio.wait_for(
            self._stream.read_out(),
            timeout=self._read_timeout_sec,
        )


@define
class Reporter:

    _log: structlog.BoundLogger = field(factory=structlog.get_logger)

    def run_starting(self, implementations):
        self._log.info("Starting", implementations=implementations)

    def ready(self, implementations):
        self._log.debug("Ready", implementations=implementations)

    def finished(self, count):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)

    def case_started(self, seq, case):
        return _CaseReporter.case_started(
            log=self._log.bind(seq=seq, case=case),
        )


@define
class _CaseReporter:

    _log: structlog.BoundLogger

    @classmethod
    def case_started(cls, log):
        log.info("Starting")
        return cls(log=log)

    def case_finished(self, results):
        self._log.msg("Responded", results=results)

    def backoff(self, result):
        self._log.warn("Backing off!", **result)

    def errored(self, result):
        self._log.error("ERROR", **result)
