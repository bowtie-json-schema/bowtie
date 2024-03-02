from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from pprint import pformat
from textwrap import dedent, indent
import asyncio
import json as _json
import os
import re
import sys
import tarfile

from aiodocker.exceptions import DockerError
import pytest
import pytest_asyncio

from bowtie._commands import ErroredTest, TestResult
from bowtie._core import Dialect, Test, TestCase
from bowtie._report import EmptyReport, InvalidReport, Report

Test.__test__ = TestCase.__test__ = TestResult.__test__ = (
    False  # frigging py.test
)


HERE = Path(__file__).parent
FAUXMPLEMENTATIONS = HERE / "fauxmplementations"


def tag(name: str):
    return f"bowtie-integration-tests/{name}"


async def bowtie(*argv, stdin: str = "", exit_code=0, json=False):
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
    )
    raw_stdout, raw_stderr = await process.communicate(stdin.encode())
    decoded = stdout, stderr = raw_stdout.decode(), raw_stderr.decode()

    if exit_code == -1:
        assert process.returncode != 0, decoded
    else:
        assert process.returncode == exit_code, stderr

    if json:
        if stdout:
            try:
                jsonout = _json.loads(stdout)
            except _json.JSONDecodeError:
                pytest.fail(
                    f"stdout had invalid JSON: {stdout!r}\n\n"
                    f"stderr had {stderr}",
                )
            return jsonout, stderr
        pytest.fail(f"stdout was empty. stderr contained {stderr}")

    return decoded


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
always_valid = shellplementation(  # I'm sorry future me.
    name="always_valid",
    contents=r"""
    read
    printf '{"implementation": {"name": "always-valid", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    while IFS= read -r input; do
      [[ "$input" == '{"cmd": "stop"}' ]] && exit
      echo $input | awk '{
       seq = gensub(/.*"seq": ([^,]+).*/, "\\1", "g", $0);
       tests = gensub(/.*"tests": \[([^]]+)\].*/, "\\1", "g", $0);
       gsub(/}, \{/, "\n", tests);
       count = split(tests, tests_array, ",");
       result = sprintf("{\"seq\": %s, \"results\": [", seq);
       for (i = 1; i <= count; i++) {
         result = result "{\"valid\": true}";
         if (i < count) {
             result = result ",";
         }
       }
       result = result "]}";
       print result;
      }'
    done
    """,  # noqa: E501
)
passes_smoke = shellplementation(
    name="passes_smoke",
    contents=r"""
    read
    printf '{"implementation": {"name": "passes-smoke", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    printf '{"seq": 1, "results": [{"valid": true}, {"valid": true}, {"valid": true}, {"valid": true}, {"valid": true}]}\n'
    read
    printf '{"seq": 2, "results": [{"valid": false}, {"valid": false}, {"valid": false}, {"valid": false}, {"valid": false}]}\n'
    """,  # noqa: E501
)
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
    read
    printf 'BOOM!\n' >&2
    """,
)
fail_on_dialect = shellplementation(
    name="fail_on_dialect",
    contents=r"""
    read
    printf '{"implementation": {"name": "fail-on-dialect", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read
    printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
