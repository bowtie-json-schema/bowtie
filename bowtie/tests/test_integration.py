from collections.abc import Iterable
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from pprint import pformat
from textwrap import dedent
import asyncio
import json as _json
import os
import platform
import re
import sys
import tarfile

from aiodocker.exceptions import DockerError
from dateutil.parser import isoparse, parse as parse_datetime
from dateutil.tz import tzlocal
from dateutil.utils import default_tzinfo, within_delta
from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode
import pexpect
import pytest
import pytest_asyncio

from bowtie._cli import EX
from bowtie._commands import ErroredTest, TestResult
from bowtie._core import (
    Dialect,
    Implementation,
    Test,
    TestCase,
)
from bowtie._direct_connectable import IMPLEMENTATIONS as KNOWN_DIRECT, Direct
from bowtie._report import EmptyReport, InvalidReport, Report
from bowtie.tests import miniatures as _miniatures

# Make pytest ignore these classes matching Test*
Test.__test__ = False
TestCase.__test__ = False
TestResult.__test__ = False


HERE = Path(__file__).parent
FAUXMPLEMENTATIONS = HERE / "fauxmplementations"

# Make believe we're wide for tests to avoid line breaks in rich-click.
WIDE_TERMINAL_ENV = dict(os.environ, TERMINAL_WIDTH="512")
WIDE_TERMINAL_ENV.pop("CI", None)  # Run subprocesses as if they're not in CI


class _Miniatures:
    def __getattr__(self, name: str):
        getattr(_miniatures, name)  # check for typos
        return f"direct:{_miniatures.__name__}:{name}"


miniatures = _Miniatures()

#: An arbitrary harness for when behavior shouldn't depend on a specific one.
ARBITRARY = miniatures.always_invalid

VALIDATORS = Direct.from_id("python-jsonschema").registry()


def tag(name: str):
    return f"bowtie-integration-tests/{name}"


async def command_validator(command):
    stdout, stderr = await bowtie(command, "--schema")
    assert stderr == "", stderr
    return VALIDATORS.for_schema(_json.loads(stdout))


async def bowtie(*argv, stdin: str = "", exit_code=EX.OK, json=False):
    """
    Run a Bowtie subprocess asynchronously to completion.

    An exit code of `-1` means "any non-zero exit code".
    """
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        *argv,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=WIDE_TERMINAL_ENV,
    )
    raw_stdout, raw_stderr = await process.communicate(stdin.encode())
    decoded = stdout, stderr = raw_stdout.decode(), raw_stderr.decode()

    if exit_code == -1:
        assert process.returncode != 0, decoded
    else:
        assert process.returncode == exit_code, decoded

    if json:
        if not stdout:
            pytest.fail(f"stdout was empty. stderr contained {stderr}")
        try:
            jsonout = _json.loads(stdout)
        except _json.JSONDecodeError:
            pytest.fail(
                f"stdout had invalid JSON: {stdout!r}\n\n"
                f"stderr had {stderr}",
            )
        return jsonout, stderr

    return decoded


def tar_from_directory(directory):
    fileobj = BytesIO()
    with tarfile.TarFile(fileobj=fileobj, mode="w") as tar:
        for file in directory.iterdir():
            tar.add(file, file.name)
    fileobj.seek(0)
    return fileobj


def tar_from_versioned_reports(
    tar_path: Path,
    id: str,
    versions: frozenset[str],
    versioned_reports: Iterable[tuple[str, Dialect, str]],
):
    with tarfile.TarFile(name=tar_path, mode="w") as tar:
        root_info = tarfile.TarInfo(f"./{id}")
        root_info.type = tarfile.DIRTYPE
        tar.addfile(root_info)

        if not versions:
            empty_file_info = tarfile.TarInfo(f"./{id}/.keep")
            empty_file_info.size = 0
            tar.addfile(empty_file_info, BytesIO(b""))
            return

        matrix_versions = _json.dumps(list(versions)).encode("utf-8")
        matrix_info = tarfile.TarInfo(f"./{id}/matrix-versions.json")
        matrix_info.size = len(matrix_versions)
        tar.addfile(matrix_info, BytesIO(matrix_versions))

        for version, dialect, stdout in versioned_reports:
            version_info = tarfile.TarInfo(f"./{id}/v{version}")
            version_info.type = tarfile.DIRTYPE
            tar.addfile(version_info)

            report_bytes = stdout.encode("utf-8")
            report_info = tarfile.TarInfo(
                f"./{id}/v{version}/{dialect.short_name}.json",
            )
            report_info.size = len(report_bytes)
            tar.addfile(report_info, BytesIO(report_bytes))


def image(name, fileobj):
    @pytest_asyncio.fixture(scope="module")
    async def _image(docker):
        images = docker.images
        t = tag(name)
        lines = await images.build(fileobj=fileobj, encoding="utf-8", tag=t)
        try:
            await docker.images.inspect(t)
        except DockerError:
            pytest.fail(f"Failed to build {name}:\n\n{pformat(lines)}")
        yield t
        await images.delete(name=t, force=True)

    return _image


def fauxmplementation(name):
    """
    A fake implementation built from files in the fauxmplementations directory.
    """
    fileobj = tar_from_directory(FAUXMPLEMENTATIONS / name)
    return image(name=name, fileobj=fileobj)


def strimplementation(name, contents, files={}, base="alpine:3.19"):
    """
    A fake implementation built from the given Dockerfile contents.
    """
    containerfile = f"FROM {base}\n{dedent(contents)}".encode()

    fileobj = BytesIO()
    with tarfile.TarFile(fileobj=fileobj, mode="w") as tar:
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(containerfile)
        tar.addfile(info, BytesIO(containerfile))

        for k, v in files.items():
            v = dedent(v).encode("utf-8")
            info = tarfile.TarInfo(name=k)
            info.size = len(v)
            tar.addfile(info, BytesIO(v))

    fileobj.seek(0)
    return image(name=name, fileobj=fileobj)


def shellplementation(name, contents):
    """
    A fake implementation which runs an assembled shell script for results.
    """
    return strimplementation(
        name=name,
        files={"run.sh": contents},
        contents="""
        COPY run.sh .
        CMD sh run.sh
        """,
    )


