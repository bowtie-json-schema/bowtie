"""
A uniform interface to the container engines we know how to drive.

Nothing in here knows anything about Bowtie, JSON Schema or harnesses --
it deliberately stays a general purpose way to start a container and
speak to its standard streams, so that it can move out into a library of
its own once the interface has survived contact with all three engines.

It's also free of any particular async framework beyond `anyio`, which
means it runs unmodified on asyncio today and on trio whenever the rest
of Bowtie is ready to follow.
"""

from bowtie._engines._backends import (
    CONTAINER,
    DOCKER,
    KNOWN,
    PODMAN,
    Backend,
)
from bowtie._engines._errors import (
    EngineError,
    EngineFailed,
    EngineNotRunning,
    NoSuchContainer,
    NoSuchEngine,
    NoSuchImage,
    SessionClosed,
    Unsupported,
)
from bowtie._engines._subprocess import Engine, Session

__all__ = [
    "CONTAINER",
    "DOCKER",
    "KNOWN",
    "PODMAN",
    "Backend",
    "Engine",
    "EngineError",
    "EngineFailed",
    "EngineNotRunning",
    "NoSuchContainer",
    "NoSuchEngine",
    "NoSuchImage",
    "Session",
    "SessionClosed",
    "Unsupported",
]
