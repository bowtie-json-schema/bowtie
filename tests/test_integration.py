from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from textwrap import dedent
import asyncio
import os
import sys
import tarfile

import pytest
import pytest_asyncio

HERE = Path(__file__).parent
FAUXMPLEMENTATIONS = HERE / "fauxmplementations"


def tar_from_directory(directory):
    fileobj = BytesIO()
    tar = tarfile.TarFile(fileobj=fileobj, mode="w")
    for file in directory.iterdir():
        tar.add(file, file.name)
    tar.close()
    fileobj.seek(0)
    return fileobj


@pytest_asyncio.fixture(scope="module")
async def lintsonschema(docker):
    tag = "bowtie-integration-tests/lintsonschema"
    await docker.images.build(
        fileobj=tar_from_directory(FAUXMPLEMENTATIONS / "lintsonschema"),
        encoding="utf-8",
        tag=tag,
    )
    yield tag
    await docker.images.delete(name=tag)


@asynccontextmanager
async def bowtie(*args):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "bowtie", "run", *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _send(stdin):
        result = await proc.communicate(dedent(stdin).lstrip("\n").encode())
        return proc.returncode, *result
    yield _send


@pytest.mark.asyncio
async def test_lint(lintsonschema):
    async with bowtie("-i", lintsonschema) as send:
        returncode, stdout, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert stderr.decode() == ""
    assert returncode == 0


@pytest.mark.asyncio
async def test_no_tests_run(lintsonschema):
    async with bowtie("-i", lintsonschema) as send:
        returncode, stdout, stderr = await send("")

    assert stderr.decode() == ""
    assert returncode == os.EX_DATAERR
