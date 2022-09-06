from contextlib import asynccontextmanager
from textwrap import indent
from time import monotonic_ns
import asyncio
import json

from attrs import define
import aiodocker


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
    _restarts: int = 2 + 1
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
        return await self._send(cmd="run", seq=seq, case=case)

    async def _stop(self):
        await self._send(cmd="stop")

    async def _send(self, **kwargs):
        if self._restarts <= 0:
            return dict(succeeded=False, implementation=self._name)

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
