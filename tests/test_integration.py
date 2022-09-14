from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from textwrap import dedent
import asyncio
import json
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


def image(name):
    @pytest_asyncio.fixture(scope="module")
    async def _image(docker):
        tag = f"bowtie-integration-tests/{name}"
        await docker.images.build(
            fileobj=tar_from_directory(FAUXMPLEMENTATIONS / name),
            encoding="utf-8",
            tag=tag,
        )
        yield tag
        await docker.images.delete(name=tag, force=True)
    return _image


lintsonschema = image("lintsonschema")
envsonschema = image("envsonschema")


@asynccontextmanager
async def bowtie(*args):
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "bowtie", "run", *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _send(stdin=""):
        input = dedent(stdin).lstrip("\n").encode()
        stdout, stderr = await proc.communicate(input)
        lines = (json.loads(line.decode()) for line in stdout.splitlines())

        metadata = next(lines)
        assert metadata.keys() == {"implementations"}

        results = sorted(
            (each for each in lines if "implementation" in each),
            key=lambda each: each["implementation"],
        )
        return proc.returncode, results, stderr
    yield _send


@pytest.mark.asyncio
async def test_lint(lintsonschema):
    async with bowtie("-i", lintsonschema) as send:
        returncode, results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    got = [[test for test in each["results"]] for each in results]
    assert got == [[{"valid": True}]]
    assert returncode == 0


@pytest.mark.asyncio
async def test_it_runs_tests_from_a_file(tmp_path, lintsonschema):
    tests = tmp_path / "tests.jsonl"
    tests.write_text("""{"description": "foo", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }\n""")  # noqa: E501
    async with bowtie("-i", lintsonschema, tests) as send:
        returncode, results, stderr = await send()

    got = [[test for test in each["results"]] for each in results]
    assert got == [[{"valid": True}]]
    assert returncode == 0


@pytest.mark.asyncio
async def test_no_tests_run(lintsonschema):
    async with bowtie("-i", lintsonschema) as send:
        returncode, results, stderr = await send("")

    assert results == []
    assert stderr != ""
    assert returncode == os.EX_DATAERR


@pytest.mark.asyncio
async def test_unsupported_dialect(lintsonschema):
    dialect = "some://other/URI/"
    async with bowtie("-i", lintsonschema, "--dialect", dialect) as send:
        returncode, results, stderr = await send("")

    assert results == []
    assert b"unsupported dialect" in stderr.lower()
    assert returncode == os.EX_DATAERR


@pytest.mark.asyncio
async def test_restarts_crashed_implementations(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "a", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "sleep:8", "instance": {}}] }
            """,  # noqa: E501
        )

    got = [[test for test in each["results"]] for each in results]
    assert got == [[{"valid": False}]]
    assert stderr != ""
    assert returncode == 0


@pytest.mark.asyncio
async def test_implementations_can_signal_errors(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, stderr = await send(
            """
            {"description": "error:", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "4", "schema": {}, "tests": [{"description": "error:message=boom", "instance": {}}] }
            {"description": "works", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    got = [[test for test in each["results"]] for each in results]
    assert got == [[{"valid": True}]]
    assert stderr != ""
    assert returncode == 0


@pytest.mark.asyncio
async def test_it_handles_split_messages(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, stderr = await send(
            """
            {"description": "split:1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}, {"description": "2 valid:0", "instance": {}}] }
            """,  # noqa: E501
        )

    got = [[test for test in each["results"]] for each in results]
    assert got == [[{"valid": True}, {"valid": False}]]
    assert returncode == 0