lintsonschema = fauxmplementation("lintsonschema")
envsonschema = fauxmplementation("envsonschema")
succeed_immediately = strimplementation(
    name="succeed",
    contents="ENTRYPOINT true",
)
fail_immediately = shellplementation(
    name="fail_immediately",
    contents=r"""
    printf 'BOOM!\n' >&2
    """,
)
fail_on_start = shellplementation(
    name="fail_on_start",
    contents=r"""
    read -r request
    printf 'BOOM!\n' >&2
    """,
)
fail_on_dialect = shellplementation(
    name="fail_on_dialect",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "fail-on-dialect", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
fail_on_run = shellplementation(
    name="fail_on_run",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "fail-on-run", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
nonjson_on_run = shellplementation(
    name="nonjson_on_run",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "nonjson-on-run", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    printf 'BOOM!\n'
    """,  # noqa: E501
)
wrong_seq = shellplementation(
    name="wrong_seq",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "wrong-seq", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    printf '{"seq": 373737373737, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
wrong_version = shellplementation(
    name="wrong_version",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "wrong-version", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 0}\n'
    read >&2
    """,  # noqa: E501
)
hit_the_network_once = shellplementation(
    name="hit_the_network_once",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "hit-the-network", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    wget --timeout=1 -O - http://example.com >&2
    read -r request
    printf '{"seq": %s, "results": [{"valid": true}]}\n' "$(sed 's/.*"seq":\s*\([^,]*\).*/\1/' <(echo $request))"
    """,  # noqa: E501
)
missing_homepage = shellplementation(
    name="missing_homepage",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "missing-homepage", "language": "sh", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"]}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    """,  # noqa: E501
)
with_versions = shellplementation(
    name="with_versions",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "with-versions", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"], "language_version": "123", "os": "Lunix", "os_version": "37"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    printf '{"seq": %s, "results": [{"valid": true}]}\n' "$(sed 's/.*"seq":\s*\([^,]*\).*/\1/' <(echo $request))"
    """,  # noqa: E501
)
wrong_number_of_tests = shellplementation(
    name="wrong_number_of_tests",
    contents=r"""
    read -r request
    printf '{"implementation": {"name": "wrong-number-of-tests", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read -r request
    printf '{"ok": true}\n'
    read -r request
    printf '{"seq": %s, "results": [{"valid": true}, {"valid": true}, {"valid": true}, {"valid": true}]}\n' "$(sed 's/.*"seq":\s*\([^,]*\).*/\1/' <(echo $request))"
    """,  # noqa: E501
)


@pytest_asyncio.fixture
async def envsonschema_container(docker, envsonschema):
    config = dict(
        Image=envsonschema,
        OpenStdin=True,
        HostConfig=dict(NetworkMode="none"),
    )
    container = await docker.containers.create(config=config)
    await container.start()
    yield f"container:{container.id}"

    # FIXME: When this happens, it's likely due to #1187.
    with suppress(DockerError):
        await container.delete()


@pytest_asyncio.fixture
async def lintsonschema_container(docker, lintsonschema):
    config = dict(
        Image=lintsonschema,
        OpenStdin=True,
        HostConfig=dict(NetworkMode="none"),
    )
    container = await docker.containers.create(config=config)
    await container.start()
    yield f"container:{container.id}"

    # FIXME: When this happens, it's likely due to #1187.
    with suppress(DockerError):
        await container.delete()


@asynccontextmanager
async def run(*args, **kwargs):
    async def _send(stdin=""):
        input = dedent(stdin).lstrip("\n")
        stdout, stderr = await bowtie("run", *args, stdin=input, **kwargs)

        try:
            report = Report.from_serialized(stdout.splitlines())
        except _json.JSONDecodeError:
            pytest.fail(
                f"stdout had invalid JSON: {stdout!r}\n\n"
                f"stderr had {stderr}",
            )
        except EmptyReport:
            results = []
        except InvalidReport as err:
            pytest.fail(f"Invalid report: {err}\nStderr had:\n{stderr}")
        else:
            results = [
                test_result
                for _, case_results in report.cases_with_results()
                for _, test_result in case_results
            ]
        return results, stderr

    yield _send


@pytest.mark.asyncio
@pytest.mark.containers
async def test_validating_on_both_sides(lintsonschema):
    async with run("-i", lintsonschema, "-V") as send:
        results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("lintsonschema"): TestResult.VALID},
    ], stderr


class TestRun:
    @pytest.mark.asyncio
    async def test_from_file(self, tmp_path):
        tests = tmp_path / "tests.jsonl"
        tests.write_text(
            """{"description": "foo", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }\n""",  # noqa: E501
        )

        async with run("-i", miniatures.always_invalid, tests) as send:
            results, stderr = await send()

        assert results == [
            {miniatures.always_invalid: TestResult.INVALID},
        ], stderr

    @pytest.mark.asyncio
    async def test_with_registry(self):
        raw = """
            {"description":"one","schema":{"type": "integer"}, "registry":{"urn:example:foo": "http://example.com"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        """  # noqa: E501

        run_stdout, run_stderr = await bowtie(
            "run",
            "-i",
            "direct:null",
            "-V",
            stdin=dedent(raw.strip("\n")),
        )

        jsonout, stderr = await bowtie(
            "summary",
            "--format",
            "json",
            "--show",
            "validation",
            stdin=run_stdout,
            json=True,
        )

        assert (await command_validator("summary")).validated(jsonout) == [
            [
                {"type": "integer"},
                [
                    [12, {"direct:null": "valid"}],
                    [12.5, {"direct:null": "valid"}],
                ],
            ],
        ], run_stderr
        assert stderr == ""


@pytest.mark.asyncio
async def test_suite(tmp_path):
    definitions = tmp_path / "tests/draft7/definitions.json"
    definitions.parent.mkdir(parents=True)
    definitions.write_text(
        _json.dumps(  # trimmed down definitions.json from the suite
            [
                {
                    "description": "the case",
                    "schema": {
                        "$ref": "http://json-schema.org/draft-07/schema#",
                    },
                    "tests": [
                        {
                            "description": "one",
                            "data": {"definitions": {}},
                            "valid": True,
                        },
                        {
                            "description": "two",
                            "data": {"definitions": 12},
                            "valid": False,
                        },
                    ],
                },
            ],
        ),
    )

    stdout, stderr = await bowtie(
        "suite",
        "-i",
        miniatures.always_invalid,
        definitions,
    )
    report = Report.from_serialized(stdout.splitlines())

    one = Test(
        description="one",
        instance={"definitions": {}},
        valid=True,
    )
    two = Test(
        description="two",
        instance={"definitions": 12},
        valid=False,
    )
    assert (report.metadata.dialect, list(report.cases_with_results())) == (
        Dialect.by_short_name()["draft7"],
        [
            (
                TestCase(
                    description="the case",
                    schema={"$ref": "http://json-schema.org/draft-07/schema#"},
                    tests=[one, two],
                ),
                [
                    (
                        one,
                        {
                            miniatures.always_invalid: TestResult.INVALID,
                        },
                    ),
                    (
                        two,
                        {
                            miniatures.always_invalid: TestResult.INVALID,
                        },
                    ),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_set_schema_sets_a_dialect_explicitly():
    async with run("-i", "direct:null", "--set-schema") as send:
        results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    # XXX: we need to make run() return the whole report
    assert results == [{"direct:null": TestResult.VALID}], stderr


@pytest.mark.asyncio
async def test_no_tests_run():
    async with run("-i", ARBITRARY, exit_code=EX.NOINPUT) as send:
        results, stderr = await send("")

    assert results == []
    assert stderr != ""


@pytest.mark.asyncio
async def test_unknown_dialect():
    dialect = "some://other/URI/"
    async with run(
        "-i",
        ARBITRARY,
        "--dialect",
        dialect,
        exit_code=2,  # comes from click
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "not a known dialect" in stderr, stderr


@pytest.mark.asyncio
async def test_nonurl_dialect():
    dialect = ";;;;;"
    async with run(
        "-i",
        ARBITRARY,
        "--dialect",
        dialect,
        exit_code=2,  # comes from click
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "not a known dialect" in stderr, stderr


@pytest.mark.asyncio
async def test_unsupported_known_dialect():
    async with run(
        "-i",
        miniatures.only_supports + ",dialect=draft3",
        "--dialect",
        str(Dialect.by_short_name()["draft3"].uri),
        exit_code=-1,  # because no test cases ran
    ) as send:
        results, stderr = await send("")
    assert "does not support" not in stderr, stderr

    async with run(
        "-i",
        miniatures.only_supports + ",dialect=draft3",
        "--dialect",
        str(Dialect.by_short_name()["draft2020-12"].uri),
        exit_code=EX.CONFIG,
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert re.search(r"does\s+not\s+support", stderr), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_restarts_crashed_implementations(envsonschema):
    async with run("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "a", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "sleep:8", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): ErroredTest.in_errored_case()},
        {tag("envsonschema"): TestResult.INVALID},
        {tag("envsonschema"): ErroredTest.in_errored_case()},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
@pytest.mark.containers
async def test_handles_dead_implementations(succeed_immediately):
    async with run(
        "-i",
        succeed_immediately,
        "-i",
        miniatures.always_invalid,
        exit_code=EX.CONFIG,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {miniatures.always_invalid: TestResult.INVALID},
        {miniatures.always_invalid: TestResult.INVALID},
    ], stderr
    assert "failed to start" in stderr, stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_exits_when_no_implementations_succeed(succeed_immediately):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with run("-i", succeed_immediately, exit_code=EX.CONFIG) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert "failed to start" in stderr, stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_immediately_broken_implementations(fail_immediately):
    async with run(
        "-i",
        fail_immediately,
        "-i",
        miniatures.always_invalid,
        exit_code=EX.CONFIG,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "failed to start" in stderr, stderr
    assert "BOOM!" in stderr, stderr
    assert results == [
        {miniatures.always_invalid: TestResult.INVALID},
        {miniatures.always_invalid: TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_broken_start_implementations(fail_on_start):
    async with run(
        "-i",
        fail_on_start,
        "-i",
        miniatures.always_invalid,
        exit_code=EX.CONFIG,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "failed to start" in stderr, stderr
    assert "BOOM!" in stderr, stderr
    assert results == [
        {miniatures.always_invalid: TestResult.INVALID},
        {miniatures.always_invalid: TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_broken_dialect_implementations(fail_on_dialect):
    async with run(
        "-i",
        fail_on_dialect,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=EX.CONFIG,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert "failed as we were beginning" in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_broken_run_implementations(fail_on_run):
    async with run(
        "-i",
        fail_on_run,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            tag("fail_on_run"): ErroredTest.in_errored_case(),
        },
        {
            tag("fail_on_run"): ErroredTest.in_errored_case(),
        },
    ]
    assert "boom!" in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_invalid_json_run_implementations(nonjson_on_run):
    async with run(
        "-i",
        nonjson_on_run,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            tag("nonjson_on_run"): ErroredTest.in_errored_case(),
        },
    ]
    assert "response=boom!" in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_implementations_can_signal_errors(envsonschema):
    async with run("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "error:", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "4", "schema": {}, "tests": [{"description": "error:message=boom", "instance": {}}] }
            {"description": "works", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): ErroredTest.in_errored_case()},
        {tag("envsonschema"): ErroredTest(context=dict(message="boom"))},
        {tag("envsonschema"): TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_split_messages(envsonschema):
    async with run("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "split:1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}, {"description": "2 valid:0", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.VALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_handles_invalid_start_responses(missing_homepage):
    async with run("-i", missing_homepage, "-V", exit_code=EX.CONFIG) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "failed to start" in stderr, stderr
    assert "'homepage' is a required" in stderr, stderr
    assert results == [], stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_preserves_all_metadata(with_versions):
    async with run("-i", with_versions, "-V") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    # XXX: we need to make run() return the whole report
    assert results == [
        {tag("with_versions"): TestResult.VALID},
    ], stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_it_prevents_network_access(hit_the_network_once):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with run(
        "-i",
        hit_the_network_once,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            tag("hit_the_network_once"): ErroredTest.in_errored_case(),
        },
        {tag("hit_the_network_once"): TestResult.VALID},
    ], stderr
    assert "bad address" in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_wrong_version(wrong_version):
    """
    An implementation speaking the wrong version of the protocol is skipped.
    """
    async with run(
        "-i",
        wrong_version,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=1,  # FIXME: We're emitting the traceback
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [], stderr
    assert "expected to speak version 1 " in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_wrong_seq(wrong_seq):
    """
    Sending the wrong seq for a test case produces an error.
    """
    async with run(
        "-i",
        wrong_seq,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=0,  # FIXME: It'd be nice if this was nonzero.
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            tag("wrong_seq"): ErroredTest.in_errored_case(),
        },
    ], stderr
    assert "mismatched seq " in stderr.lower(), stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_wrong_number_of_tests(wrong_number_of_tests):
    """
    Sending the wrong number of responses for the number of tests in a test
    case produces an error.
    """
    async with run(
        "-i",
        wrong_number_of_tests,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=0,  # FIXME: It'd be nice if this was nonzero.
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            tag("wrong_number_of_tests"): ErroredTest.in_errored_case(),
        },
    ], stderr
    assert "wrong number of responses " in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_fail_fast():
    async with run("-i", "direct:null", "-x") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "2", "instance": 7, "valid": false}] }
            {"description": "3", "schema": {}, "tests": [{"description": "3", "instance": {}, "valid": false}] }
            """,  # noqa: E501
        )

    assert results == [
        {"direct:null": TestResult.VALID},
        {"direct:null": TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_fail_fast_many_tests_at_once():
    async with run("-i", "direct:null", "-x") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": false}, {"description": "valid:1", "instance": {}, "valid": false}, {"description": "valid:1", "instance": {}, "valid": false}] }
            {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": false}] }
            {"description": "3", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {"direct:null": TestResult.VALID},
        {"direct:null": TestResult.VALID},
        {"direct:null": TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_max_fail():
    async with run("-i", "direct:null", "--max-fail", "2") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "2", "instance": 7, "valid": false}] }
            {"description": "3", "schema": {}, "tests": [{"description": "3", "instance": 8, "valid": false}] }
            {"description": "4", "schema": {}, "tests": [{"description": "4", "instance": {}, "valid": false}] }
            """,  # noqa: E501
        )

    assert results == [
        {"direct:null": TestResult.VALID},
        {"direct:null": TestResult.VALID},
        {"direct:null": TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_max_fail_with_fail_fast():
    stdout, stderr = await bowtie(
        "run",
        "-i",
        ARBITRARY,
        "--max-fail",
        "2",
        "--fail-fast",
        exit_code=2,  # comes from click
    )
    assert stdout == ""
    assert "don't provide both" in stderr, stderr

    stdout, stderr = await bowtie(
        "run",
        "-i",
        ARBITRARY,
        "--fail-fast",
        "--max-fail",
        "2",
        exit_code=2,  # comes from click
    )
    assert stdout == ""
    assert "don't provide both" in stderr, stderr


@pytest.mark.asyncio
async def test_filter():
    async with run("-i", "direct:null", "-k", "baz") as send:
        results, stderr = await send(
            """
            {"description": "foo", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "bar", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "baz", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [{"direct:null": TestResult.VALID}], stderr
    assert stderr == ""


class TestSmoke:
    @pytest.mark.asyncio
    @pytest.mark.json
    async def test_full_failure(self):
        jsonout, stderr = await bowtie(
            "smoke",
            "--format",
            "json",
            "-i",
            miniatures.always_wrong,
            json=True,
            exit_code=EX.DATAERR,
        )
        assert (await command_validator("smoke")).validated(jsonout) == {
            "success": False,
            "dialects": {
                "draft2020-12": [
                    {
                        "schema": {
                            "$schema": "https://json-schema.org/draft/2020-12/schema",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [
                                37,
                            ],
                            {
                                "foo": 37,
                            },
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "https://json-schema.org/draft/2020-12/schema",
                            "not": {
                                "$schema": "https://json-schema.org/draft/2020-12/schema",
                            },
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
                "draft2019-09": [
                    {
                        "schema": {
                            "$schema": "https://json-schema.org/draft/2019-09/schema",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "https://json-schema.org/draft/2019-09/schema",
                            "not": {
                                "$schema": "https://json-schema.org/draft/2019-09/schema",
                            },
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
                "draft7": [
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-07/schema#",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-07/schema#",
                            "not": {
                                "$schema": "http://json-schema.org/draft-07/schema#",
                            },
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
                "draft6": [
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-06/schema#",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-06/schema#",
                            "not": {
                                "$schema": "http://json-schema.org/draft-06/schema#",
                            },
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
                "draft4": [
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-04/schema#",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-04/schema#",
                            "not": {
                                "$schema": "http://json-schema.org/draft-04/schema#",
                            },
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
                "draft3": [
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-03/schema#",
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                    },
                    {
                        "schema": {
                            "$schema": "http://json-schema.org/draft-03/schema#",
                            "disallow": [
                                {},
                            ],
                        },
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                    },
                ],
            },
        }, stderr

    @pytest.mark.asyncio
    @pytest.mark.json
    async def test_single_dialect_failure(self):
        jsonout, stderr = await bowtie(
            "smoke",
            "--format",
            "json",
            "-i",
            miniatures.incorrectly_claims_draft7,
            json=True,
            exit_code=EX.DATAERR,
        )
        assert (await command_validator("smoke")).validated(jsonout) == {
            "success": False,
            "dialects": {
                "draft2019-09": [],
                "draft2020-12": [],
                "draft3": [],
                "draft4": [],
                "draft6": [],
                "draft7": [
                    {
                        "expected": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "results": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "schema": {
                            "$schema": "http://json-schema.org/draft-07/schema#",
                        },
                    },
                    {
                        "expected": [
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                            {"valid": False},
                        ],
                        "instances": [
                            None,
                            True,
                            37,
                            37.37,
                            "37",
                            [37],
                            {"foo": 37},
                        ],
                        "results": [
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                            {"valid": True},
                        ],
                        "schema": {
                            "$schema": "http://json-schema.org/draft-07/schema#",
                            "not": {
                                "$schema": "http://json-schema.org/draft-07/schema#",
                            },
                        },
                    },
                ],
            },
        }, stderr

    @pytest.mark.asyncio
    @pytest.mark.json
    async def test_no_registry_support(self):
        jsonout, stderr = await bowtie(
            "smoke",
            "--format",
            "json",
            "-i",
            miniatures.no_registry_support,
            json=True,
        )
        assert (await command_validator("smoke")).validated(jsonout) == {
            "success": True,
            "registry": False,
            "dialects": [
                dialect.short_name
                for dialect in sorted(Dialect.known(), reverse=True)
            ],
        }, stderr

    @pytest.mark.asyncio
    @pytest.mark.json
    async def test_pass(self):
        jsonout, stderr = await bowtie(
            "smoke",
            "--format",
            "json",
            "-i",
            miniatures.passes_smoke,
            json=True,
        )
        assert (await command_validator("smoke")).validated(jsonout) == {
            "success": True,
            "dialects": [
                dialect.short_name
                for dialect in sorted(Dialect.known(), reverse=True)
            ],
        }, stderr

    @pytest.mark.asyncio
    async def test_pretty(self):
        stdout, stderr = await bowtie(
            "smoke",
            "--format",
            "pretty",
            "-i",
            miniatures.always_invalid,
            exit_code=EX.DATAERR,  # because indeed invalid isn't always right
        )

        # FIXME: We don't assert against the exact output yet, as it's a WIP
        assert dedent(stdout), stderr

    @pytest.mark.asyncio
    async def test_markdown(self):
        stdout, stderr = await bowtie(
            "smoke",
            "--format",
            "markdown",
            "-i",
            miniatures.incorrectly_claims_draft7,
            exit_code=EX.DATAERR,  # because indeed it isn't always right
        )
        assert dedent(stdout) == dedent(
            """\
            # incorrectly_claims_draft7 (python)

            Smoke test **failed!**

            ## Dialects

            * Draft 2020-12
            * Draft 2019-09
            * Draft 7 **(failed)**
            * Draft 6
            * Draft 4
            * Draft 3

            ## Failures


            <details>
            <summary>Draft 7</summary>


            ### Schema

            ```json
            {"$schema": "http://json-schema.org/draft-07/schema#"}
            ```

            #### Instances


            * `None`
            * `True`
            * `37`
            * `37.37`
            * `37`
            * `[37]`
            * `{'foo': 37}`

            ### Schema

            ```json
            {"$schema": "http://json-schema.org/draft-07/schema#", "not": {"$schema": "http://json-schema.org/draft-07/schema#"}}
            ```

            #### Instances


            * `None`
            * `True`
            * `37`
            * `37.37`
            * `37`
            * `[37]`
            * `{'foo': 37}`

            </details>
            """,  # noqa: E501
        ), stderr

        # Markdown is very permissive, but let's try parsing it anyhow.
        parsed = MarkdownIt("gfm-like", {"linkify": False}).parse(stdout)
        tokens = SyntaxTreeNode(parsed).pretty(indent=2)
        assert tokens, tokens

    @pytest.mark.asyncio
    async def test_pretty_multiple(self):
        stdout, stderr = await bowtie(
            "smoke",
            "--format",
            "pretty",
            "-i",
            miniatures.always_invalid,
            "-i",
            miniatures.passes_smoke,
            exit_code=EX.DATAERR,  # because indeed invalid isn't always right
        )

        # FIXME: We don't assert against the exact output yet, as it's a WIP
        assert dedent(stdout), stdout

    @pytest.mark.asyncio
    async def test_json_multiple(self):
        jsonout, stderr = await bowtie(
            "smoke",
            "--format",
            "json",
            "-i",
            miniatures.always_invalid,
            "-i",
            miniatures.passes_smoke,
            json=True,
            exit_code=EX.DATAERR,  # because indeed invalid isn't always right
        )
        assert (await command_validator("smoke")).validated(jsonout) == {
            miniatures.passes_smoke: {
                "success": True,
                "dialects": [
                    dialect.short_name
                    for dialect in sorted(Dialect.known(), reverse=True)
                ],
            },
            miniatures.always_invalid: {
                "success": False,
                "dialects": {
                    "draft2019-09": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "https://json-schema.org/draft/2019-09/schema",
                            },
                        },
                    ],
                    "draft2020-12": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "https://json-schema.org/draft/2020-12/schema",
                            },
                        },
                    ],
                    "draft3": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "http://json-schema.org/draft-03/schema#",
                            },
                        },
                    ],
                    "draft4": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "http://json-schema.org/draft-04/schema#",
                            },
                        },
                    ],
                    "draft6": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "http://json-schema.org/draft-06/schema#",
                            },
                        },
                    ],
                    "draft7": [
                        {
                            "expected": [
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                                {"valid": True},
                            ],
                            "instances": [
                                None,
                                True,
                                37,
                                37.37,
                                "37",
                                [37],
                                {"foo": 37},
                            ],
                            "results": [
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                                {"valid": False},
                            ],
                            "schema": {
                                "$schema": "http://json-schema.org/draft-07/schema#",
                            },
                        },
                    ],
                },
            },
        }, stderr

    @pytest.mark.asyncio
    async def test_quiet(self):
        stdout, stderr = await bowtie(
            "smoke",
            "--quiet",
            "-i",
            miniatures.always_invalid,
            exit_code=EX.DATAERR,  # because indeed invalid isn't always right
        )
        assert stdout == "", stderr

    @pytest.mark.asyncio
    async def test_quiet_multiple(self):
        stdout, stderr = await bowtie(
            "smoke",
            "--quiet",
            "-i",
            miniatures.passes_smoke,
            "-i",
            miniatures.always_invalid,
            exit_code=EX.DATAERR,  # one failing implementation fails all
        )
        assert stdout == "", stderr


