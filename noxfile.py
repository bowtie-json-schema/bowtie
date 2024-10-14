from contextlib import ExitStack
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory
from textwrap import dedent
from zipfile import ZipFile
import os
import shlex
import tarfile

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
DOCS = ROOT / "docs"
BOWTIE = ROOT / "bowtie"
SCHEMAS = BOWTIE / "schemas"
IMPLEMENTATIONS = ROOT / "implementations"

UI = ROOT / "frontend"
UI_NEEDS_INSTALL = not UI.joinpath("node_modules").is_dir()

REQUIREMENTS = dict(
    main=ROOT / "requirements.txt",
    docs=DOCS / "requirements.txt",
    tests=ROOT / "test-requirements.txt",
)
REQUIREMENTS_IN = [  # this is actually ordered, as files depend on each other
    (
        (
            ROOT / "pyproject.toml"
            if path.absolute() == REQUIREMENTS["main"].absolute()
            else path.parent / f"{path.stem}.in"
        ),
        path,
    )
    for path in REQUIREMENTS.values()
]


SUPPORTED = ["3.12", "3.13"]
LATEST = SUPPORTED[-1]

nox.options.default_venv_backend = "uv|virtualenv"
nox.options.sessions = []


def session(default=True, python=LATEST, **kwargs):  # noqa: D103
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(python=python, **kwargs)(fn)

    return _session


def _install_coverage_hook(session: nox.Session):
    """
    Enable measurement of coverage in sub-processes.

    See https://coverage.readthedocs.io/en/latest/subprocess.html.
    """
    session.run(
        "python",
        "-c",
        dedent(
            r"""
            from pathlib import Path
            import sysconfig

            Path(sysconfig.get_path("purelib")).joinpath("coverage.pth").write_text(
                "import coverage; coverage.process_startup()\n",
                encoding="utf-8",
            )
            """,
        ).lstrip("\n"),
    )


@session(python=SUPPORTED)
def tests(session):
    """
    Run Bowtie's test suite.
    """
    session.install("-r", REQUIREMENTS["tests"])

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            github = Path(os.environ["GITHUB_STEP_SUMMARY"])
        else:
            github = None

        session.install("coverage[toml]")

        _install_coverage_hook(session)
        with TemporaryDirectory() as _tmpdir:
            tmpdir = Path(_tmpdir)
            coverage = os.environ.get("COVERAGE_FILE", tmpdir / "coverage")
            env = dict(
                COVERAGE_PROCESS_START=os.fsencode(PYPROJECT.resolve()),
                COVERAGE_FILE=os.fsencode(coverage),
            )
            session.run(
                "coverage",
                "run",
                "-m",
                "pytest",
                BOWTIE,
                env=env,
            )
            session.run("coverage", "combine", env=env)
            if github is None:
                session.run("coverage", "report", env=env)
            else:
                with github.open("a") as summary:
                    summary.write("### Coverage\n\n")
                    summary.flush()  # without flush, output seems out of order
                    session.run(
                        "coverage",
                        "report",
                        "--format=markdown",
                        stdout=summary,
                        env=env,
                    )
    else:
        session.run("pytest", *session.posargs, BOWTIE)


@session(python=SUPPORTED)
def audit(session):
    """
    Audit Python dependencies for vulnerabilities.
    """
    session.install("pip-audit", "-r", REQUIREMENTS["main"])
    session.run("python", "-m", "pip_audit")


