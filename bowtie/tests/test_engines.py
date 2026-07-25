"""
Tests for the container engine layer.

These deliberately drive a stand-in engine rather than a real one, as
what's worth testing here is the plumbing -- argv construction, stdio
round trips, how sessions end and how failures are classified -- none of
which needs a container to exercise.
Whether each real engine actually speaks the dialect described in
`bowtie._engines._backends` is what the integration suite is for.
"""

from __future__ import annotations

import sys

import pytest

from bowtie._engines import (
    CONTAINER,
    DOCKER,
    PODMAN,
    Backend,
    Engine,
    EngineFailed,
    EngineNotRunning,
    NoSuchContainer,
    NoSuchEngine,
    NoSuchImage,
    SessionClosed,
    Unsupported,
    _subprocess,
)

pytestmark = pytest.mark.anyio


#: An "engine" which knows just enough to be driven like a real one.
#: Starting a container gets you an echo server standing in for a
#: harness, which dies on request so that closure is testable.
FAKE_ENGINE = f"""\
#!{sys.executable}
import pathlib, sys

args = sys.argv[1:]
pathlib.Path(__file__).with_name("argv").open("a").write(f"{{args}}\\n")

match args:
    case ["create", *rest]:
        if "nonexistent" in rest[-1]:
            print("Error: manifest unknown", file=sys.stderr)
            sys.exit(1)
        print("fake-container-id")
    case ["start", *rest]:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            if line.strip() == "die":
                sys.exit(0)
            if line.strip() == "complain":
                print("something went wrong", file=sys.stderr, flush=True)
                continue
            if line.strip() == "flood":
                sys.stdout.write("x" * 1000)  # ... and never a newline
                sys.stdout.flush()
                continue
            print(line.strip()[::-1], flush=True)
    case ["container", "inspect", *rest]:
        if "nonexistent" in rest[-1]:
            print("Error: no such container", file=sys.stderr)
            sys.exit(1)
    case ["build", *rest]:
        if not pathlib.Path(rest[-1]).is_dir():
            print(f"not a context directory: {{rest[-1]}}", file=sys.stderr)
            sys.exit(1)
    case ["pull", *rest] | ["rm", *rest]:
        pass
    case _:
        print(f"unknown invocation: {{args}}", file=sys.stderr)
        sys.exit(2)
"""


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def engine(tmp_path):
    executable = tmp_path / "fake-engine"
    executable.write_text(FAKE_ENGINE)
    executable.chmod(0o755)
    return Engine(
        backend=Backend(
            name="fake",
            executable=str(executable),
            no_such_image=("manifest unknown",),
            no_such_container=("no such container",),
        ),
    )


@pytest.fixture
def argv(tmp_path):
    def _argv():
        path = tmp_path / "argv"
        return path.read_text().splitlines() if path.exists() else []

    return _argv


class TestSessions:
    async def test_round_trip(self, engine):
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            await session.send("hello")
            assert await session.receive() == "olleh"
            await session.send("goodbye")
            assert await session.receive() == "eybdoog"

    async def test_receiving_from_a_dead_container(self, engine):
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            await session.send("die")
            with pytest.raises(SessionClosed):
                await session.receive()

    async def test_stderr_is_collected_without_ending_the_session(
        self,
        engine,
    ):
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            await session.send("complain")
            await session.send("hello")
            assert await session.receive() == "olleh"
            assert b"something went wrong" in session.stderr()

    async def test_stderr_survives_closure(self, engine):
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            await session.send("complain")
            await session.send("die")
            with pytest.raises(SessionClosed):
                await session.receive()
            assert b"something went wrong" in session.stderr()

    async def test_the_container_is_gone_afterwards(self, engine):
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            assert session.alive
        assert not session.alive

    async def test_a_container_which_never_sends_a_newline(
        self,
        engine,
        monkeypatch,
    ):
        monkeypatch.setattr(_subprocess, "_MAX_LINE", 100)
        id = await engine.create("some-image")
        async with engine.start(id) as session:
            await session.send("flood")
            with pytest.raises(SessionClosed):
                await session.receive()


class TestCreating:
    async def test_networking_is_off_by_default(self, engine, argv):
        await engine.create("some-image")
        assert "'--network', 'none'" in argv()[0]

    async def test_networking_can_be_asked_for(self, engine, argv):
        await engine.create("some-image", network=True)
        assert "--network" not in argv()[0]

    async def test_stdin_is_always_open(self, engine, argv):
        await engine.create("some-image")
        assert "--interactive" in argv()[0]

    async def test_nonexistent_image(self, engine):
        with pytest.raises(NoSuchImage) as excinfo:
            await engine.create("nonexistent-image")
        assert excinfo.value.image == "nonexistent-image"

    async def test_pulls_only_when_needed(self, engine, argv):
        await engine.create_pulling_if_needed("some-image")
        assert not any(each.startswith("['pull'") for each in argv())

    async def test_pulls_when_missing(self, engine, argv):
        # The stand-in never starts existing, so this ends up back where
        # it started -- but only after having tried a pull.
        with pytest.raises(NoSuchImage):
            await engine.create_pulling_if_needed("nonexistent-image")
        assert any(each.startswith("['pull'") for each in argv())


