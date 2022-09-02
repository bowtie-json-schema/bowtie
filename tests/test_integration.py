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


@pytest_asyncio.fixture(scope='function')
async def lintsonschema(docker):
    tag = "bowtie-integration-tests/lintsonschema"
    await docker.images.build(
        fileobj=tar_from_directory(FAUXMPLEMENTATIONS / "lintsonschema"),
        encoding="utf-8",
        tag=tag
    )
    yield tag
    await docker.images.delete(name=tag)


@pytest.mark.asyncio
async def test_lint(lintsonschema):

    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "bowtie", "run",
        "-i", lintsonschema,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate(
        dedent(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """
        ).lstrip("\n").encode("utf-8")
    )

    assert stderr.decode() == ""
    assert proc.returncode == 0
