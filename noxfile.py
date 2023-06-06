from contextlib import ExitStack
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


@session(python=["3.8", "3.9", "3.10", "3.11"])
def tests(session):
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
    session.install("build", "twine")
    with TemporaryDirectory() as tmpdir:
        session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
        session.run("twine", "check", "--strict", tmpdir + "/*")


@session(tags=["build"])
def shiv(session):
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
    session.install("ruff")
    session.run("ruff", "check", BOWTIE, TESTS, __file__)


@session()
def typing(session):
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
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", "--config", PYPROJECT, DOCS)


@session(default=False, tags=["perf"], name="bench(info)")
def bench_info(session):
    """
    Time how long ``bowtie info`` takes to run (effectively startup time).
    """
    session.install(ROOT)
    executable = Path(session.bin) / "bowtie"

    cmd = f"{executable} info -i {{implementation}}"

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

    session.run("hyperfine", *args, cmd, external=True)


@session(default=False, tags=["perf"], name="bench(smoke)")
def bench_smoke(session):
    """
    Time how long ``bowtie smoke`` takes to run (startup + ~2 simple examples).
    """
    session.install(ROOT)
    executable = Path(session.bin) / "bowtie"

    cmd = f"{executable} smoke -i {{implementation}}"

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

    session.run("hyperfine", *args, cmd, external=True)


@session(default=False, tags=["perf"], name="bench(suite)")
def bench_suite(session):
    if not session.posargs:
        session.error("Provide a test suite to benchmark")

    session.install(ROOT)
    bowtie = Path(session.bin) / "bowtie"

    posargs = shlex.join(session.posargs)
    if "-i" not in session.posargs:
        args = [
            "-L",
            "implementation",
            ",".join(p.name for p in IMPLEMENTATIONS.iterdir() if p.is_dir()),
            f"{bowtie} suite -i {{implementation}} {posargs}",
        ]
    else:
        args = [f"{bowtie} suite {posargs}"]
    session.run("hyperfine", "--warmup", "1", *args, external=True)


@session(default=False)
def requirements(session):
    session.install("pip-tools")
    for each in [DOCS / "requirements.in", ROOT / "test-requirements.in"]:
        session.run(
            "pip-compile",
            "--resolver",
            "backtracking",
            "-U",
            each.relative_to(ROOT),
        )
