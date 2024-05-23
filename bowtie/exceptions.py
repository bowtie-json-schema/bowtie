"""
Errors. Oh no!
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen
from diagnostic import DiagnosticError, DiagnosticWarning

if TYPE_CHECKING:
    from collections.abc import Sequence

    from jsonschema.exceptions import ValidationError

    from bowtie._core import Dialect, Implementation


#: The current version of Bowtie's IO protocol.
_PROTOCOL_VERSION = 1


@frozen
class StartupFailure(Exception):
    """
    An implementation failed to start properly.
    """

    implementation: Implementation
    stderr: bytes


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

    errors: Sequence[ValidationError]


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
