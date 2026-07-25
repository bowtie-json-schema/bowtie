"""
Errors which can happen whilst speaking to a container engine.

Every engine reports the same failure in its own way, and none of them do
so machine readably -- not even over their HTTP APIs, which is why the
code this layer replaces was reduced to matching on substrings of prose.
Turning that mess into something a caller can branch on is most of the
reason this layer exists at all.
"""

from __future__ import annotations

from attrs import frozen


class EngineError(Exception):
    """
    Something went wrong whilst speaking to a container engine.
    """


@frozen
class NoSuchEngine(EngineError):
    """
    None of the container engines we know how to drive are installed.
    """

    tried: tuple[str, ...]

    def __str__(self):
        return f"No container engine found (tried {', '.join(self.tried)})."


@frozen
class EngineNotRunning(EngineError):
    """
    The engine is installed, but whatever it speaks to isn't running.

    For docker and podman that's a daemon (and on macOS, a VM housing it).
    For Apple's container it's a launchd-managed service.
    """

    engine: str

    def __str__(self):
        return f"The {self.engine} engine isn't running."


@frozen
class NoSuchImage(EngineError):
    """
    The image doesn't exist, locally nor in the registry it came from.
    """

    image: str

    def __str__(self):
        return f"No image named {self.image!r}."


@frozen
class NoSuchContainer(EngineError):
    """
    No container with the given ID exists.
    """

    id: str

    def __str__(self):
        return f"No container with ID {self.id!r}."


@frozen
class Unsupported(EngineError):
    """
    The engine cannot do what was asked of it.

    This is a capability gap rather than a failure -- Apple's container,
    for instance, has no way to reattach to a running container's stdio.
    """

    engine: str
    operation: str

    def __str__(self):
        return f"{self.engine} cannot {self.operation}."


@frozen
class SessionClosed(EngineError):
    """
    The container's standard streams are closed, but we tried to use them.
    """

    stderr: bytes = b""


@frozen
class EngineFailed(EngineError):
    """
    The engine failed in some way we do not specifically recognize.
    """

    argv: tuple[str, ...]
    returncode: int
    stderr: str

    def __str__(self):
        return (
            f"`{' '.join(self.argv)}` exited with {self.returncode}:\n"
            f"{self.stderr}"
        )
