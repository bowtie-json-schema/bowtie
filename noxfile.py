from contextlib import ExitStack
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import shlex

import nox

ROOT = Path(__file__).parent
PYPROJECT = ROOT / "pyproject.toml"
DOCS = ROOT / "docs"
BOWTIE = ROOT / "bowtie"
IMPLEMENTATIONS = ROOT / "implementations"
TESTS = ROOT / "tests"


nox.options.sessions = []


def session(default=True, **kwargs):
    def _session(fn):
        if default:
            nox.options.sessions.append(kwargs.get("name", fn.__name__))
        return nox.session(**kwargs)(fn)

    return _session


@session(python=["3.10", "3.11"])
def tests(session):
    """
    Run Bowtie's test suite.
    """
    session.install("-r", ROOT / "test-requirements.txt")

    if session.posargs and session.posargs[0] == "coverage":
        if len(session.posargs) > 1 and session.posargs[1] == "github":
            github = os.environ["GITHUB_STEP_SUMMARY"]
        else:
            github = None

        session.install("coverage[toml]")
        session.run("coverage", "run", "-m", "pytest", TESTS)
        if github is None:
            session.run("coverage", "report")
        else:
            with open(github, "a") as summary:
                summary.write("### Coverage\n\n")
                summary.flush()  # without a flush, output seems out of order.
                session.run(
                    "coverage",
                    "report",
                    "--format=markdown",
                    stdout=summary,
                )
    else:
        session.run("pytest", *session.posargs, TESTS)


@session(tags=["build"])
def build(session):
    """
    Build Bowtie (via a PEP517 builder), and check the built artifact is valid.
    """
    session.install("build", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")


@session(tags=["build"])
def shiv(session):
    """
    Build a shiv which will run Bowtie.
    """
    session.install("shiv")

    with ExitStack() as stack:
        if session.posargs:
            out = session.posargs[0]
        else:
            tmpdir = Path(stack.enter_context(TemporaryDirectory()))
            out = tmpdir / "bowtie"
        session.run(
            "python",
            "-m",
            "shiv",
            "--reproducible",
            "-c",
            "bowtie",
            ROOT,
            "-o",
            out,
        )
        print(f"Outputted a shiv to {out}.")


@session(tags=["style"])
def style(session):
    """
    Lint for style on Bowtie's Python codebase.
    """
    session.install("ruff")
    session.run("ruff", "check", BOWTIE, TESTS, __file__)


@session()
def typing(session):
    """
    Check Bowtie's codebase using pyright.
    """
    session.install("pyright", ROOT)
    session.run("pyright", BOWTIE)


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
    session.install("-r", DOCS / "requirements.txt")
    with TemporaryDirectory() as tmpdir_str:
        tmpdir = Path(tmpdir_str)
        argv = ["-n", "-T", "-W"]
        if builder != "spelling":
            argv += ["-q"]
        session.run(
            "python",
            "-m",
            "sphinx",
            "-b",
            builder,
            DOCS,
            tmpdir / builder,
            *argv,
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
        session.install(ROOT)
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


@session(default=False)
def requirements(session):
    """
    Update bowtie's requirements.txt files.
    """
    session.install("pip-tools")
    for each in [DOCS / "requirements.in", ROOT / "test-requirements.in"]:
        session.run(
            "pip-compile",
            "--resolver",
            "backtracking",
            "-U",
            each.relative_to(ROOT),
        )
