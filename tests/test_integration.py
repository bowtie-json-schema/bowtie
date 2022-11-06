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

from bowtie._report import RunInfo, _InvalidBowtieReport

HERE = Path(__file__).parent
FAUXMPLEMENTATIONS = HERE / "fauxmplementations"


def tar_from_directory(directory):
    fileobj = BytesIO()
    with tarfile.TarFile(fileobj=fileobj, mode="w") as tar:
        for file in directory.iterdir():
            tar.add(file, file.name)
    fileobj.seek(0)
    return fileobj


def image(name, fileobj):
    @pytest_asyncio.fixture(scope="module")
    async def _image(docker):
        tag = f"bowtie-integration-tests/{name}"
        await docker.images.build(fileobj=fileobj, encoding="utf-8", tag=tag)
        yield tag
        await docker.images.delete(name=tag, force=True)

    return _image


def fauxmplementation(name):
    fileobj = tar_from_directory(FAUXMPLEMENTATIONS / name)
    return image(name=name, fileobj=fileobj)


def strimplementation(name, contents):
    fileobj = BytesIO()
    with tarfile.TarFile(fileobj=fileobj, mode="w") as tar:
        contents = dedent(contents).encode("utf-8")
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(contents)
        tar.addfile(info, BytesIO(contents))
    fileobj.seek(0)
    return image(name=name, fileobj=fileobj)


lintsonschema = fauxmplementation("lintsonschema")
envsonschema = fauxmplementation("envsonschema")
succeed_immediately = strimplementation(
    name="succeed",
    contents="FROM alpine:3.16\nENTRYPOINT true\n",
)
fail_on_run = strimplementation(
    name="fail_on_run",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf '{"implementation": {"dialects": ["urn:foo"]}, "ready": true, "version": 1}\n' && read && printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
hit_the_network = strimplementation(
    name="hit_the_network",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf '{"implementation": {"dialects": ["urn:foo"]}, "ready": true, "version": 1}\n' && read && printf '{"ok": true}\n' && read && wget --timeout=1 -O - http://example.com >&2 && printf '{"seq": 0, "results": [{"valid": true}]}\n' && read
    """,  # noqa: E501
)


@asynccontextmanager
async def bowtie(*args, succeed=True):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        *args,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _send(stdin=""):
        input = dedent(stdin).lstrip("\n").encode()
        stdout, stderr = await proc.communicate(input)
        lines = (json.loads(line.decode()) for line in stdout.splitlines())

        if succeed:
            try:
                RunInfo.from_header_lines(next(lines, None), next(lines))
            except _InvalidBowtieReport:
                pytest.fail(f"Invalid report, stderr contained: {stderr}")
        else:
            assert proc.returncode != 0

        successful, errors, cases = [], [], []
        for each in sorted(lines, key=lambda e: e.get("implementation", "")):
            if "results" in each:
                successful.append(each["results"])
            elif "case" in each:
                cases.append(each)
            else:
                errors.append(each)

        return proc.returncode, successful, errors, cases, stderr

    yield _send


@pytest.mark.asyncio
async def test_validating_on_both_sides(lintsonschema):
    async with bowtie("-i", lintsonschema, "-V") as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}]], stderr
    assert returncode == 0


@pytest.mark.asyncio
async def test_it_runs_tests_from_a_file(tmp_path, envsonschema):
    tests = tmp_path / "tests.jsonl"
    tests.write_text(
        """{"description": "foo", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }\n""",  # noqa: E501
    )
    async with bowtie("-i", envsonschema, tests) as send:
        returncode, results, _, _, stderr = await send()

    assert results == [[{"valid": False}]], stderr
    assert returncode == 0


@pytest.mark.asyncio
async def test_set_schema_sets_a_dialect_explicitly(envsonschema):
    async with bowtie("-i", envsonschema, "--set-schema") as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}]], stderr
    assert returncode == 0


@pytest.mark.asyncio
async def test_no_tests_run(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, _, cases, stderr = await send("")

    assert results == []
    assert cases == []
    assert stderr != ""
    assert returncode == os.EX_NOINPUT


@pytest.mark.asyncio
async def test_unsupported_dialect(envsonschema):
    dialect = "some://other/URI/"
    async with bowtie(
        "-i",
        envsonschema,
        "--dialect",
        dialect,
        succeed=False,
    ) as send:
        returncode, results, _, _, stderr = await send("")

    assert results == []
    assert b"unsupported dialect" in stderr.lower()
    assert returncode != 0


@pytest.mark.asyncio
async def test_restarts_crashed_implementations(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "a", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "sleep:8", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": False}]]
    assert stderr != ""
    assert returncode == 0, stderr


@pytest.mark.asyncio
async def test_handles_dead_implementations(succeed_immediately, envsonschema):
    async with bowtie("-i", succeed_immediately, "-i", envsonschema) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": False}], [{"valid": False}]]
    assert b"startup failed" in stderr.lower(), stderr
    assert returncode != 0, stderr


@pytest.mark.asyncio
async def test_it_exits_when_no_implementations_succeed(succeed_immediately):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with bowtie("-i", succeed_immediately, succeed=False) as send:
        returncode, results, _, cases, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert cases == []
    assert b"startup failed" in stderr.lower(), stderr
    assert returncode != 0, stderr


@pytest.mark.asyncio
async def test_handles_broken_run_implementations(fail_on_run):
    async with bowtie(
        "-i",
        fail_on_run,
        "--dialect",
        "urn:foo",
        succeed=False,
    ) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert b"got an error" in stderr.lower(), stderr
    assert returncode != 0, stderr


@pytest.mark.asyncio
async def test_implementations_can_signal_errors(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "error:", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "4", "schema": {}, "tests": [{"description": "error:message=boom", "instance": {}}] }
            {"description": "works", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}]], stderr
    assert stderr != ""
    assert returncode == 0, stderr


@pytest.mark.asyncio
async def test_it_handles_split_messages(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "split:1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}, {"description": "2 valid:0", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}, {"valid": False}]]
    assert returncode == 0


@pytest.mark.asyncio
async def test_it_prevents_network_access(hit_the_network):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with bowtie("-i", hit_the_network, "--dialect", "urn:foo") as send:
        returncode, results, errors, cases, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert b"bad address" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_fail_fast(envsonschema):
    async with bowtie("-i", envsonschema, "-x") as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "3", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}], [{"valid": False}]], stderr
    assert stderr != ""
    assert returncode == 0, stderr


@pytest.mark.asyncio
async def test_smoke(envsonschema):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "-i",
        envsonschema,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, _ = await proc.communicate()
    # FIXME: This != 0 is because indeed envsonschema gets answers wrong
    #        Change to asserting about the smoke stdout once that's there.
    assert proc.returncode != 0
