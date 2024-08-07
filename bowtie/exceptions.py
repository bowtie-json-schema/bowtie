"""
Errors. Oh no!

Bowtie's sequence speaking to an implementation breaks down roughly as
attempting to perform a sequence of steps.

Listed below is a short description of each step, along with a possible
exception class that connectables and/or harnesses can raise if the specific
step fails.

    * establish a connection (fails via `CannotConnect`)
    * send a first request, retrieving metadata about the implementation
      (fails via `StartupFailed` or `VersionMismatch`)
    * send sequences of test cases, collecting results
    * close the connection

At any given point in time, `InvalidResponse` or `ProtocolError` may be raised
to indicate that the harness didn't return a response which appropriately
matches Bowtie's IO protocol (which essentially always indicates a harness
bug, at least in not catching the implementation crashing or writing
extraneous data).

Similarly, `GotStderr` can be raised to indicate that some (likely) error has
appeared on standard error and that a response may no longer be expected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from attrs import frozen
from diagnostic import DiagnosticError, DiagnosticWarning

if TYPE_CHECKING:
    from collections.abc import Iterable

    from rich.console import Console, ConsoleOptions, RenderResult

    from bowtie._connectables import ConnectableId
    from bowtie._core import Dialect, Implementation


#: The current version of Bowtie's IO protocol.
_PROTOCOL_VERSION = 1


@frozen
class CannotConnect(Exception):
    """
    A connectable could not locate the given implementation.

    Either it isn't connectable the way we asked for or it's unreachable in
    some connectable-specific way.
    """

    kind: str
    id: ConnectableId
    hint: str | None = None

    def __rich__(self):
        causes: list[str] = []
        if self.__cause__ is not None:
            causes.append(str(self.__cause__))
        elif self.__context__ is not None:
            causes.append(str(self.__context__))

        return DiagnosticError(
            code="cannot-connect",
            message=f"Couldn't connect to '{self.kind}:{self.id}'",
            causes=causes,
            hint_stmt=self.hint,
        )


@frozen
class NoSuchImplementation(Exception):
    """
    An implementation with the given name does not exist.
    """

    id: ConnectableId

    # TODO: Combine with CannotConnect / make so CannotConnect means 'we know
    #       that implementation but can't reach it?

    def __rich__(self):
        return DiagnosticError(
            code="no-such-implementation",
            message=f"{self.id!r} is not a known Bowtie implementation.",
            causes=[],
            hint_stmt=(
                "Check Bowtie's supported list of implementations "
                "to ensure you have the name correct. "
                "If you are developing a new harness, ensure you have "
                "built and tagged it properly."
            ),
        )


@frozen
class StartupFailed(Exception):
    """
    We found to an implementation but could not get it to start.
    """

    id: ConnectableId
    stderr: str = ""
    data: Any = None

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        cause = self.__cause__
        if cause is None:
            root_causes, hint = [], (
                "If you are developing a new harness, check if stderr "
                "(shown below) contains harness-specific information "
                "which can help. Otherwise, you may have an issue with your "
                "local container setup (podman, docker, etc.)."
            )
        else:
            root_causes: Iterable[Exception] = getattr(
                cause.__cause__,
                "exceptions",
                [],
            )
            hint = (
                "The harness sent an invalid response for Bowtie's protocol. "
                "Details for what was wrong are above. If you are developing "
                "support for a new harness you should address them, otherwise "
                "if you are not, this is a bug in Bowtie's harness for this "
                "implementation! File an issue on Bowtie's issue tracker."
            )

        yield DiagnosticError(
            code="startup-failed",
            message=f"{self.id!r} failed to start.",
            causes=[str(exc) for exc in root_causes],
            hint_stmt=hint,
        )
        if self.stderr:
            from rich.panel import Panel

            yield Panel(self.stderr, title="stderr")


@frozen
class VersionMismatch(Exception):
    """
    The wrong protocol version was returned from an implementation.
    """

    got: int
    expected: int = _PROTOCOL_VERSION

    def __str__(self) -> str:
        return (
            f"Expected to speak version {self.expected} of the Bowtie "
            f"protocol but the implementation sent {self.got}."
        )

    @classmethod
    def check(cls, got: int) -> None:
        """
        Complain if we are speaking the wrong protocol version.
        """
        if got != _PROTOCOL_VERSION:
            raise cls(got=got)


@frozen
class ProtocolError(Exception):
    """
    An invalid request or response was sent.
    """


@frozen
class InvalidResponse(Exception):
    """
    An invalid response was sent by a harness.
    """

    # TODO: Combine with ProtocolError?

    contents: str


@frozen
class UnsupportedDialect(Exception):
    """
    An implementation does not support the dialect which is to be spoken.
    """

    implementation: Implementation
    dialect: Dialect

    def __rich__(self):
        supports = ", ".join(
            each.pretty_name
            for each in sorted(self.implementation.info.dialects, reverse=True)
        )
        return DiagnosticWarning(
            code="unsupported-dialect",
            message=(
                f"{self.implementation.id!r} does not "
                f"support {self.dialect.pretty_name}."
            ),
            causes=[],
            hint_stmt=None,
            note_stmt=f"its supported dialects are: {supports}\n",
        )


@frozen
class DialectError(Exception):
    """
    We tried to start sending test cases but encountered an unknown error.

    It probably ain't our fault, the implementation blew up.
    """

    implementation: Implementation
    dialect: Dialect
    stderr: bytes

    def __rich__(self):
        return DiagnosticError(
            code="dialect-error",
            message=(
                f"{self.implementation.id!r} failed as we were beginning to "
                f"send {self.dialect.pretty_name} tests."
            ),
            causes=[],
            hint_stmt=(
                "The error may be transient, so you may want to try again. "
                "If it does not appear to be, it may indicate a bug both in "
                "the implementation as well as in Bowtie's test harness. "
                "Bowtie aims not to propagate these bugs in a way that they "
                "cause crashes, so at very least you should open a bug "
                "(with reproducer) on Bowtie's issue board."
            ),
        )


@frozen
class GotStderr(Exception):
    """
    An implementation sent data on standard error.

    We were trying to communicate with it (via Bowtie's protocol), but the
    implementation has likely encountered some unexpected error.

    It may have crashed.

    Implementations of the `Connection` protocol should raise this exception
    when they detect this kind of out-of-band error (in whatever concrete
    connection-specific mechanism indicates this has occurred).
    """

    stderr: bytes
