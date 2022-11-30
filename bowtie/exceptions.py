from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from bowtie._core import Implementation


@frozen
class StartupFailure(Exception):
    """
    An implementation failed to start properly.
    """

    implementation: "Implementation"
    stderr: bytes


@frozen
class ImplementationNotReady(Exception):
    """
    An implementation said it was not ready.
    """

    implementation: "Implementation"


@frozen
class VersionMismatch(Exception):
    """
    The wrong protocol version was returned from an implementation.
    """

    implementation: "Implementation"
    expected: int
    got: int


@frozen
class _ProtocolError(Exception):
    """
    An invalid request or response was sent.
    """

    errors: list