class TestBuilding:
    """
    A directory is the one form of build context every engine takes.
    """

    async def test_from_a_directory(self, engine, argv, tmp_path):
        context = tmp_path / "context"
        context.mkdir()
        context.joinpath("Dockerfile").write_text("FROM scratch\n")
        await engine.build(tag="some-image", context=context)
        assert str(context) in argv()[0]

    async def test_a_context_which_isnt_there(self, engine, tmp_path):
        with pytest.raises(EngineFailed):
            await engine.build(tag="x", context=tmp_path / "nope")


class TestAttaching:
    async def test_nonexistent_container(self, engine):
        with pytest.raises(NoSuchContainer):
            async with engine.attach("nonexistent-container"):
                pass

    async def test_unsupported(self):
        engine = Engine(backend=CONTAINER)
        with pytest.raises(Unsupported) as excinfo:
            async with engine.attach("whatever"):
                pass
        assert excinfo.value.engine == "container"


class TestDetection:
    def test_no_engine_at_all(self):
        nowhere = Backend(name="definitely-not-installed-anywhere")
        with pytest.raises(NoSuchEngine):
            Engine.detect(nowhere)

    def test_by_name(self):
        assert Engine.named("podman").name == "podman"

    def test_by_unknown_name(self):
        with pytest.raises(NoSuchEngine):
            Engine.named("kubernetes-lol")


class TestClassification:
    """
    Each engine says the same things differently, and none of them
    usefully.
    """

    @pytest.mark.parametrize(
        "backend, stderr",
        [
            (DOCKER, "Cannot connect to the Docker daemon at unix://x.sock"),
            (DOCKER, "Is the docker daemon running?"),
            (PODMAN, "Cannot connect to Podman. Please verify your conn"),
            (PODMAN, "Error: unable to connect to Podman socket"),
            (CONTAINER, 'interrupted: "XPC connection error: Connection'),
            (
                CONTAINER,
                "Ensure container system service has been started with "
                "`container system start`.",
            ),
        ],
    )
    def test_not_running(self, backend, stderr):
        error = backend.classify(
            argv=("x",),
            returncode=1,
            stderr=stderr,
            subject="whatever",
        )
        assert isinstance(error, EngineNotRunning)

    @pytest.mark.parametrize(
        "backend, stderr",
        [
            (
                DOCKER,
                "Error response from daemon: manifest for foo:latest not "
                "found: manifest unknown",
            ),
            (DOCKER, "Error response from daemon: pull access denied for x"),
            (DOCKER, 'Head "https://ghcr.io/v2/x/manifests/latest": denied'),
            (PODMAN, "Error: unable to find a name and tag match for x"),
            (PODMAN, 'Head "https://ghcr.io/v2/x/manifests/latest": denied'),
        ],
    )
    def test_no_such_image(self, backend, stderr):
        error = backend.classify(
            argv=("x",),
            returncode=1,
            stderr=stderr,
            subject="some-image",
        )
        assert isinstance(error, NoSuchImage)
        assert error.image == "some-image"

    @pytest.mark.parametrize(
        "backend, stderr",
        [
            (DOCKER, "Error response from daemon: No such container: abcd"),
            (PODMAN, 'Error: no container with name or ID "abcd" found'),
        ],
    )
    def test_no_such_container(self, backend, stderr):
        error = backend.classify(
            argv=("x",),
            returncode=1,
            stderr=stderr,
            subject="abcd",
        )
        assert isinstance(error, NoSuchContainer)
        assert error.id == "abcd"

    def test_a_downed_engine_beats_a_missing_image(self):
        """
        An engine which isn't running will cheerfully tell you an image
        doesn't exist, which is true but unhelpful.
        """
        error = DOCKER.classify(
            argv=("x",),
            returncode=1,
            stderr=(
                "Cannot connect to the Docker daemon. "
                "manifest unknown"  # both, and the daemon is the story
            ),
            subject="some-image",
        )
        assert isinstance(error, EngineNotRunning)

    def test_anything_else(self):
        error = DOCKER.classify(
            argv=("docker", "create", "x"),
            returncode=125,
            stderr="something nobody has ever seen before",
            subject="x",
        )
        assert isinstance(error, EngineFailed)
        assert "something nobody has ever seen before" in str(error)