@pytest.mark.asyncio
async def test_info_pretty():
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "pretty",
        "-i",
        miniatures.fake_language_and_os,
    )
    assert stdout == dedent(
        """\
        ╭────────────────┬─────────────────────────────────────────────────────────────╮
        │ implementation │ fake_language_and_os v1.0.0                                 │
        │ language       │ python 1.2.3                                                │
        │ dialects       │ Draft 2020-12                                               │
        │                │ Draft 2019-09                                               │
        │                │ Draft 7                                                     │
        │                │ Draft 6                                                     │
        │                │ Draft 4                                                     │
        │                │ Draft 3                                                     │
        ├────────────────┼─────────────────────────────────────────────────────────────┤
        │ links          │ homepage https://bowtie.report/                             │
        │                │ source   https://github.com/bowtie-json-schema/bowtie       │
        │                │ issues   https://github.com/bowtie-json-schema/bowtie/iss…  │
        ╰────────────────┴─────────────────────────────────────────────────────────────╯
                                       Ran on Linux 4.5.6                               \n\n
        """,  # noqa: E501
    )
    assert stderr == ""


@pytest.mark.asyncio
async def test_info_markdown():
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "markdown",
        "-i",
        miniatures.always_invalid,
    )
    assert stdout == dedent(
        f"""\
        **name**: "always_invalid"
        **language**: "python"
        **version**: "v1.0.0"
        **homepage**: "https://bowtie.report/"
        **issues**: "https://github.com/bowtie-json-schema/bowtie/issues"
        **language_version**: "{platform.python_version()}"
        **os**: "{platform.system()}"
        **os_version**: "{platform.release()}"
        **source**: "https://github.com/bowtie-json-schema/bowtie"
        **dialects**: [
          "https://json-schema.org/draft/2020-12/schema",
          "https://json-schema.org/draft/2019-09/schema",
          "http://json-schema.org/draft-07/schema#",
          "http://json-schema.org/draft-06/schema#",
          "http://json-schema.org/draft-04/schema#",
          "http://json-schema.org/draft-03/schema#"
        ]
        """,
    )
    assert stderr == ""


