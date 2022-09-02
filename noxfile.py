from pathlib import Path

import nox

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
BOWTIE = ROOT / "bowtie"


@nox.session(python=["3.8", "3.9", "3.10"])
def tests(session):
    session.install(str(ROOT), "pytest")
    session.run("pytest")


@nox.session
def build(session):
    session.install("build")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", str(ROOT), "--outdir", tmpdir)


@nox.session
def readme(session):
    session.install("build", "twine")
    tmpdir = session.create_tmp()
    session.run("python", "-m", "build", str(ROOT), "--outdir", tmpdir)
    session.run("python", "-m", "twine", "check", tmpdir + "/*")


@nox.session
def style(session):
    session.install(
        "flake8",
        "flake8-broken-line",
        "flake8-bugbear",
        "flake8-commas",
        "flake8-quotes",
        "flake8-tidy-imports",
    )
    session.run("python", "-m", "flake8", str(BOWTIE))


@nox.session
def docs(session):
    session.install("-r", str(DOCS / "requirements.txt"))
    tmpdir = session.create_tmp()
    session.run(
        "python", "-m", "sphinx", "-b", "dirhtml",
        str(DOCS), tmpdir, "-n", "-q", "-T", "-W",
    )


@nox.session
def docs_style(session):
    session.install(
        "doc8",
        "pygments",
        "pygments-github-lexers",
    )
    session.run("python", "-m", "doc8", str(DOCS))