fail_on_run = shellplementation(
    name="fail_on_run",
    contents=r"""
    read
    printf '{"implementation": {"name": "fail-on-run", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read
    printf '{"ok": "true"}\n'
    read
    printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
nonjson_on_run = shellplementation(
    name="nonjson_on_run",
    contents=r"""
    read
    printf '{"implementation": {"name": "nonjson-on-run", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read
    printf '{"ok": "true"}\n'
    read
    printf 'BOOM!\n'
    """,  # noqa: E501
)
wrong_seq = shellplementation(
    name="wrong_seq",
    contents=r"""
    read
    printf '{"implementation": {"name": "wrong-seq", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read
    printf '{"ok": "true"}\n'
    read
    printf '{"seq": 373737373737, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
wrong_version = shellplementation(
    name="wrong_version",
    contents=r"""
    read
    printf '{"implementation": {"name": "wrong-version", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 0}\n'
    read >&2
    """,  # noqa: E501
)
hit_the_network_once = shellplementation(
    name="hit_the_network_once",
    contents=r"""
    read
    printf '{"implementation": {"name": "hit-the-network", "language": "sh", "dialects": ["http://json-schema.org/draft-07/schema#"], "homepage": "urn:example", "source": "urn:example", "issues": "urn:example"}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    wget --timeout=1 -O - http://example.com >&2
    read
    printf '{"seq": 2, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
missing_homepage = shellplementation(
    name="missing_homepage",
    contents=r"""
    read
    printf '{"implementation": {"name": "missing-homepage", "language": "sh", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    """,  # noqa: E501
)
with_versions = shellplementation(
    name="with_versions",
    contents=r"""
    read
    printf '{"implementation": {"name": "with-versions", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"], "language_version": "123", "os": "Lunix", "os_version": "37"}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    printf '{"seq": 1, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
links = shellplementation(
    name="links",
    contents=r"""
    read
    printf '{"implementation": {"name": "links", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["http://json-schema.org/draft-07/schema#"], "links": [{"description": "foo", "url": "urn:example:foo"}, {"description": "bar", "url": "urn:example:bar"}]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    printf '{"seq": 1, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
only_draft3 = shellplementation(
    name="only_draft3",
    contents=r"""
    read
    printf '{"implementation": {"name": "only-draft3", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["http://json-schema.org/draft-03/schema#"]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    printf '{"seq": 1, "results": [{"valid": true}]}\n'
    """,  # noqa: E501
)
fakejsimpl = shellplementation(
    name="fakejsimpl",
    contents=r"""
    read
    printf '{"implementation": {"name": "fakejsimpl", "language": "javascript", "homepage": "urn:example", "issues": "urn:example", "source": "urn:example", "dialects": ["http://json-schema.org/draft-07/schema#"]}, "version": 1}\n'
    """,  # noqa: E501
)


def _failed(message, stderr):
    indented = indent(stderr.decode(), prefix=" " * 2)
    pytest.fail(f"{message}. stderr contained:\n\n{indented}")


@asynccontextmanager
async def run(*args, **kwargs):
    async def _send(stdin=""):
        input = dedent(stdin).lstrip("\n")
        stdout, stderr = await bowtie("run", *args, stdin=input, **kwargs)

        try:
            report = Report.from_serialized(stdout.splitlines())
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


@pytest.mark.asyncio
async def test_it_runs_tests_from_a_file(tmp_path, envsonschema):
    tests = tmp_path / "tests.jsonl"
    tests.write_text(
        """{"description": "foo", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }\n""",  # noqa: E501
    )
    async with run("-i", envsonschema, tests) as send:
        results, stderr = await send()

    assert results == [
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_suite(tmp_path, envsonschema):
    # FIXME: maybe make suite not read the remotes until it needs them
    tmp_path.joinpath("remotes").mkdir()

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

    stdout, stderr = await bowtie("suite", "-i", envsonschema, definitions)
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
                            tag("envsonschema"): TestResult.INVALID,
                        },
                    ),
                    (
                        two,
                        {
                            tag("envsonschema"): TestResult.INVALID,
                        },
                    ),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_set_schema_sets_a_dialect_explicitly(envsonschema):
    async with run("-i", envsonschema, "--set-schema") as send:
        results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.VALID},
    ], stderr


@pytest.mark.asyncio
async def test_no_tests_run(envsonschema):
    async with run("-i", envsonschema, exit_code=os.EX_NOINPUT) as send:
        results, stderr = await send("")

    assert results == []
    assert stderr != ""


