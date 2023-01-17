from pathlib import Path
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
    session.run("pytest", "--verbosity=3")


@session(tags=["build"])
def build(session):
    session.install("build")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)


@session(tags=["build"])
def shiv(session):
    session.install("shiv")
    if session.posargs:
        out = session.posargs[0]
    else:
        tmpdir = Path(session.create_tmp())
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
def readme(session):
    session.install("build", "twine")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", ROOT, "--outdir", tmpdir)
    session.run("python", "-m", "twine", "check", tmpdir + "/*")


@session(tags=["style"])
def style(session):
    session.install(
        "flake8",
        "flake8-broken-line",
        "flake8-bugbear",
        "flake8-commas",
        "flake8-quotes",
        "flake8-tidy-imports",
    )
    session.run("python", "-m", "flake8", BOWTIE, TESTS, __file__)


@session()
def typing(session):
    session.install("pyright", "types-jsonschema", ROOT)
    session.run("python", "-m", "pyright", BOWTIE)


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
    tmpdir = Path(session.create_tmp())
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


@session(default=False, tags=["perf"], name="bench(smoke)")
def bench_smoke(session):
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