@pytest.mark.asyncio
async def test_info_valid_markdown():
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "markdown",
        "-i",
        ARBITRARY,
    )
    parsed_markdown = MarkdownIt("gfm-like", {"linkify": False}).parse(stdout)
    tokens = SyntaxTreeNode(parsed_markdown).pretty(indent=2)
    assert (
        tokens
        == dedent(
            """
            <root>
              <paragraph>
                <inline>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <strong>
                    <text>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
                  <softbreak>
                  <text>
            """,
        ).strip()
    )
    assert stderr == ""


@pytest.mark.asyncio
@pytest.mark.json
async def test_info_json():
    jsonout, stderr = await bowtie(
        "info",
        "--format",
        "json",
        "-i",
        miniatures.always_invalid,
        json=True,
    )

    assert (await command_validator("info")).validated(jsonout) == {
        "name": "always_invalid",
        "language": "python",
        "homepage": "https://bowtie.report/",
        "issues": "https://github.com/bowtie-json-schema/bowtie/issues",
        "source": "https://github.com/bowtie-json-schema/bowtie",
        "language_version": platform.python_version(),
        "os_version": platform.release(),
        "os": platform.system(),
        "version": "v1.0.0",
        "dialects": [
            "https://json-schema.org/draft/2020-12/schema",
            "https://json-schema.org/draft/2019-09/schema",
            "http://json-schema.org/draft-07/schema#",
            "http://json-schema.org/draft-06/schema#",
            "http://json-schema.org/draft-04/schema#",
            "http://json-schema.org/draft-03/schema#",
        ],
    }, stderr
    assert stderr == ""


@pytest.mark.asyncio
@pytest.mark.json
async def test_info_json_multiple_implementations():
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "json",
        "-i",
        miniatures.always_invalid,
        "-i",
        miniatures.links,
    )
    jsonout = _json.loads(stdout)

    assert (await command_validator("info")).validated(jsonout) == {
        miniatures.always_invalid: {
            "name": "always_invalid",
            "language": "python",
            "homepage": "https://bowtie.report/",
            "issues": "https://github.com/bowtie-json-schema/bowtie/issues",
            "source": "https://github.com/bowtie-json-schema/bowtie",
            "language_version": platform.python_version(),
            "os_version": platform.release(),
            "os": platform.system(),
            "version": "v1.0.0",
            "dialects": [
                "https://json-schema.org/draft/2020-12/schema",
                "https://json-schema.org/draft/2019-09/schema",
                "http://json-schema.org/draft-07/schema#",
                "http://json-schema.org/draft-06/schema#",
                "http://json-schema.org/draft-04/schema#",
                "http://json-schema.org/draft-03/schema#",
            ],
        },
        miniatures.links: {
            "name": "links",
            "language": "python",
            "homepage": "urn:example",
            "issues": "urn:example",
            "language_version": platform.python_version(),
            "os_version": platform.release(),
            "os": platform.system(),
            "source": "urn:example",
            "version": "v1.0.0",
            "dialects": ["http://json-schema.org/draft-07/schema#"],
            "links": [
                {"description": "foo", "url": "urn:example:foo"},
                {"description": "bar", "url": "urn:example:bar"},
            ],
        },
    }, stderr
    assert stderr == ""


@pytest.mark.asyncio
async def test_info_pretty_links():
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "pretty",
        "-i",
        miniatures.fake_language_and_os_with_links,
    )
    assert stdout == dedent(
        """\
        ╭────────────────┬─────────────────────────────────────────────────────────────╮
        │ implementation │ fake_language_and_os_with_links v1.0.0                      │
        │ language       │ python 1.2.3                                                │
        │ dialects       │ Draft 2020-12                                               │
        │                │ Draft 7                                                     │
        ├────────────────┼─────────────────────────────────────────────────────────────┤
        │ links          │ homepage https://bowtie.report/                             │
        │                │ source   https://github.com/bowtie-json-schema/bowtie       │
        │                │ issues   https://github.com/bowtie-json-schema/bowtie/iss…  │
        │                │ foo      urn:example:bar                                    │
        │                │ hello    urn:example:world                                  │
        ╰────────────────┴─────────────────────────────────────────────────────────────╯
                                       Ran on Linux 4.5.6                               \n\n
        """,  # noqa: E501
    )
    assert stderr == ""


@pytest.mark.asyncio
@pytest.mark.containers
async def test_info_unsuccessful_start(succeed_immediately):
    stdout, stderr = await bowtie(
        "info",
        "-i",
        succeed_immediately,
        exit_code=EX.CONFIG,
    )

    assert stdout.strip() in {"", "{}"}  # empty, but ignore if JSON or not
    assert "failed to start" in stderr, stderr


