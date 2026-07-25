"""
Driving a container engine by running its command line interface.

This is the only mechanism all the engines have in common.
Apple's container has no HTTP API at all, and speaking to it over XPC
instead would cover it alone whilst leaving docker and podman needing a
second mechanism anyhow.

Doing so also means the engine demultiplexes container stdio onto real
pipes for us, which is precisely the job the previous aiodocker based
code did by hand.
"""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager, suppress
from pathlib import Path
from shutil import which
from tempfile import TemporaryDirectory, TemporaryFile
from typing import TYPE_CHECKING, cast
import sys

from anyio.streams.buffered import BufferedByteReceiveStream
from attrs import field, frozen
import anyio

from bowtie._engines._backends import KNOWN
from bowtie._engines._errors import (
    NoSuchContainer,
    NoSuchEngine,
    NoSuchImage,
    SessionClosed,
    Unsupported,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, Generator
    from typing import IO

    from anyio.abc import ByteReceiveStream, Process

    from bowtie._engines._backends import Backend


#: The longest line we will buffer from a container before giving up.
#: Responses carrying large schemas are entirely normal, so this is less
#: a protocol limit than a way to stay bounded if a harness never emits
#: a newline at all.
_MAX_LINE = 32 * 1024 * 1024


@contextmanager
def _prepared(context: Path) -> Generator[Path]:
    """
    A build context in a state an engine can be handed.

    On most platforms that's simply the directory we were given.
    Windows needs a normalized copy of it, as git's autocrlf will have
    rewritten LF to CRLF on checkout -- which breaks shebang lines
    inside a Linux container -- and its filesystem has no executable bit
    for the engine to preserve.
    """
    if sys.platform != "win32":
        yield context
        return

    with TemporaryDirectory() as temporary:
        prepared = Path(temporary)
        for path in sorted(context.rglob("*")):
            if path.is_dir():
                continue
            data = path.read_bytes().replace(b"\r\n", b"\n")
            copy = prepared / path.relative_to(context)
            copy.parent.mkdir(parents=True, exist_ok=True)
            copy.write_bytes(data)
            copy.chmod(0o755 if data.startswith(b"#!") else 0o644)
        yield prepared


@frozen
class Session:
    """
    A live bidirectional connection to a container's standard streams.

    Standard error is collected into a file rather than a pipe.
    A container which says a great deal there therefore cannot deadlock
    by filling a pipe nobody is draining, and reading it needs no
    background task -- which in turn keeps this layer free of any cancel
    scope spanning a yield, and so portable to trio.
    """

    _process: Process = field(alias="process", repr=False)
    _stdout: BufferedByteReceiveStream = field(alias="stdout", repr=False)
    _stderr: IO[bytes] = field(alias="stderr", repr=False)

    @property
    def alive(self) -> bool:
        """
        Is the container still running?
        """
        return self._process.returncode is None

    def stderr(self) -> bytes:
        """
        Whatever the container has written to standard error so far.
        """
        self._stderr.seek(0)
        return self._stderr.read()

    async def send(self, line: str) -> None:
        """
        Write a single line to the container's standard input.
        """
        stdin = self._process.stdin
        if stdin is None:
            raise SessionClosed(stderr=self.stderr())
        try:
            await stdin.send(f"{line}\n".encode())
        except (anyio.BrokenResourceError, anyio.ClosedResourceError):
            raise SessionClosed(stderr=self.stderr()) from None

    async def receive(self) -> str:
        """
        Read a single line from the container's standard output.

        Raises `SessionClosed` if the container has gone away.
        Callers wanting to wait only so long should wrap this in an
        `anyio.fail_after` scope, which is safe to abandon and retry --
        anything already read stays buffered for the next attempt.
        """
        try:
            line = await self._stdout.receive_until(b"\n", _MAX_LINE)
        except (
            anyio.BrokenResourceError,
            anyio.ClosedResourceError,
            anyio.EndOfStream,
            anyio.IncompleteRead,
        ):
            raise SessionClosed(stderr=self.stderr()) from None
        except anyio.DelimiterNotFound:
            # A harness which has said this much without a newline is
            # never going to send one.
            raise SessionClosed(stderr=self.stderr()) from None
        return line.decode()


@frozen
class Engine:
    """
    A container engine, driven via its command line interface.
    """

    _backend: Backend = field(alias="backend")

    @classmethod
    def detect(cls, *backends: Backend) -> Engine:
        """
        Use the first engine we know about which is actually installed.
        """
        candidates = backends or KNOWN
        for backend in candidates:
            if which(backend.command) is not None:
                return cls(backend=backend)
        raise NoSuchEngine(tried=tuple(each.name for each in candidates))

    @classmethod
    def named(cls, name: str) -> Engine:
        """
        Use one specific engine, by name.
        """
        for backend in KNOWN:
            if backend.name == name:
                return cls(backend=backend)
        raise NoSuchEngine(tried=(name,))

    @property
    def name(self) -> str:
        """
        Which engine this is.
        """
        return self._backend.name

    @property
    def attaches(self) -> bool:
        """
        Can this engine reattach to a running container's stdio?
        """
        return self._backend.attaches

    async def pull(self, image: str) -> None:
        """
        Fetch an image from wherever it lives.
        """
        await self._engine(
            *self._backend.pull,
            *self._backend.quiet_pull,
            image,
            subject=image,
        )

    async def create(self, image: str, *, network: bool = False) -> str:
        """
        Create (but do not start) a container, returning its ID.

        Networking is off unless asked for, which is what keeps a
        container from reaching anything whilst it runs.
        """
        args = ["create", "--interactive"]
        if not network:
            args.extend(self._backend.no_network)
        args.append(image)
        return (await self._engine(*args, subject=image)).strip()

    async def create_pulling_if_needed(
        self,
        image: str,
        *,
        network: bool = False,
    ) -> str:
        """
        Create a container, fetching its image first if we lack it.

        Engines differ on whether creating pulls implicitly, so we ask
        for it explicitly rather than relying on either behavior.
        """
        try:
            return await self.create(image, network=network)
        except NoSuchImage:
            await self.pull(image)
            return await self.create(image, network=network)

    async def remove(self, id: str) -> None:
        """
        Delete a container, running or not.
        """
        await self._engine("rm", "--force", id, subject=id)

    async def start_detached(self, id: str) -> None:
        """
        Start a container without speaking to it.
        """
        await self._engine("start", id, subject=id)

    async def build(self, tag: str, context: Path) -> None:
        """
        Build an image from a directory holding its build context.

        A directory is the one form every engine accepts -- Apple's
        container takes nothing else, and whilst docker will read a tar
        archive from standard input, podman reserves that for reading a
        Containerfile.
        """
        with _prepared(context) as prepared:
            await self._engine(
                "build",
                "--tag",
                tag,
                str(prepared),
                subject=tag,
            )

    async def remove_image(self, tag: str) -> None:
        """
        Delete an image.
        """
        await self._engine(*self._backend.remove_image, tag, subject=tag)

    async def exists(self, id: str) -> bool:
        """
        Is there a container with the given ID?
        """
        try:
            await self._engine(*self._backend.inspect, id, subject=id)
        except NoSuchContainer:
            return False
        return True

    @asynccontextmanager
    async def start(self, id: str) -> AsyncGenerator[Session]:
        """
        Start a created container and speak to its standard streams.
        """
        args = ("start", "--attach", "--interactive", id)
        async with self._session(*args) as session:
            yield session

    @asynccontextmanager
    async def attach(self, id: str) -> AsyncGenerator[Session]:
        """
        Speak to the standard streams of an already running container.
        """
        if not self._backend.attaches:
            raise Unsupported(
                engine=self._backend.name,
                operation="attach to a running container",
            )
        # Confirm it exists up front, as otherwise a bad ID shows up only
        # as a session which closes immediately for no stated reason.
        await self._engine(*self._backend.inspect, id, subject=id)
        async with self._session("attach", id) as session:
            yield session

    async def _engine(self, *args: str, subject: str) -> str:
        """
        Run an engine command to completion, returning its stdout.
        """
        argv = (self._backend.command, *args)
        try:
            completed = await anyio.run_process(argv, check=False)
        except FileNotFoundError:
            raise NoSuchEngine(tried=(self._backend.name,)) from None

        if completed.returncode:
            raise self._backend.classify(
                argv=argv,
                returncode=completed.returncode,
                stderr=completed.stderr.decode(),
                subject=subject,
            )
        return completed.stdout.decode()

    @asynccontextmanager
    async def _session(self, *args: str) -> AsyncGenerator[Session]:
        """
        Speak to whatever container the given command connects us to.
        """
        argv = (self._backend.command, *args)
        with TemporaryFile() as stderr:
            try:
                process = await anyio.open_process(argv, stderr=stderr)
            except FileNotFoundError:
                raise NoSuchEngine(tried=(self._backend.name,)) from None

            try:
                yield Session(
                    process=process,
                    stdout=BufferedByteReceiveStream(
                        cast("ByteReceiveStream", process.stdout),
                    ),
                    stderr=stderr,
                )
            finally:
                if process.returncode is None:
                    with suppress(ProcessLookupError):  # it may beat us
                        process.kill()
                await process.wait()
