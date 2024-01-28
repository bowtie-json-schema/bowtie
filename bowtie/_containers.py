"""
Clunky pepperings-over of communication with containers.

Some of this is warts from aiodocker, but mixed in with fun
special-to-this-package logic occasionally.
"""
from __future__ import annotations

from collections import deque
from contextlib import suppress
from typing import TYPE_CHECKING
import asyncio
import json

from attrs import field, frozen, mutable
import aiodocker.exceptions

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from typing import Any

    import aiodocker.containers
    import aiodocker.docker
    import aiodocker.stream  # noqa: TCH004 ??? no it's not?


class StreamClosed(Exception):
    """
    The stream was closed, and we just noticed.

    Who knows whether the last message was sent, or what happened.
    """


@frozen
class NoSuchImage(Exception):
    name: str
    data: Any = None


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

    async def send(self, message: dict[str, Any]) -> None:
        as_bytes = f"{json.dumps(message)}\n".encode()
        try:  # aiodocker doesn't appear to properly report stream closure
            await self._stream.write_in(as_bytes)
        except AttributeError:
            raise StreamClosed(self) from None

    async def receive(self) -> bytes:
        if self._buffer:
            return self._buffer.popleft()

        while True:
            message = await self._read_with_timeout()
            if message is not None:
                break
            info: dict[str, Any] = await self._container.show()  # type: ignore[reportUnknownMemberType]
            if info["State"]["FinishedAt"]:
                raise StreamClosed(self)

        if message.stream == 2:  # type: ignore[reportUnknownMemberType]  # noqa: PLR2004
            data: list[bytes] = []

            while message.stream == 2:  # type: ignore[reportUnknownMemberType]  # noqa: PLR2004
                data.append(message.data)  # type: ignore[reportUnknownMemberType]
                message = await self._read_with_timeout()
                if message is None:
                    raise GotStderr(b"".join(data))

        line: bytes
        rest: list[bytes]
        while True:
            line, *rest = message.data.split(b"\n")  # type: ignore[reportUnknownMemberType]
            if rest:
                line, self._last = self._last + line, rest.pop()  # type: ignore[reportUnknownVariableType]
                self._buffer.extend(rest)
                return line  # type: ignore[reportUnknownVariableType]

            message = None
            while message is None:
                message = await self._read_with_timeout()
            self._last += line  # type: ignore[reportUnknownMemberType]

    async def ensure_deleted(self):
        with suppress(aiodocker.exceptions.DockerError):
            await self._container.delete(force=True)  # type: ignore[reportUnknownMemberType]
