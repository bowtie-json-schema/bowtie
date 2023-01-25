"""
Errors. Oh no!
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from bowtie._core import Implementation


@frozen
class StartupFailure(Exception):
    """
    An implementation failed to start properly.
    """

    implementation: Implementation
    stderr: bytes


@frozen
class ImplementationNotReady(Exception):
    """
    An implementation said it was not ready.
    """


@frozen
class VersionMismatch(Exception):
    """
    The wrong protocol version was returned from an implementation.
    """

    expected: int
    got: int


@frozen
class _ProtocolError(Exception):  # type: ignore[reportUnusedClass]
    """
    An invalid request or response was sent.
    """

    errors: list[Exception]