@pytest.mark.asyncio
async def test_unknown_dialect(envsonschema):
    dialect = "some://other/URI/"
    async with run(
        "-i",
        envsonschema,
        "--dialect",
        dialect,
        exit_code=-1,
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "not a known dialect" in stderr.lower()


@pytest.mark.asyncio
async def test_nonurl_dialect(envsonschema):
    dialect = ";;;;;"
    async with run(
        "-i",
        envsonschema,
        "--dialect",
        dialect,
        exit_code=-1,
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "not a known dialect" in stderr.lower()


@pytest.mark.asyncio
async def test_unsupported_known_dialect(only_draft3):
    async with run(
        "-i",
        only_draft3,
        "--dialect",
        str(Dialect.by_alias()["draft2020-12"].uri),
        exit_code=-1,
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "unsupported dialect" in stderr.lower()


@pytest.mark.asyncio
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
        {
            tag("envsonschema"): ErroredTest.in_errored_case(),
        },
        {tag("envsonschema"): TestResult.INVALID},
        {
            tag("envsonschema"): ErroredTest.in_errored_case(),
        },
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_handles_dead_implementations(succeed_immediately, envsonschema):
    async with run(
        "-i",
        succeed_immediately,
        "-i",
        envsonschema,
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.INVALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr
    assert "startup failed" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_it_exits_when_no_implementations_succeed(succeed_immediately):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with run("-i", succeed_immediately, exit_code=-1) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert "startup failed" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_it_handles_immediately_broken_implementations(
    fail_immediately,
    envsonschema,
):
    async with run(
        "-i",
        fail_immediately,
        "-i",
        envsonschema,
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "startup failed" in stderr.lower(), stderr
    assert "BOOM!" in stderr, stderr
    assert results == [
        {tag("envsonschema"): TestResult.INVALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_it_handles_broken_start_implementations(
    fail_on_start,
    envsonschema,
):
    async with run(
        "-i",
        fail_on_start,
        "-i",
        envsonschema,
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "startup failed" in stderr.lower(), stderr
    assert "BOOM!" in stderr, stderr
    assert results == [
        {tag("envsonschema"): TestResult.INVALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_it_handles_broken_dialect_implementations(fail_on_dialect):
    async with run(
        "-i",
        fail_on_dialect,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert "got an error" in stderr.lower(), stderr


@pytest.mark.asyncio
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
        {
            tag("envsonschema"): ErroredTest.in_errored_case(),
        },
        {
            tag("envsonschema"): ErroredTest(
                context=dict(message="boom"),
            ),
        },
        {tag("envsonschema"): TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
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
async def test_it_handles_invalid_start_responses(missing_homepage):
    async with run("-i", missing_homepage, "-V", exit_code=-1) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "startup failed" in stderr.lower(), stderr
    assert "'homepage' is a required" in stderr, stderr
    assert results == [], stderr


@pytest.mark.asyncio
async def test_it_preserves_all_metadata(with_versions):
    async with run("-i", with_versions, "-V") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    # FIXME: we need to make run() return the whole report
    assert results == [
        {tag("with_versions"): TestResult.VALID},
    ], stderr


@pytest.mark.asyncio
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
async def test_wrong_version(wrong_version):
    """
    An implementation speaking the wrong version of the protocol is skipped.
    """
    async with run(
        "-i",
        wrong_version,
        "--dialect",
        "http://json-schema.org/draft-07/schema#",
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [], stderr
    assert "expected to speak version 1 " in stderr.lower(), stderr


@pytest.mark.asyncio
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
async def test_fail_fast(envsonschema):
    async with run("-i", envsonschema, "-x") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "3", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.VALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_max_fail(envsonschema):
    async with run("-i", envsonschema, "--max-fail", "2") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "3", "schema": {}, "tests": [{"description": "valid:0", "instance": 8, "valid": true}] }
            {"description": "4", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.VALID},
        {tag("envsonschema"): TestResult.INVALID},
        {tag("envsonschema"): TestResult.INVALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_max_fail_with_fail_fast(envsonschema):
    async with run(
        "-i",
        envsonschema,
        "--max-fail",
        "2",
        "--fail-fast",
    ) as send:
        with pytest.raises(AssertionError) as exec_info:
            results, stderr = await send(
                """
                    {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
                    {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
                    {"description": "3", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
                    """,  # noqa: E501
            )
        assert (
            "Error: Cannot use --fail-fast with --max-fail / --max-error"
            in exec_info.value.args[0]
        )


@pytest.mark.asyncio
async def test_filter(envsonschema):
    async with run("-i", envsonschema, "-k", "baz") as send:
        results, stderr = await send(
            """
            {"description": "foo", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "bar", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "baz", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {tag("envsonschema"): TestResult.VALID},
    ], stderr
    assert stderr == ""


@pytest.mark.asyncio
async def test_smoke_pretty(envsonschema):
    stdout, stderr = await bowtie(
        "smoke",
        "--format",
        "pretty",
        "-i",
        envsonschema,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert (
        dedent(stdout)
        == dedent(
            """
            · allow-everything: ✗✗✗✗✗✗
            · allow-nothing: ✓✓✓✓✓✓
        """,
        ).lstrip("\n")
    ), stderr


@pytest.mark.asyncio
async def test_smoke_markdown(envsonschema):
    stdout, stderr = await bowtie(
        "smoke",
        "--format",
        "markdown",
        "-i",
        envsonschema,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert (
        dedent(stdout)
        == dedent(
            """
            * allow-everything: ✗✗✗✗✗✗
            * allow-nothing: ✓✓✓✓✓✓
        """,
        ).lstrip("\n")
    ), stderr


@pytest.mark.asyncio
async def test_smoke_json(envsonschema):
    jsonout, stderr = await bowtie(
        "smoke",
        "--format",
        "json",
        "-i",
        envsonschema,
        json=True,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert jsonout == [
        {
            "case": {
                "description": "allow-everything",
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                },
                "tests": [
                    {"description": "boolean", "instance": True},
                    {"description": "integer", "instance": 37},
                    {"description": "number", "instance": 37.37},
                    {"description": "string", "instance": "37"},
                    {"description": "array", "instance": [37]},
                    {"description": "object", "instance": {"foo": 37}},
                ],
            },
            "result": {
                "results": [
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                ],
            },
        },
        {
            "case": {
                "description": "allow-nothing",
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "not": {},
                },
                "tests": [
                    {"description": "boolean", "instance": True},
                    {"description": "integer", "instance": 37},
                    {"description": "number", "instance": 37.37},
                    {"description": "string", "instance": "37"},
                    {"description": "array", "instance": [37]},
                    {"description": "object", "instance": {"foo": 37}},
                ],
            },
            "result": {
                "results": [
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                    {"valid": False},
                ],
            },
        },
    ], stderr


@pytest.mark.asyncio
async def test_smoke_quiet(envsonschema):
    stdout, stderr = await bowtie(
        "smoke",
        "--quiet",
        "-i",
        envsonschema,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert stdout == "", stderr


@pytest.mark.asyncio
async def test_smoke_multiple(envsonschema, passes_smoke):
    stdout, stderr = await bowtie(
        "smoke",
        "--format",
        "pretty",
        "-i",
        envsonschema,
        "-i",
        passes_smoke,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert (
        dedent(stderr)
        == dedent(
            """\
            Testing 'bowtie-integration-tests/passes_smoke'...


            ✅ all passed
            Testing 'bowtie-integration-tests/envsonschema'...


            ❌ some failures
            """,
        )
        or dedent(stderr)
        == dedent(
            """\
            Testing 'bowtie-integration-tests/envsonschema'...


            ❌ some failures
            Testing 'bowtie-integration-tests/passes_smoke'...


            ✅ all passed
            """,
        )
    ), stdout


@pytest.mark.asyncio
async def test_info_pretty(envsonschema):
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "pretty",
        "-i",
        envsonschema,
    )
    assert stdout == dedent(
        """\
        name: "envsonschema"
        language: "python"
        homepage: "https://github.com/bowtie-json-schema/bowtie"
        issues: "https://github.com/bowtie-json-schema/bowtie/issues"
        source: "https://github.com/bowtie-json-schema/bowtie"
        dialects: [
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
async def test_info_markdown(envsonschema):
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "markdown",
        "-i",
        envsonschema,
    )
    assert stdout == dedent(
        """\
        **name**: "envsonschema"
        **language**: "python"
        **homepage**: "https://github.com/bowtie-json-schema/bowtie"
        **issues**: "https://github.com/bowtie-json-schema/bowtie/issues"
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
async def test_info_json(envsonschema):
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "json",
        "-i",
        envsonschema,
    )
    assert _json.loads(stdout) == {
        "name": "envsonschema",
        "language": "python",
        "homepage": "https://github.com/bowtie-json-schema/bowtie",
        "issues": "https://github.com/bowtie-json-schema/bowtie/issues",
        "source": "https://github.com/bowtie-json-schema/bowtie",
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
async def test_info_json_multiple_implementations(envsonschema, links):
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "json",
        "-i",
        envsonschema,
        "-i",
        links,
    )
    assert _json.loads(stdout) == {
        tag("envsonschema"): {
            "name": "envsonschema",
            "language": "python",
            "homepage": "https://github.com/bowtie-json-schema/bowtie",
            "issues": "https://github.com/bowtie-json-schema/bowtie/issues",
            "source": "https://github.com/bowtie-json-schema/bowtie",
            "dialects": [
                "https://json-schema.org/draft/2020-12/schema",
                "https://json-schema.org/draft/2019-09/schema",
                "http://json-schema.org/draft-07/schema#",
                "http://json-schema.org/draft-06/schema#",
                "http://json-schema.org/draft-04/schema#",
                "http://json-schema.org/draft-03/schema#",
            ],
        },
        tag("links"): {
            "name": "links",
            "language": "sh",
            "homepage": "urn:example",
            "issues": "urn:example",
            "source": "urn:example",
            "dialects": ["http://json-schema.org/draft-07/schema#"],
            "links": [
                {"description": "foo", "url": "urn:example:foo"},
                {"description": "bar", "url": "urn:example:bar"},
            ],
        },
    }, stderr
    assert stderr == ""


@pytest.mark.asyncio
async def test_info_links(links):
    stdout, stderr = await bowtie(
        "info",
        "--format",
        "pretty",
        "-i",
        links,
    )
    assert stdout == dedent(
        """\
        name: "links"
        language: "sh"
        homepage: "urn:example"
        issues: "urn:example"
        source: "urn:example"
        dialects: [
          "http://json-schema.org/draft-07/schema#"
        ]
        links: [
          {
            "description": "foo",
            "url": "urn:example:foo"
          },
          {
            "description": "bar",
            "url": "urn:example:bar"
          }
        ]
        """,
    )
    assert stderr == ""


@pytest.mark.asyncio
async def test_info_unsuccessful_start(succeed_immediately):
    stdout, stderr = await bowtie(
        "info",
        "-i",
        succeed_immediately,
        exit_code=-1,
    )

    assert stdout == ""
    assert "failed to start" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_filter_given_implementations_lang(
    envsonschema,
    lintsonschema,
    fakejsimpl,
):
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        envsonschema,
        "-i",
        lintsonschema,
        "-i",
        fakejsimpl,
        "--supports-language",
        "python",
    )
    assert sorted(stdout.splitlines()) == {
        tag("envsonschema"),
        tag("lintsonschema"),
    }
    assert stderr == ""


@pytest.mark.asyncio
async def test_filter_given_implementations_dialect(
    envsonschema,
    lintsonschema,
    fakejsimpl,
):
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        envsonschema,
        "-i",
        lintsonschema,
        "-i",
        fakejsimpl,
        "--supports-dialect",
        "2020-12",
    )
    assert sorted(stdout.splitlines()) == {
        tag("envsonschema"),
        tag("lintsonschema"),
    }
    assert stderr == ""


@pytest.mark.asyncio
async def test_filter_given_implementations_lang_and_dialect(
    envsonschema,
    lintsonschema,
    fakejsimpl,
):
    stdout, stderr = await bowtie(
        "filter-implementations",
        "-i",
        envsonschema,
        "-i",
        lintsonschema,
        "-i",
        fakejsimpl,
        "-l",
        "javascript",
        "-d",
        "7",
    )
    assert stdout == {
        tag("fakejsimpl"),
    }
    assert stderr == ""


@pytest.mark.asyncio
async def test_validate(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("a.json").write_text("12")
    tmp_path.joinpath("b.json").write_text('"foo"')

    stdout, _ = await bowtie(
        "validate",
        "-i",
        envsonschema,
        tmp_path / "schema.json",
        tmp_path / "a.json",
        tmp_path / "b.json",
        exit_code=0,
    )
    assert stdout != ""  # the real assertion here is we succeed above


@pytest.mark.asyncio
async def test_summary_show_failures(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        envsonschema,
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
    )
    assert stderr == ""
    assert jsonout == [
        [
            tag("envsonschema"),
            dict(failed=2, skipped=0, errored=0),
        ],
    ]


@pytest.mark.asyncio
async def test_summary_show_failures_markdown(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("one.json").write_text("12")
    tmp_path.joinpath("two.json").write_text("37")

    validate_stdout, _ = await bowtie(
        "validate",
        "-i",
        envsonschema,
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
    )
    assert stderr == ""
    assert stdout == dedent(
        """\
        # Bowtie Failures Summary

        | Implementation | Skips | Errors | Failures |
        |:-:|:-:|:-:|:-:|
        | envsonschema (python) | 0 | 0 | 2 |

        **2 tests ran**

        """,
    )


@pytest.mark.asyncio
async def test_validate_no_tests(envsonschema, tmp_path):
    """
    Don't bother starting up if we have nothing to run.
    """
    schema = tmp_path / "schema.json"
    schema.write_text("{}")
    stdout, stderr = await bowtie(
        "validate",
        "-i",
        envsonschema,
        schema,
        exit_code=-1,
    )
    assert stdout == ""
    assert stderr == ""


@pytest.mark.asyncio
async def test_summary_show_validation(envsonschema, always_valid):
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
        always_valid,
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
    assert stderr == ""
    assert jsonout == [
        [
            {"type": "integer"},
            [
                [
                    12,
                    {
                        tag("always_valid"): "valid",
                        tag("envsonschema"): "valid",
                    },
                ],
                [
                    12.5,
                    {
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
                        tag("envsonschema"): "error",
                    },
                ],
                [
                    37,
                    {
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
                        tag("envsonschema"): "error",
                    },
                ],
                [
                    12,
                    {
                        tag("always_valid"): "valid",
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
                        tag("always_valid"): "valid",
                        tag("envsonschema"): "error",
                    },
                ],
            ],
        ],
    ], run_stderr


@pytest.mark.asyncio
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
async def test_badges_nothing_ran(envsonschema, tmp_path):
    run_stdout, _ = await bowtie(
        "run",
        "-i",
        envsonschema,
        stdin="",
        exit_code=-1,  # no test cases run causes a non-zero here
    )

    badges = tmp_path / "badges"
    stdout, stderr = await bowtie(
        "badges",
        badges,
        stdin=run_stdout,
        exit_code=-1,
    )
    assert stdout == ""
    assert stderr != ""
    assert not badges.is_dir()


@pytest.mark.asyncio
async def test_run_with_registry(always_valid):
    raw = """
        {"description":"one","schema":{"type": "integer"}, "registry":{"urn:example:foo": "http://example.com"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
    """  # noqa: E501

    run_stdout, run_stderr = await bowtie(
        "run",
        "-i",
        always_valid,
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
    assert stderr == ""
    assert jsonout == [
        [
            {"type": "integer"},
            [
                [12, {tag("always_valid"): "valid"}],
                [12.5, {tag("always_valid"): "valid"}],
            ],
        ],
    ], run_stderr


@pytest.mark.asyncio
async def test_no_such_image(tmp_path):
    stdout, stderr = await bowtie(
        "run",
        "-i",
        "no-such-image",
        exit_code=-1,
    )
    assert stdout == ""
    assert (
        "[error    ] Not a known Bowtie implementation. [ghcr.io/bowtie-json-schema/no-such-image]\n"  # noqa: E501
        in stderr
    ), stderr

    stdout, stderr = await bowtie(
        "smoke",
        "-i",
        "no-such-image",
        exit_code=-1,
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
        exit_code=-1,
    )
    assert stdout == ""
    assert (
        "[error    ] Not a known Bowtie implementation. [ghcr.io/bowtie-json-schema/no-such-image]\n"  # noqa: E501
        in stderr
    ), stderr


@pytest.mark.asyncio
async def test_suite_not_a_suite_directory(envsonschema, tmp_path):
    _, stderr = await bowtie(
        "suite",
        "-i",
        envsonschema,
        tmp_path,
        exit_code=-1,
    )
    assert re.search(r"does not contain .* cases", stderr)