@pytest.mark.asyncio
async def test_filter_implementations_no_arguments():
    output, exit_code = pexpect.runu(
        sys.executable,
        args=["-m", "bowtie", "filter-implementations"],
        withexitstatus=True,
    )
    expected = sorted(Implementation.known())
    assert (sorted(output.splitlines()), exit_code) == (expected, 0)


@pytest.mark.asyncio
async def test_filter_implementations_by_language():
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "-i",
        miniatures.fake_javascript,
        "--language",
        "python",
    )
    expected = sorted([miniatures.always_invalid, "direct:null"])
    assert (sorted(stdout.splitlines()), stderr) == (expected, "")


@pytest.mark.asyncio
async def test_filter_implementations_by_dialect():
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "-i",
        miniatures.only_supports + ",dialect=draft3",
        "--supports-dialect",
        "202012",
    )
    expected = sorted([miniatures.always_invalid, "direct:null"])
    assert (sorted(stdout.splitlines()), stderr) == (expected, "")


@pytest.mark.asyncio
async def test_filter_implementations_both_language_and_dialect():
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "-i",
        miniatures.fake_javascript,
        "-l",
        "javascript",
        "-d",
        "7",
    )
    assert (stdout, stderr) == (f"{miniatures.fake_javascript}\n", "")


@pytest.mark.asyncio
async def test_filter_implementations_direct():
    output, exit_code = pexpect.runu(
        sys.executable,
        args=["-m", "bowtie", "filter-implementations", "--direct"],
        withexitstatus=True,
    )
    expected = sorted(KNOWN_DIRECT)
    assert (sorted(output.splitlines()), exit_code) == (expected, 0)


@pytest.mark.asyncio
async def test_filter_implementations_direct_by_language():
    output, exit_code = pexpect.runu(
        sys.executable,
        args=[
            "-m",
            "bowtie",
            "filter-implementations",
            "--direct",
            "--language",
            "python",
        ],
        withexitstatus=True,
    )
    expected = sorted(d for d in KNOWN_DIRECT if d.startswith("python-"))
    assert (sorted(output.splitlines()), exit_code) == (expected, 0)


@pytest.mark.asyncio
async def test_filter_implementations_direct_additional_unknown():
    stdout, stderr = await bowtie(
        "filter-implementations",
        "--direct",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
    )
    expected = sorted([miniatures.always_invalid, "direct:null"])
    assert (sorted(stdout.splitlines()), stderr) == (expected, "")


@pytest.mark.asyncio
async def test_filter_implementations_direct_by_language_with_unknown():
    stdout, stderr = await bowtie(
        "filter-implementations",
        "--direct",
        "-i",
        "direct:null",
        "-i",
        miniatures.fake_javascript,
        "--language",
        "python",
    )
    expected = ["direct:null"]
    assert (sorted(stdout.splitlines()), stderr) == (expected, "")


@pytest.mark.asyncio
async def test_filter_implementations_stdin():
    lines = dedent(
        f"""\
        {"direct:null"}
        {miniatures.always_invalid}
        {miniatures.fake_javascript}
        """.rstrip(),
    )
    stdout, stderr = await bowtie(
        "filter-implementations",
        "--language",
        "javascript",
        stdin=lines + "\n",
    )
    assert (stdout, stderr) == (f"{miniatures.fake_javascript}\n", "")


@pytest.mark.asyncio
@pytest.mark.json
async def test_filter_implementations_json():
    jsonout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "-i",
        miniatures.fake_javascript,
        "-l",
        "javascript",
        "-d",
        "7",
        "--format",
        "json",
        json=True,
    )
    assert (await command_validator("filter-implementations")).validated(
        jsonout,
    ) == [miniatures.fake_javascript]
    assert stderr == ""


@pytest.mark.asyncio
async def test_filter_dialects():
    stdout, stderr = await bowtie("filter-dialects")
    dialects_supported = "\n".join(
        [
            str(dialect.uri)
            for dialect in sorted(Dialect.known(), reverse=True)
        ],
    )
    assert (stdout.strip(), stderr) == (f"{dialects_supported}", "")


@pytest.mark.asyncio
async def test_filter_dialects_latest_dialect():
    stdout, stderr = await bowtie(
        "filter-dialects",
        "-l",
    )
    assert (stdout, stderr) == (f"{Dialect.latest().uri}\n", "")


@pytest.mark.asyncio
async def test_filter_dialects_supporting_implementation():
    output = await bowtie(
        "filter-dialects",
        "-i",
        miniatures.only_supports + ",dialect=draft3",
    )
    assert output == ("http://json-schema.org/draft-03/schema#\n", "")


@pytest.mark.asyncio
async def test_filter_dialects_boolean_schemas():
    stdout, stderr = await bowtie("filter-dialects", "-b")
    boolean_schemas = "\n".join(
        [
            str(dialect.uri)
            for dialect in sorted(Dialect.known(), reverse=True)
            if dialect.has_boolean_schemas
        ],
    )
    assert (stdout.strip(), stderr) == (f"{boolean_schemas}", "")


@pytest.mark.asyncio
async def test_filter_dialects_non_boolean_schemas():
    stdout, stderr = await bowtie("filter-dialects", "-B")
    non_boolean_schemas = "\n".join(
        [
            str(dialect.uri)
            for dialect in sorted(Dialect.known(), reverse=True)
            if not dialect.has_boolean_schemas
        ],
    )
    assert (stdout.strip(), stderr) == (f"{non_boolean_schemas}", "")


@pytest.mark.asyncio
async def test_filter_dialects_no_results():
    stdout, stderr = await bowtie(
        "filter-dialects",
        "-i",
        miniatures.only_supports + ",dialect=draft3",
        "--boolean-schemas",
        exit_code=EX.DATAERR,
    )
    assert (stdout.strip(), stderr) == ("", "No dialects match.\n")


@pytest.mark.asyncio
async def test_validate(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("a.json").write_text("12")
    tmp_path.joinpath("b.json").write_text('"foo"')

    stdout, _ = await bowtie(
        "validate",
        "-i",
        "direct:null",
        tmp_path / "schema.json",
        tmp_path / "a.json",
        tmp_path / "b.json",
        exit_code=0,
    )
    assert stdout != ""  # the real assertion here is we succeed above


@pytest.mark.asyncio
@pytest.mark.json
async def test_summary_show_failures_json(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    jsonout, stderr = await bowtie(
        "summary",
        "--format",
        "json",
        "--show",
        "failures",
        stdin=validate_stdout,
        json=True,
        exit_code=EX.DATAERR,
    )

    assert (await command_validator("summary")).validated(jsonout) == [
        [
            "direct:null",
            dict(failed=0, skipped=0, errored=0),
        ],
        [
            miniatures.always_invalid,
            dict(failed=2, skipped=0, errored=0),
        ],
    ]
    assert stderr == ""


@pytest.mark.asyncio
async def test_summary_show_failures_markdown(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        "direct:null",
        "-i",
        miniatures.always_invalid,
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    stdout, stderr = await bowtie(
        "summary",
        "--format",
        "markdown",
        "--show",
        "failures",
        stdin=validate_stdout,
        exit_code=EX.DATAERR,
    )
    assert stderr == ""
    assert stdout == dedent(
        """\
        # Bowtie Failures Summary

        | Implementation | Skips | Errors | Failures |
        |:-----------------------:|:-:|:-:|:-:|
        |      null (python)      | 0 | 0 | 0 |
        | always_invalid (python) | 0 | 0 | 2 |

        **2 tests ran**
        """,
    )


@pytest.mark.asyncio
async def test_summary_show_failures_markdown_different_versions(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        "direct:null",
        "-i",
        miniatures.has_bugs_by_versions + ",version=1.0",
        "-i",
        miniatures.has_bugs_by_versions + ",version=2.0",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    stdout, stderr = await bowtie(
        "summary",
        "--format",
        "markdown",
        "--show",
        "failures",
        stdin=validate_stdout,
        exit_code=EX.DATAERR,
    )
    assert stderr == ""
    assert stdout in {
        dedent(
            """\
            # Bowtie Failures Summary

            | Implementation | Skips | Errors | Failures |
            |:------------------:|:-:|:-:|:-:|
            | buggy 2.0 (python) | 0 | 0 | 0 |
            |   null (python)    | 0 | 0 | 0 |
            | buggy 1.0 (python) | 0 | 0 | 2 |

            **2 tests ran**
            """,
        ),
        dedent(
            """\
            # Bowtie Failures Summary

            | Implementation | Skips | Errors | Failures |
            |:------------------:|:-:|:-:|:-:|
            |   null (python)    | 0 | 0 | 0 |
            | buggy 2.0 (python) | 0 | 0 | 0 |
            | buggy 1.0 (python) | 0 | 0 | 2 |

            **2 tests ran**
            """,
        ),
    }


@pytest.mark.asyncio
async def test_summary_failures_valid_markdown(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        ARBITRARY,
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    stdout, stderr = await bowtie(
        "summary",
        "--format",
        "markdown",
        "--show",
        "failures",
        stdin=validate_stdout,
        exit_code=EX.DATAERR,
    )
    parsed_markdown = MarkdownIt("gfm-like", {"linkify": False}).parse(stdout)
    tokens = SyntaxTreeNode(parsed_markdown).pretty(indent=2)
    assert stderr == ""
    assert (
        tokens
        == (
            """
        <root>
  <heading>
    <inline>
      <text>
  <table>
    <thead>
      <tr>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
    <tbody>
      <tr>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
  <paragraph>
    <inline>
      <text>
      <strong>
        <text>
      <text>
        """
        ).strip()
    )


@pytest.mark.asyncio
async def test_validate_no_tests(tmp_path):
    """
    Don't bother starting up if we have nothing to run.
    """
    schema = tmp_path / "schema.json"
    schema.write_text("{}")
    stdout, stderr = await bowtie(
        "validate",
        "-i",
        ARBITRARY,
        schema,
        exit_code=EX.NOINPUT,
    )
    assert stdout == ""
    assert stderr == ""


@pytest.mark.asyncio
@pytest.mark.containers
@pytest.mark.json
async def test_summary_show_validation_json(envsonschema):
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    run_stdout, run_stderr = await bowtie(
        "run",
        "-i",
        envsonschema,
        "-i",
        "direct:null",
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    jsonout, stderr = await bowtie(
        "summary",
        "--format",
        "json",
        "--show",
        "validation",
        stdin=run_stdout,
        json=True,
    )

    assert (await command_validator("summary")).validated(jsonout) == [
        [
            {"type": "integer"},
            [
                [
                    12,
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "valid",
                    },
                ],
                [
                    12.5,
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "invalid",
                    },
                ],
            ],
        ],
        [
            {"type": "string"},
            [
                [
                    "{}",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "error",
                    },
                ],
            ],
        ],
        [
            {"type": "number"},
            [
                [
                    "{}",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "error",
                    },
                ],
                [
                    37,
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "error",
                    },
                ],
            ],
        ],
        [
            {"type": "array"},
            [
                [
                    "",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "skipped",
                    },
                ],
            ],
        ],
        [
            {"type": "boolean"},
            [
                [
                    "",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "skipped",
                    },
                ],
            ],
        ],
        [
            {"type": "array"},
            [
                [
                    "",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "error",
                    },
                ],
                [
                    12,
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "invalid",
                    },
                ],
            ],
        ],
        [
            {"type": "array"},
            [
                [
                    "",
                    {
                        "direct:null": "valid",
                        tag("envsonschema"): "error",
                    },
                ],
            ],
        ],
    ], run_stderr
    assert stderr == ""


