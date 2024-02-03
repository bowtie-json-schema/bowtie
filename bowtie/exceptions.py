"""
Errors. Oh no!
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from bowtie._core import Implementation


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

    errors: list[Exception]
