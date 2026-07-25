"""
The (few) ways the container engines we support differ from each other.

Pleasantly, they agree on nearly all of the spelling we need --
`create --interactive`, `start --attach --interactive`, `build --tag`
and `rm --force` are common to all three -- so what's left below is
quite small, and mostly concerns how each reports failure.
"""

from __future__ import annotations

from attrs import frozen

from bowtie._engines._errors import (
    EngineFailed,
    EngineNotRunning,
    NoSuchContainer,
    NoSuchImage,
)


@frozen
class Backend:
    """
    One container engine, and how its CLI differs from the others.
    """

    name: str

    #: How the engine spells fetching an image.
    #: Apple's container hides it under its image subcommand.
    pull: tuple[str, ...] = ("pull",)

    #: Flags silencing whatever progress output a pull would otherwise
    #: emit.
    #: This matters more than it may look, as a caller cannot tell
    #: something the engine wrote to standard error apart from something
    #: the container wrote there.
    quiet_pull: tuple[str, ...] = ("--quiet",)

    #: How the engine spells showing a *container's* configuration.
    #: docker and podman also have a bare `inspect` which will happily
    #: look at images and networks too, and which says "no such object"
    #: rather than naming what it couldn't find.
    inspect: tuple[str, ...] = ("container", "inspect")

    #: Flags which disable networking entirely for a container.
    no_network: tuple[str, ...] = ("--network", "none")

    #: How the engine spells deleting an image.
    remove_image: tuple[str, ...] = ("rmi", "--force")

    #: Whether the engine can reattach to a running container's stdio.
    #: Apple's container has no attach subcommand, and its exec starts a
    #: new process rather than reattaching to the existing one.
    attaches: bool = True

    #: Substrings indicating the engine's daemon or service is down.
    not_running: tuple[str, ...] = ()

    #: Substrings indicating an image does not exist.
    no_such_image: tuple[str, ...] = ()

    #: Substrings indicating a container does not exist.
    no_such_container: tuple[str, ...] = ()

    #: The binary to invoke, where it isn't simply the engine's name.
    executable: str | None = None

    @property
    def command(self) -> str:
        """
        The binary to invoke.
        """
        return self.executable or self.name

    def classify(
        self,
        argv: tuple[str, ...],
        returncode: int,
        stderr: str,
        subject: str,
    ) -> Exception:
        """
        Work out what an engine was trying to tell us when it failed.

        `subject` is whatever the command was operating on -- an image
        or a container -- as the engines are inconsistent about whether
        they mention it themselves.
        """
        message = stderr.casefold()

        # Check this first, as an engine which isn't running will happily
        # claim an image doesn't exist rather than admitting as much.
        if any(each in message for each in self.not_running):
            return EngineNotRunning(engine=self.name)
        if any(each in message for each in self.no_such_image):
            return NoSuchImage(image=subject)
        if any(each in message for each in self.no_such_container):
            return NoSuchContainer(id=subject)
        return EngineFailed(
            argv=argv,
            returncode=returncode,
            stderr=stderr,
        )


DOCKER = Backend(
    name="docker",
    not_running=(
        "cannot connect to the docker daemon",
        "is the docker daemon running",
    ),
    no_such_image=(
        "manifest unknown",
        "pull access denied",
        "repository does not exist",
        # Registries (including ghcr.io) decline to distinguish "no such
        # image" from "you may not look at this image", and Bowtie has
        # always treated the two alike.
        ": denied",
    ),
    no_such_container=("no such container",),
)

PODMAN = Backend(
    name="podman",
    not_running=(
        "cannot connect to podman",
        "unable to connect to podman socket",
    ),
    no_such_image=(
        "manifest unknown",
        "unable to find a name and tag match",
        ": denied",
    ),
    no_such_container=(
        "no such container",
        "no container with name or id",
    ),
)

CONTAINER = Backend(
    name="container",
    pull=("image", "pull"),
    quiet_pull=("--disable-progress-updates",),
    inspect=("inspect",),
    remove_image=("image", "rm"),
    attaches=False,
    not_running=(
        "xpc connection error",
        "container system service has been started",
    ),
    # FIXME: Unverified. Apple's container refuses to say anything at all
    #        until its service is running, so these need filling in from
    #        a machine where it is.
    no_such_image=(),
    no_such_container=(),
)

#: Every engine we know how to drive, in the order we look for them.
KNOWN = (DOCKER, PODMAN, CONTAINER)