@pytest.mark.asyncio
@pytest.mark.containers
async def test_badges(envsonschema, tmp_path):
    site = tmp_path / "site"
    site.mkdir()

    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501

    run_stdout, _ = await bowtie(
        "run",
        "-i",
        envsonschema,
        stdin=dedent(raw.strip("\n")),
    )

    site.joinpath("draft2020-12.json").write_text(run_stdout)

    stdout, stderr = await bowtie("badges", "--site", site)

    badges = site / "badges"
    assert {path.relative_to(badges) for path in badges.rglob("*")} == {
        Path("python-envsonschema"),
        Path("python-envsonschema/supported_versions.json"),
        Path("python-envsonschema/compliance"),
        Path("python-envsonschema/compliance/draft2020-12.json"),
    }


@pytest.mark.asyncio
async def test_badges_nothing_ran(tmp_path):
    run_stdout, _ = await bowtie(
        "run",
        "-i",
        ARBITRARY,
        stdin="",
        exit_code=-1,  # no test cases run causes a non-zero here
    )

    badges = tmp_path / "badges"
    stdout, stderr = await bowtie(
        "badges",
        badges,
        stdin=run_stdout,
        exit_code=2,  # comes from click
    )
    assert stdout == ""
    assert stderr != ""
    assert not badges.is_dir()


@pytest.mark.asyncio
@pytest.mark.containers
async def test_no_such_image(tmp_path):
    stdout, stderr = await bowtie(
        "run",
        "-i",
        "no-such-image",
        exit_code=EX.CONFIG,
    )
    assert stdout == ""
    assert (
        "'ghcr.io/bowtie-json-schema/no-such-image' is not a known " in stderr
    ), stderr

    stdout, stderr = await bowtie(
        "smoke",
        "-i",
        "no-such-image",
        exit_code=EX.CONFIG,
    )
    assert "/no-such-image' is not a known" in stderr, stderr

    foo = tmp_path / "foo.json"
    foo.write_text("{}")

    stdout, stderr = await bowtie(
        "validate",
        "-i",
        "no-such-image",
        "-",
        foo,
        stdin="{}",
        exit_code=EX.CONFIG,
    )
    assert stdout == ""
    assert (
        "'ghcr.io/bowtie-json-schema/no-such-image' is not a known " in stderr
    ), stderr


@pytest.mark.asyncio
async def test_suite_not_a_suite_directory(tmp_path):
    _, stderr = await bowtie(
        "suite",
        "-i",
        ARBITRARY,
        tmp_path,
        exit_code=2,  # comes from click
    )
    assert "does not contain" in stderr, stderr


@pytest.mark.asyncio
async def test_trend_no_id_directory(tmp_path):
    tar_path = tmp_path / "versioned-reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(),
        versioned_reports=[],
    )

    _, stderr = await bowtie(
        "trend",
        "-i",
        "foo",
        tar_path,
        exit_code=EX.DATAERR,
    )

    assert "Couldn't find a 'foo' directory" in stderr, stderr


@pytest.mark.asyncio
async def test_trend_no_versions_detected(tmp_path):
    tar_path = tmp_path / "versioned-reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(),
        versioned_reports=[],
    )

    _, stderr = await bowtie(
        "trend",
        "-i",
        "buggy",
        tar_path,
        exit_code=EX.DATAERR,
    )

    assert "No versions detected" in stderr, stderr


@pytest.mark.asyncio
async def test_trend_no_versions_subdirs(tmp_path):
    tar_path = tmp_path / "versioned-reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(["1.0", "2.0"]),
        versioned_reports=[],
    )

    _, stderr = await bowtie(
        "trend",
        "-i",
        "buggy",
        tar_path,
        exit_code=EX.DATAERR,
    )

    assert "Couldn't find any versions sub-directories" in stderr, stderr


@pytest.mark.asyncio
async def test_trend_no_versions_support(tmp_path):
    tar_path = tmp_path / "versioned-reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(["1.0", "2.0"]),
        versioned_reports=[
            ("1.0", Dialect.by_alias()["2020"], "report_placeholder"),
        ],
    )

    stdout, _ = await bowtie(
        "trend",
        "-i",
        "buggy",
        "--dialect",
        "7",
        tar_path,
    )

    assert stdout.strip() == "None of the versions of 'buggy' support Draft 7."


@pytest.mark.asyncio
async def test_trend_json(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    buggy_v1_2020_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=1.0",
        "--dialect",
        "https://json-schema.org/draft/2020-12/schema",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )
    buggy_v1_2019_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=1.0",
        "-D",
        "https://json-schema.org/draft/2019-09/schema",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    buggy_v2_2020_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=2.0",
        "--dialect",
        "2020",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )
    buggy_v2_2019_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=2.0",
        "-D",
        "2019",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    tar_path = tmp_path / "versioned_reports.tar"
    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(["1.0", "2.0"]),
        versioned_reports=[
            (
                "1.0",
                Dialect.by_short_name()["draft2020-12"],
                buggy_v1_2020_stdout,
            ),
            (
                "1.0",
                Dialect.by_short_name()["draft2019-09"],
                buggy_v1_2019_stdout,
            ),
            (
                "2.0",
                Dialect.by_alias()["2020"],
                buggy_v2_2020_stdout,
            ),
            (
                "2.0",
                Dialect.by_alias()["2019"],
                buggy_v2_2019_stdout,
            ),
        ],
    )

    jsonout, stderr = await bowtie(
        "trend",
        "-i",
        "buggy",
        tar_path,
        "--format",
        "json",
        json=True,
    )

    assert (await command_validator("trend")).validated(jsonout) == [
        [
            "buggy",
            [
                [
                    "draft2020-12",
                    [
                        [
                            "2.0",
                            {
                                "failed": 0,
                                "errored": 0,
                                "skipped": 0,
                            },
                        ],
                        [
                            "1.0",
                            {
                                "failed": 2,
                                "errored": 0,
                                "skipped": 0,
                            },
                        ],
                    ],
                ],
                [
                    "draft2019-09",
                    [
                        [
                            "2.0",
                            {
                                "failed": 2,
                                "errored": 0,
                                "skipped": 0,
                            },
                        ],
                        [
                            "1.0",
                            {
                                "failed": 0,
                                "errored": 0,
                                "skipped": 0,
                            },
                        ],
                    ],
                ],
            ],
        ],
    ]
    assert stderr == ""


