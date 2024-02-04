"""
Clunky pepperings-over of communication with containers.

Some of this is warts from aiodocker, but mixed in with fun
special-to-this-package logic occasionally.
"""

from __future__ import annotations

from collections import deque
from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING
import asyncio
import json

from attrs import field, mutable
import aiodocker.exceptions

from bowtie._core import (
    GotStderr,
    InvalidResponse,
    NoSuchImplementation,
    Restarted,
    StartupFailed,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable
    from typing import Any, Self

    import aiodocker.containers
    import aiodocker.docker
    import aiodocker.stream  # noqa: TCH004 ??? no it's not?

    from bowtie._commands import Message


class _ClosedStream(Exception):
    """
    The stream is closed, and we tried to send something on it.

    This exception should never bubble out of this module, it should be handled
    by the connection.
    """


@mutable
class Stream:
    """
    Wrapper to make aiodocker's Stream more pleasant to use.
    """

    _stream: aiodocker.stream.Stream = field(repr=False, alias="stream")
    _container: aiodocker.containers.DockerContainer = field(
        repr=False,
        alias="container",
    )
    _read_timeout_sec: float | None = field(
        repr=False,
        alias="read_timeout_sec",
    )
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

    async def send(self, message: str) -> None:
        try:  # aiodocker doesn't appear to properly report stream closure
            await self._stream.write_in(message.encode())
        except aiodocker.exceptions.DockerError as err:
            raise _ClosedStream(self) from err
        except AttributeError:
            raise _ClosedStream(self) from None

    async def receive(self) -> str:
        if self._buffer:
            return self._buffer.popleft().decode()

        while True:
            message = await self._read_with_timeout()
            if message is not None:
                break
            info: dict[str, Any] = await self._container.show()  # type: ignore[reportUnknownMemberType]
            if info["State"]["FinishedAt"]:
                raise _ClosedStream(self)

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
                return line.decode()  # type: ignore[reportUnknownVariableType]

            message = None
            while message is None:
                message = await self._read_with_timeout()
            self._last += line  # type: ignore[reportUnknownMemberType]

    async def ensure_deleted(self):
        with suppress(aiodocker.exceptions.DockerError):
            await self._container.delete(force=True)  # type: ignore[reportUnknownMemberType]


@mutable
class ContainerConnection:
    """
    A connection with a restartable container over stdio via request/responses.

    Requests and responses are JSON-serializable messages, with serialization
    handled here.
    """

    _image: str = field(alias="image")

    _docker: aiodocker.docker.Docker = field(repr=False, alias="docker")
    _stream: Stream = field(default=None, repr=False, alias="stream")

    # Maybe second versions of these will be useful also at the Implementation
    # level again, to control for non-protocol-related flakiness or slowness
    _restarts: int = field(default=10, repr=False, alias="restarts")
    _read_timeout_sec: float | None = field(
        default=2.0,
        converter=lambda value: value or None,  # type: ignore[reportUnknownArgumentType]
        repr=False,
    )

    #: A per-request number of retries, before giving up
    _retry: int = 3

    @classmethod
    @asynccontextmanager
    async def open(
        cls,
        image_name: str,
        **kwargs: Any,
    ) -> AsyncIterator[Self]:
        self = cls(image=image_name, **kwargs)

        try:
            await self._start_container()
        except GotStderr as error:
            err = StartupFailed(name=image_name, stderr=error.stderr.decode())
            raise err from None
        except _ClosedStream:
            raise StartupFailed(name=image_name) from None
        except aiodocker.exceptions.DockerError as err:
            # This craziness can go wrong in various ways, none of them
            # machine parseable.

            status, data, *_ = err.args
            if data.get("cause") == "image not known":
                raise NoSuchImplementation(image_name) from err

            message = ghcr = data.get("message", "")

            if status == 500:  # noqa: PLR2004
                try:
                    # GitHub Registry saying an image doesn't exist as reported
                    # within GitHub Actions' version of Podman...
                    # This is some crazy string like:
                    #   Get "https://ghcr.io/v2/bowtie-json-schema/image-name/tags/list": denied  # noqa: E501
                    # with seemingly no other indication elsewhere and
                    # obviously no real good way to detect this specific case
                    no_image = message.endswith('/tags/list": denied')
                except Exception:  # noqa: BLE001, S110
                    pass
                else:
                    if no_image:
                        raise NoSuchImplementation(image_name)

                try:
                    # GitHub Registry saying an image doesn't exist as reported
                    # locally via podman on macOS...

                    # message will be ... a JSON string !?! ...
                    error = json.loads(ghcr).get("message", "")
                except Exception:  # noqa: BLE001, S110
                    pass  # nonJSON / missing key
                else:
                    if "403 (forbidden)" in error.casefold():
                        raise NoSuchImplementation(image_name)

            raise StartupFailed(name=image_name, data=data) from err

        yield self
        await self._stream.ensure_deleted()

    async def _start_container(self):
        container = await self._docker.containers.run(  # type: ignore[reportUnknownMemberType]
            config=dict(
                Image=self._image,
                OpenStdin=True,
                HostConfig=dict(NetworkMode="none"),
            ),
        )
        self._stream = Stream.attached_to(
            container,
            read_timeout_sec=self._read_timeout_sec,
        )

    async def request(self, message: Message) -> Message | None:
        request = f"{json.dumps(message)}\n"

        try:
            await self._stream.send(request)
        except _ClosedStream:
            self._restarts -= 1
            await self._stream.ensure_deleted()
            await self._start_container()
            raise Restarted() from None

        for _ in range(self._retry):
            try:
                response = await self._stream.receive()
            except asyncio.exceptions.TimeoutError:
                continue
            except _ClosedStream:
                return

            try:
                return json.loads(response)
            except json.JSONDecodeError as err:
                raise InvalidResponse(contents=response) from err

    async def poison(self, message: dict[str, Any]) -> None:
        request = f"{json.dumps(message)}\n"
        with suppress(_ClosedStream):
            await self._stream.send(request)
