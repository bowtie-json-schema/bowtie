from typing import TYPE_CHECKING

from attrs import define

if TYPE_CHECKING:
    from bowtie._core import Implementation


@define
class StartupFailure(Exception):
    """
    An implementation failed to start properly.
    """

    implementation: "Implementation"
    stderr: bytes


@define
class ImplementationNotReady(Exception):
    """
    An implementation said it was not ready.
    """

    implementation: "Implementation"


@define
class VersionMismatch(Exception):
    """
    The wrong protocol version was returned from an implementation.
    """

    implementation: "Implementation"
    expected: int
    got: int


@define
class _ProtocolError(Exception):
    """
    An invalid request or response was sent.
    """

    errors: list