@pytest.mark.asyncio
async def test_trend_markdown(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    buggy_v1_2020_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=1.0",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    buggy_v2_2020_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=2.0",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    tar_path = tmp_path / "versioned_reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(["1.0", "2.0"]),
        versioned_reports=[
            ("1.0", Dialect.by_alias()["2020"], buggy_v1_2020_stdout),
            ("2.0", Dialect.by_alias()["2020"], buggy_v2_2020_stdout),
        ],
    )

    stdout, stderr = await bowtie(
        "trend",
        "-i",
        "buggy",
        tar_path,
        "--format",
        "markdown",
    )

    assert stderr == ""
    assert stdout == dedent(
        """
        ## Trend Data of buggy versions:

        ### Dialect: Draft 2020-12

        | Version | Skips | Errors | Failures |
        |:---:|:-:|:-:|:-:|
        | 2.0 | 0 | 0 | 0 |
        | 1.0 | 0 | 0 | 2 |

        **2 tests ran**
        """,
    )


@pytest.mark.asyncio
async def test_trend_valid_markdown(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    buggy_v1_2019_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=1.0",
        "--dialect",
        "201909",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    buggy_v2_2019_stdout, _ = await bowtie(
        "validate",
        "-i",
        miniatures.has_bugs_by_versions + ",version=2.0",
        "-D",
        "draft201909",
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    tar_path = tmp_path / "versioned_reports.tar"

    tar_from_versioned_reports(
        tar_path=tar_path,
        id="buggy",
        versions=frozenset(["1.0", "2.0"]),
        versioned_reports=[
            (
                "1.0",
                Dialect.by_short_name()["draft2019-09"],
                buggy_v1_2019_stdout,
            ),
            (
                "2.0",
                Dialect.by_short_name()["draft2019-09"],
                buggy_v2_2019_stdout,
            ),
        ],
    )

    stdout, stderr = await bowtie(
        "trend",
        "-i",
        "buggy",
        "-D",
        "2019-09",
        tar_path,
        "--format",
        "markdown",
    )
    parsed_markdown = MarkdownIt("gfm-like", {"linkify": False}).parse(stdout)
    tokens = SyntaxTreeNode(parsed_markdown).pretty(indent=2)

    assert stderr == ""
    assert (
        tokens
        == (
            """
        <root>
  <heading>
    <inline>
      <text>
  <heading>
    <inline>
      <text>
  <table>
    <thead>
      <tr>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
        <th style='text-align:center'>
          <inline>
            <text>
    <tbody>
      <tr>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
      <tr>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
        <td style='text-align:center'>
          <inline>
            <text>
  <paragraph>
    <inline>
      <text>
      <strong>
        <text>
      <text>
            """
        ).strip()
    )


@pytest.mark.asyncio
async def test_validate_mismatched_dialect(tmp_path):
    tmp_path.joinpath("schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2020-12/schema"}',
    )
    tmp_path.joinpath("instance.json").write_text("12")

    stdout, stderr = await bowtie(
        "validate",
        "-D",
        "7",
        "-i",
        ARBITRARY,
        tmp_path / "schema.json",
        tmp_path / "instance.json",
    )
    dialect = _json.loads(stdout.split("\n")[0])["dialect"]

    assert dialect == "http://json-schema.org/draft-07/schema#"
    assert "$schema keyword does not" in stderr, stderr


@pytest.mark.asyncio
async def test_run_mismatched_dialect():
    async with run("-i", miniatures.always_invalid, "-D", "2019") as send:
        results, stderr = await send(
            """
            {"description": "wrong dialect", "schema": {"$schema": "https://json-schema.org/draft/2020-12/schema"}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [{miniatures.always_invalid: TestResult.INVALID}], stderr
    assert "$schema keyword does not" in stderr, stderr


@pytest.mark.asyncio
async def test_run_registry_metasschema_not_mismatched_dialect():
    async with run("-i", miniatures.always_invalid, "-D", "2019") as send:
        results, stderr = await send(
            """
            {"description": "wrong dialect", "schema": {"$schema": "urn:metaschema"}, "registry": {"urn:metaschema": {"$schema": "https://json-schema.org/draft/2019-09/schema"}}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [{miniatures.always_invalid: TestResult.INVALID}], stderr
    assert stderr == ""


@pytest.mark.asyncio
async def test_run_registry_metasschema_still_mismatched_dialect():
    async with run("-i", miniatures.always_invalid, "-D", "2019") as send:
        results, stderr = await send(
            """
            {"description": "wrong dialect", "schema": {"$schema": "urn:metaschema"}, "registry": {"urn:metaschema": {"$schema": "https://json-schema.org/draft/2020-12/schema"}}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [{miniatures.always_invalid: TestResult.INVALID}], stderr
    assert "$schema keyword does not" in stderr, stderr


@pytest.mark.asyncio
async def test_run_mismatched_dialect_total_junk():
    """
    A $schema keyword that isn't even a string just gets ignored.

    At this point we're likely testing completely broken schemas.
    """
    async with run("-i", miniatures.always_invalid, "-D", "2019") as send:
        results, stderr = await send(
            """
            {"description": "BOOM", "schema": {"$schema": 37}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [{miniatures.always_invalid: TestResult.INVALID}], stderr
    assert stderr == ""


@pytest.mark.asyncio
async def test_validate_boolean_schema(tmp_path):
    tmp_path.joinpath("schema.json").write_text("false")
    tmp_path.joinpath("instance.json").write_text("12")

    _, stderr = await bowtie(
        "validate",
        "-i",
        ARBITRARY,
        tmp_path / "schema.json",
        tmp_path / "instance.json",
    )

    assert stderr == "", stderr


@pytest.mark.asyncio
async def test_run_boolean_schema(tmp_path):
    async with run("-i", miniatures.always_invalid) as send:
        results, stderr = await send(
            """
            {"description": "wrong dialect", "schema": false, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [{miniatures.always_invalid: TestResult.INVALID}], stderr
    assert stderr == "", stderr


@pytest.mark.asyncio
async def test_validate_set_dialect_from_schema(tmp_path):
    tmp_path.joinpath("schema.json").write_text(
        '{"$schema": "https://json-schema.org/draft/2019-09/schema"}',
    )
    tmp_path.joinpath("instance.json").write_text("12")

    stdout, stderr = await bowtie(
        "validate",
        "-i",
        ARBITRARY,
        tmp_path / "schema.json",
        tmp_path / "instance.json",
    )
    report = Report.from_serialized(stdout.splitlines())
    assert report.metadata.dialect == Dialect.by_short_name()["draft2019-09"]


@pytest.mark.asyncio
async def test_validate_specify_dialect(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("instance.json").write_text("12")

    stdout, stderr = await bowtie(
        "validate",
        "-i",
        ARBITRARY,
        "-D",
        "2019",
        tmp_path / "schema.json",
        tmp_path / "instance.json",
    )
    report = Report.from_serialized(stdout.splitlines())
    assert report.metadata.dialect == Dialect.by_short_name()["draft2019-09"]


@pytest.mark.asyncio
@pytest.mark.containers
async def test_statistics_pretty(envsonschema):
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    run_stdout, run_stderr = await bowtie(
        "run",
        "-i",
        envsonschema,
        "-i",
        "direct:null",
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    stdout, stderr = await bowtie(
        "statistics",
        "--format",
        "pretty",
        stdin=run_stdout,
    )

    prefix = "Ran on: "
    ran_on_lines = [
        line.removeprefix(prefix)
        for line in stdout.splitlines()
        if line.startswith(prefix)
    ]
    assert len(ran_on_lines) == 1, ("Couldn't find run date", stdout, stderr)
    ran_on = default_tzinfo(parse_datetime(ran_on_lines[0]), tzlocal())

    now, delta = datetime.now(tzlocal()), timedelta(minutes=1)
    assert within_delta(ran_on, now, delta), f"{ran_on} is too far from {now}."

    assert stdout == dedent(
        f"""\
        Dialect: Draft 2020-12
        {prefix}{ran_on_lines[0]}

        median: 0.65
        mean: 0.65
        """,
    )
    assert stderr == "", stderr


@pytest.mark.asyncio
@pytest.mark.containers
@pytest.mark.json
async def test_statistics_json(envsonschema):
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    run_stdout, run_stderr = await bowtie(
        "run",
        "-i",
        envsonschema,
        "-i",
        "direct:null",
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    jsonout, stderr = await bowtie(
        "statistics",
        "--format",
        "json",
        stdin=run_stdout,
        json=True,
    )

    ran_on = isoparse(jsonout["ran_on"])
    now, delta = datetime.now(tzlocal()), timedelta(minutes=1)
    assert within_delta(ran_on, now, delta), f"{ran_on} is too far from {now}."

    assert (await command_validator("statistics")).validated(jsonout) == dict(
        dialect="https://json-schema.org/draft/2020-12/schema",
        ran_on=jsonout["ran_on"],
        median=0.65,
        mean=0.65,
    )
    assert stderr == "", stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_statistics_markdown(envsonschema):
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    run_stdout, run_stderr = await bowtie(
        "run",
        "-i",
        envsonschema,
        "-i",
        "direct:null",
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    stdout, stderr = await bowtie(
        "statistics",
        "--format",
        "markdown",
        stdin=run_stdout,
    )

    prefix = "### Ran on:"

    ran_on_lines = [
        line.removeprefix(prefix)
        for line in stdout.splitlines()
        if line.startswith(prefix)
    ]
    assert len(ran_on_lines) == 1, ("Couldn't find run date", stdout, stderr)
    ran_on = default_tzinfo(parse_datetime(ran_on_lines[0]), tzlocal())

    now, delta = datetime.now(tzlocal()), timedelta(minutes=1)
    assert within_delta(ran_on, now, delta), f"{ran_on} is too far from {now}."

    assert stdout == dedent(
        f"""\
        ## Dialect: Draft 2020-12

        {prefix}{ran_on_lines[0]}

        | Metric | Value |
        |:------:|:----:|
        | median | 0.65 |
        |  mean  | 0.65 |
        """,
    )
    assert stderr == "", stderr


@pytest.mark.asyncio
@pytest.mark.containers
async def test_container_connectables(
    lintsonschema_container,
    envsonschema_container,
    tmp_path,
):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("instance.json").write_text("12")

    stdout, stderr = await bowtie(
        "validate",
        "-i",
        lintsonschema_container,
        "-i",
        envsonschema_container,
        tmp_path / "schema.json",
        tmp_path / "instance.json",
        exit_code=0,
    )
    assert stderr == ""

    report = Report.from_serialized(stdout.splitlines())
    assert [
        [test_results for _, test_results in results]
        for _, results in report.cases_with_results()
    ] == [
        [
            {
                envsonschema_container: TestResult.INVALID,
                lintsonschema_container: TestResult.VALID,
            },
        ],
    ], stderr


@pytest.mark.asyncio
async def test_direct_connectable_python_jsonschema(tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("instance.json").write_text("12")

    stdout, stderr = await bowtie(
        "validate",
        "-i",
        "direct:python-jsonschema",
        tmp_path / "schema.json",
        tmp_path / "instance.json",
        exit_code=0,
    )
    assert stderr == ""

    report = Report.from_serialized(stdout.splitlines())
    assert [
        [test_results for _, test_results in results]
        for _, results in report.cases_with_results()
    ] == [
        [{"direct:python-jsonschema": TestResult.VALID}],
    ], stderr


@pytest.mark.parametrize("id", KNOWN_DIRECT.keys())
@pytest.mark.asyncio
async def test_smoke_direct_connectables(id):
    """
    All direct connectables pass their smoke test.
    """
    await bowtie("smoke", "-i", f"direct:{id}", exit_code=0)


class TestImplicitDialectSupport:
    @pytest.mark.asyncio
    async def test_dialectless_schema_with_no_such_support(self, tmp_path):
        """
        Sending a schema with no explicit dialect warns once if the
        implementation does not support implicit dialect requests.
        """
        tmp_path.joinpath("schema.json").write_text("{}")
        tmp_path.joinpath("instance.json").write_text("12")
        stdout, stderr = await bowtie(
            "validate",
            "-i",
            miniatures.no_implicit_dialect_support,
            tmp_path / "schema.json",
            tmp_path / "instance.json",
        )

        assert not Report.from_serialized(stdout.splitlines()).is_empty
        assert "does not indicate its dialect" in stderr

    @pytest.mark.asyncio
    async def test_dialectless_schema_with_support(self, tmp_path):
        """
        Sending a schema with no explicit dialect does not warn if the
        implementation supports implicit dialect requests.
        """
        tmp_path.joinpath("schema.json").write_text("{}")
        tmp_path.joinpath("instance.json").write_text("12")
        stdout, stderr = await bowtie(
            "validate",
            "-i",
            ARBITRARY,
            tmp_path / "schema.json",
            tmp_path / "instance.json",
        )

        assert not Report.from_serialized(stdout.splitlines()).is_empty
        assert stderr == ""

    @pytest.mark.asyncio
    async def test_schema_with_dialect(self, tmp_path):
        """
        Sending a schema with an explicit dialect does not warn even if the
        implementation does not support implicit dialect requests.
        """
        tmp_path.joinpath("schema.json").write_text(
            '{"$schema": "https://json-schema.org/draft/2020-12/schema"}',
        )
        tmp_path.joinpath("instance.json").write_text("12")
        stdout, stderr = await bowtie(
            "validate",
            "-i",
            miniatures.no_implicit_dialect_support,
            tmp_path / "schema.json",
            tmp_path / "instance.json",
        )
        assert not Report.from_serialized(stdout.splitlines()).is_empty
        assert stderr == ""


class TestBenchmarkRun:

    DIRECT_CONNECTABLE_PYTHON = "direct:python-jsonschema"

    benchmark_report_validator = VALIDATORS.for_uri(
        "tag:bowtie.report,2024:benchmark_report",
    )

    @pytest.fixture
    def valid_single_benchmark(self):
        from bowtie.tests.benchmarks import valid_single_benchmark

        return valid_single_benchmark.get_benchmark()

    @pytest.fixture
    def invalid_benchmark(self):
        from bowtie.tests.benchmarks import invalid_benchmark

        return invalid_benchmark.get_benchmark()

    @pytest.mark.asyncio
    async def test_nonexistent_benchmark_run(self):
        random_name = "non-existent-benchmark.py"
        _, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-b",
            random_name,
            exit_code=EX.DATAERR,
        )
        assert "Benchmark File not found" in stderr

    @pytest.mark.asyncio
    async def test_benchmark_run_json_output(
        self,
        valid_single_benchmark,
        tmp_path,
    ):
        tmp_path.joinpath("benchmark.json").write_text(
            _json.dumps(valid_single_benchmark.serializable()),
        )
        stdout, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-q",
            "--format",
            "json",
            tmp_path / "benchmark.json",
            exit_code=0,
            json=True,
        )
        self.benchmark_report_validator.validated(stdout)

    @pytest.mark.asyncio
    async def test_benchmark_run_pretty_output(
        self,
        valid_single_benchmark,
        tmp_path,
    ):
        tmp_path.joinpath("benchmark.json").write_text(
            _json.dumps(valid_single_benchmark.serializable()),
        )
        stdout, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-q",
            "--format",
            "pretty",
            tmp_path / "benchmark.json",
            exit_code=0,
        )

        # FIXME: We don't assert against the exact output yet, as it's a WIP
        assert stdout, stderr

    @pytest.mark.asyncio
    async def test_benchmark_run_markdown_output(
        self,
        valid_single_benchmark,
        tmp_path,
    ):
        tmp_path.joinpath("benchmark.json").write_text(
            _json.dumps(valid_single_benchmark.serializable()),
        )
        stdout, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-q",
            "--format",
            "markdown",
            tmp_path / "benchmark.json",
            exit_code=0,
        )

        expected_data1 = dedent(
            """
            # Benchmark Summary
            ## Benchmark Group: benchmark
            Benchmark File: None


            Benchmark: Tests with benchmark

            | Test Name | direct:python-jsonschema |
        """,
        ).strip()

        expected_data2 = dedent(
            """
            ## Benchmark Metadata

            Runs: 3
            Values: 2
            Warmups: 1
        """,
        ).strip()

        # Cant verify the whole output as it would be dynamic
        # with differing values
        assert expected_data1 in stdout
        assert expected_data2 in stdout

    @pytest.mark.asyncio
    async def test_benchmark_run_varying_param_markdown(
        self,
        tmp_path,
    ):
        from bowtie.tests.benchmarks import benchmark_with_varying_parameter

        tmp_path.joinpath("benchmark.json").write_text(
            _json.dumps(
                benchmark_with_varying_parameter.get_benchmark().serializable(),
            ),
        )
        stdout, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-q",
            "--format",
            "markdown",
            tmp_path / "benchmark.json",
            exit_code=0,
        )

        expected_data1 = dedent(
            """
            # Benchmark Summary
            ## Benchmark Group: benchmark
            Benchmark File: None

            Benchmark: Tests with varying Array Size

            | Test Name | direct:python-jsonschema |
        """,
        ).strip()

        expected_data2 = dedent(
            """
            Benchmark: Tests with benchmark 2

            | Test Name | direct:python-jsonschema |
        """,
        ).strip()

        expected_data3 = dedent(
            """
            ## Benchmark Metadata

            Runs: 3
            Values: 2
            Warmups: 1
        """,
        ).strip()

        # Cant verify the whole output as it would be dynamic
        # with differing values
        assert expected_data1 in stdout
        assert expected_data2 in stdout
        assert expected_data3 in stdout

    @pytest.mark.asyncio
    async def test_invalid_benchmark_run(self, invalid_benchmark, tmp_path):
        tmp_path.joinpath("benchmark.json").write_text(
            _json.dumps(invalid_benchmark),
        )
        _, stderr = await bowtie(
            "perf",
            "-i",
            self.DIRECT_CONNECTABLE_PYTHON,
            "-q",
            "--format",
            "json",
            tmp_path / "benchmark.json",
            exit_code=1,
        )


class TestFilterBenchmarks:

    @pytest.mark.asyncio
    async def test_default_benchmarks(self):
        stdout, stderr = await bowtie(
            "filter-benchmarks",
            exit_code=0,
        )
        assert stderr == ""

    @pytest.mark.asyncio
    async def test_keyword_benchmarks(self):
        stdout, stderr = await bowtie(
            "filter-benchmarks",
            "-t",
            "keyword",
            exit_code=0,
        )
        assert stderr == ""

    @pytest.mark.asyncio
    async def test_filtering_by_name(self):
        stdout, stderr = await bowtie(
            "filter-benchmarks",
            "-t",
            "keyword",
            "-n",
            "random-nonexistent-name",
            exit_code=0,
        )
        assert stdout == ""
        assert stderr == ""
