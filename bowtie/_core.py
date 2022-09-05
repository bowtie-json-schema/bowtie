from contextlib import asynccontextmanager
from textwrap import indent
from time import monotonic_ns
import asyncio
import json

from attrs import define, field
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
    _container: aiodocker.containers.DockerContainer = field(repr=False)
    _stream: aiodocker.stream.Stream = None
    _reattaches: int = 3 + 1

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name):
        container = await docker.containers.create(
            config=dict(Image=image_name, OpenStdin=True),
        )
        try:
            await container.start()
            self = cls(name=image_name, container=container)
            self._attach()
            yield await self._start()
            await self._stop()
        finally:
            await container.delete(force=True)

    def _attach(self):
        self._reattaches -= 1
        self._stream = self._container.attach(
            stdin=True,
            stdout=True,
            stderr=True,
        )

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
        if self._reattaches <= 0:
            return dict(succeeded=False, implementation=self._name)

        started = monotonic_ns()
        cmd = f"{json.dumps(kwargs)}\n"
        try:
            await self._stream.write_in(cmd.encode("utf-8"))
        except AttributeError:
            # FIXME: aiodocker doesn't appear to properly report when its
            # stream is closed
            self._attach()
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
            message = await self._stream.read_out()
            if message is None:
                await asyncio.sleep(0)
                continue

            if message.stream == 2:
                data = []
                while message is not None and message.stream == 2:
                    data.append(message.data)
                    message = await self._stream.read_out()
                return False, {
                    "stderr": b"".join(data),
                    "implementation": self._name,
                }
            else:
                return True, json.loads(message.data)
        return False, {}