@session(tags=["build"])
def build(session):
    """
    Build Bowtie (via a PEP517 builder), and check the built artifact is valid.
    """
    session.install("build", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")

        schemas = frozenset(SCHEMAS.rglob("*.json"))
        assert schemas, "Didn't find any schemas!"

        tmpdir = Path(tmpdir)

        (tarpath,) = tmpdir.glob("*.tar.gz")
        with tarfile.open(tarpath) as tar:
            found = {
                SCHEMAS.joinpath(member.name.split("/", 3)[3]).absolute()
                for member in tar
                if "bowtie/schemas" in member.name
            }
            if not schemas <= found:
                session.error(
                    "Tar distribution schemas are missing. "
                    f"Expected {schemas} but found {found}.",
                )

        (wheelpath,) = tmpdir.glob("*.whl")
        wheel = ZipFile(wheelpath)
        found = {
            SCHEMAS.joinpath(name.removeprefix("bowtie/schemas/")).absolute()
            for name in wheel.namelist()
            if name.startswith("bowtie/schemas")
        }
        if not schemas <= found:
            session.error(
                "Wheel distribution schemas are missing. "
                f"Expected {schemas} but found {found}.",
            )


@session(default=False, tags=["build"])
def app(session):
    """
    Build a PyApp which will run Bowtie.
    """
    session.install("hatch")
    session.run("hatch", "build", "-t", "binary", *session.posargs)


@session(tags=["style"])
def style(session):
    """
    Lint for style on Bowtie's Python codebase.
    """
    session.install("ruff")
    session.run("ruff", "check", BOWTIE, *ROOT.glob("*.py"))


@session()
def typing(session):
    """
    Check Bowtie's codebase using pyright.
    """
    session.install("pyright", f"{ROOT}[strategies]")
    session.run("pyright", *session.posargs, BOWTIE)


@session(tags=["docs"])
@nox.parametrize(
    "builder",
    [
        nox.param(name, id=name)
        for name in [
            "dirhtml",
            "doctest",
            "linkcheck",
            "man",
            "spelling",
        ]
    ],
)
def docs(session, builder):
    """
    Build Bowtie's documentation.
    """
    session.install("-r", REQUIREMENTS["docs"])
    with TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        argv = ["-n", "-T", "-W"]
        if builder != "spelling":
            argv += ["-q"]
        posargs = session.posargs or [tmpdir / builder]
        session.run(
            "python",
            "-m",
            "sphinx",
            "-b",
            builder,
            DOCS,
            *argv,
            *posargs,
        )


@session(tags=["docs", "style"], name="docs(style)")
def docs_style(session):
    """
    Check Bowtie's documentation style.
    """
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", "--config", PYPROJECT, DOCS)


def benchmark(fn):
    """
    A non-default noxenv to run a specific benchmark.
    """
    name = fn.__name__.removeprefix("bench_")

    @session(default=False, tags=["perf"], name=f"bench({name})")
    @wraps(fn)
    def _benchmark(session):
        session.install("-r", REQUIREMENTS["main"], ROOT)
        bowtie = Path(session.bin) / "bowtie"
        hyperfine_args, command = fn(session=session, bowtie=bowtie)
        session.run("hyperfine", *hyperfine_args, command, external=True)

    return _benchmark


@benchmark
def bench_info(session, bowtie):
    """
    Time how long ``bowtie info`` takes to run (effectively startup time).
    """
    if session.posargs:
        args = session.posargs
    else:
        args = [
            "--warmup",
            "3",
            "-L",
            "implementation",
            ",".join(p.name for p in IMPLEMENTATIONS.iterdir() if p.is_dir()),
        ]
    return args, f"{bowtie} info -i {{implementation}}"


@benchmark
def bench_smoke(session, bowtie):
    """
    Time how long ``bowtie smoke`` takes to run (startup + ~2 simple examples).
    """
    if session.posargs:
        args = session.posargs
    else:
        args = [
            "--warmup",
            "3",
            "-L",
            "implementation",
            ",".join(p.name for p in IMPLEMENTATIONS.iterdir() if p.is_dir()),
        ]
    return args, f"{bowtie} smoke -i {{implementation}}"


@benchmark
def bench_suite(session, bowtie):
    """
    Time how long ``bowtie suite`` takes to run a version of the test suite.
    """
    if not session.posargs:
        session.error("Provide a test suite to benchmark")

    posargs = shlex.join(session.posargs)
    if "-i" not in session.posargs:
        args = [
            "--warmup",
            "1",
            # because not all implementations will likely support the dialect
            "--ignore-failure",
            "-L",
            "implementation",
            ",".join(p.name for p in IMPLEMENTATIONS.iterdir() if p.is_dir()),
        ]
        command = f"{bowtie} suite -i {{implementation}} {posargs}"
    else:
        args, command = [], f"{bowtie} suite {posargs}"
    return args, command


@session(default=False, python=False)
def develop_harness(session):
    """
    Build a local version of an implementation harness.

    The harness will be smoke tested after build, relying on Bowtie being
    available on your ``PATH``.
    This is used / useful during development of a new harness.

    For "real" versions of harnesses, rely on the built version from GitHub
    packages.
    """
    for each in session.posargs:
        each, has_version, version = each.partition("@")
        build_args = [
            "--build-arg",
            f"IMPLEMENTATION_VERSION={version}",
        ]
        tag = f":{version}" if has_version else ""

        name = Path(each).name
        session.run(
            "podman",
            "build",
            "-f",
            IMPLEMENTATIONS / name / "Dockerfile",
            "-t",
            f"ghcr.io/bowtie-json-schema/{name}{tag}",
            *build_args if has_version else [],
            external=True,
        )
        session.run("bowtie", "smoke", "--quiet", "-i", name, external=True)


@session(default=False)
def requirements(session):
    """
    Update bowtie's requirements.txt files.
    """
    if session.venv_backend == "uv":
        cmd = ["uv", "pip", "compile", "--no-cache"]
    else:
        session.install("pip-tools")
        cmd = ["pip-compile", "--resolver", "backtracking", "--strip-extras"]

    for each, out in REQUIREMENTS_IN:
        # otherwise output files end up with silly absolute path comments...
        relative = each.relative_to(ROOT)
        session.run(*cmd, "--upgrade", "--output-file", out, relative)


@session(default=False, python=False)
def ui(session):
    """
    Run a local development UI.

    You can use `nox -s ui -- --pr 123` to automatically checkout a pull
    request.
    """
    pnpm(session.run_install, "install", "--frozen-lockfile")

    with ExitStack() as stack:
        if session.posargs and session.posargs[0] == "--pr":
            _, pr = session.posargs
            session.run("gh", "pr", "checkout", pr, external=True)
            stack.callback(
                lambda: session.run("git", "switch", "-", external=True),
            )

        pnpm(session.run, "run", "start")


@session(python=False, tags=["ui"], name="ui(audit)")
def ui_audit(session):
    """
    Audit the UI dependencies.
    """
    pnpm(session.run, "audit")


@session(python=False, tags=["build", "ui"], name="ui(build)")
def ui_build(session):
    """
    Check that the UI properly builds.
    """
    pnpm(session.run_install, "install", "--frozen-lockfile")
    pnpm(session.run, "run", "build")


@session(python=False, tags=["style", "ui"], name="ui(style)")
def ui_style(session):
    """
    Lint for style on Bowtie's frontend.
    """
    pnpm(session.run_install, "install", "--frozen-lockfile")
    pnpm(session.run, "run", "lint")


@session(tags=["ui"], name="ui(tests)")
def ui_tests(session):
    """
    Run the UI tests.
    """
    session.install("-r", REQUIREMENTS["main"], "-e", ROOT)
    pnpm(session.run, "install-test", "--frozen-lockfile")


def pnpm(run, *args):
    """
    Run pnpm on the UI.
    """
    run("pnpm", "--dir", UI, *args, external=True)
