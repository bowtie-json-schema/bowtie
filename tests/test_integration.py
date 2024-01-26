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

from bowtie import _report
from bowtie._commands import ErroredTest, TestResult

TestResult.__test__ = False  # frigging py.test


HERE = Path(__file__).parent
FAUXMPLEMENTATIONS = HERE / "fauxmplementations"


async def run(*argv, stdin: str = "", exit_code=0, json=False):
    """
    Run a subprocess asynchronously to completion.

    An exit code of `-1` means "any non-zero exit code".
    """
    process = await asyncio.create_subprocess_exec(
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
        tag = f"bowtie-integration-tests/{name}"
        lines = await images.build(fileobj=fileobj, encoding="utf-8", tag=tag)
        try:
            await docker.images.inspect(tag)
        except DockerError:
            pytest.fail(f"Failed to build {name}:\n\n{pformat(lines)}")
        yield tag
        await images.delete(name=tag, force=True)

    return _image


def fauxmplementation(name):
    fileobj = tar_from_directory(FAUXMPLEMENTATIONS / name)
    return image(name=name, fileobj=fileobj)


def strimplementation(name, contents, files={}, base="alpine:3.19"):
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
succeed_immediately = strimplementation(
    name="succeed",
    contents="ENTRYPOINT true",
)
fail_on_start = shellplementation(
    name="fail_on_start",
    contents=r"""
    read
    printf 'BOOM!\n' >&2
    """,
)
fail_on_run = shellplementation(
    name="fail_on_run",
    contents=r"""
    read
    printf '{"implementation": {"name": "fail-on-run", "language": "sh", "dialects": ["urn:foo"]}, "version": 1}\n'
    read
    printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
wrong_version = shellplementation(
    name="wrong_version",
    contents=r"""
    read
    printf '{"implementation": {"name": "wrong-version", "language": "sh", "dialects": ["urn:foo"]}, "version": 0}\n'
    read >&2
    """,  # noqa: E501
)
hit_the_network = shellplementation(
    name="hit_the_network",
    contents=r"""
    read
    printf '{"implementation": {"name": "hit-the-network", "language": "sh", "dialects": ["urn:foo"]}, "version": 1}\n'
    read
    printf '{"ok": true}\n'
    read
    wget --timeout=1 -O - http://example.com >&2
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


def _failed(message, stderr):
    indented = indent(stderr.decode(), prefix=" " * 2)
    pytest.fail(f"{message}. stderr contained:\n\n{indented}")


@asynccontextmanager
async def bowtie(*args, exit_code=0):
    process = await asyncio.create_subprocess_exec(
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
        stdout, stderr = await process.communicate(input)
        stdout, stderr = stdout.decode(), stderr.decode()

        try:
            report = _report.Report.from_serialized(stdout.splitlines())
        except _report.EmptyReport:
            results = []
        except _report.Invalid as err:
            pytest.fail(f"Invalid report: {err}\nStderr had:\n{stderr}")
        else:
            results = [
                test_result
                for _, case_results in report.cases_with_results()
                for _, test_result in case_results
            ]

        if exit_code == -1:
            assert process.returncode != 0, stderr
        else:
            assert process.returncode == exit_code, stderr

        return results, stderr

    yield _send


@pytest.mark.asyncio
async def test_validating_on_both_sides(lintsonschema):
    async with bowtie("-i", lintsonschema, "-V") as send:
        results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {"bowtie-integration-tests/lintsonschema": TestResult.VALID},
    ], stderr


@pytest.mark.asyncio
async def test_it_runs_tests_from_a_file(tmp_path, envsonschema):
    tests = tmp_path / "tests.jsonl"
    tests.write_text(
        """{"description": "foo", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }\n""",  # noqa: E501
    )
    async with bowtie("-i", envsonschema, tests) as send:
        results, stderr = await send()

    assert results == [
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_set_schema_sets_a_dialect_explicitly(envsonschema):
    async with bowtie("-i", envsonschema, "--set-schema") as send:
        results, stderr = await send(
            """
            {"description": "a test case", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {"bowtie-integration-tests/envsonschema": TestResult.VALID},
    ], stderr


@pytest.mark.asyncio
async def test_no_tests_run(envsonschema):
    async with bowtie("-i", envsonschema, exit_code=os.EX_NOINPUT) as send:
        results, stderr = await send("")

    assert results == []
    assert stderr != ""


@pytest.mark.asyncio
async def test_unsupported_dialect(envsonschema):
    dialect = "some://other/URI/"
    async with bowtie(
        "-i",
        envsonschema,
        "--dialect",
        dialect,
        exit_code=-1,
    ) as send:
        results, stderr = await send("")

    assert results == []
    assert "unsupported dialect" in stderr.lower()


@pytest.mark.asyncio
async def test_restarts_crashed_implementations(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "a", "instance": {}}] }
            {"description": "3", "schema": {}, "tests": [{"description": "sleep:8", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            "bowtie-integration-tests/envsonschema": ErroredTest.in_errored_case(),
        },
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
        {
            "bowtie-integration-tests/envsonschema": ErroredTest.in_errored_case(),
        },
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_handles_dead_implementations(succeed_immediately, envsonschema):
    async with bowtie(
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
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
    ], stderr
    assert "startup failed" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_it_exits_when_no_implementations_succeed(succeed_immediately):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with bowtie("-i", succeed_immediately, exit_code=-1) as send:
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
async def test_handles_broken_start_implementations(
    fail_on_start,
    envsonschema,
):
    async with bowtie(
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
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_handles_broken_run_implementations(fail_on_run):
    async with bowtie(
        "-i",
        fail_on_run,
        "--dialect",
        "urn:foo",
        exit_code=-1,
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert "got an error" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_implementations_can_signal_errors(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "error:", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "4", "schema": {}, "tests": [{"description": "error:message=boom", "instance": {}}] }
            {"description": "works", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            "bowtie-integration-tests/envsonschema": ErroredTest.in_errored_case(),
        },
        {
            "bowtie-integration-tests/envsonschema": ErroredTest(
                context=dict(message="boom"),
            ),
        },
        {"bowtie-integration-tests/envsonschema": TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_it_handles_split_messages(envsonschema):
    async with bowtie("-i", envsonschema) as send:
        results, stderr = await send(
            """
            {"description": "split:1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}, {"description": "2 valid:0", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {"bowtie-integration-tests/envsonschema": TestResult.VALID},
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
    ], stderr


@pytest.mark.asyncio
async def test_it_handles_invalid_start_responses(missing_homepage):
    async with bowtie("-i", missing_homepage, "-V", exit_code=-1) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert "startup failed" in stderr.lower(), stderr
    assert "'homepage' is a required" in stderr, stderr
    assert results == [], stderr


@pytest.mark.asyncio
async def test_it_prevents_network_access(hit_the_network):
    """
    Don't uselessly "run" tests on no implementations.
    """
    async with bowtie(
        "-i",
        hit_the_network,
        "--dialect",
        "urn:foo",
    ) as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        {
            "bowtie-integration-tests/hit_the_network": ErroredTest.in_errored_case(),
        },
    ], stderr
    assert "bad address" in stderr.lower(), stderr


@pytest.mark.asyncio
async def test_wrong_version(wrong_version):
    """
    An implementation speaking the wrong version of the protocol is skipped.
    """
    async with bowtie(
        "-i",
        wrong_version,
        "--dialect",
        "urn:foo",
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
async def test_fail_fast(envsonschema):
    async with bowtie("-i", envsonschema, "-x") as send:
        results, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "2", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "3", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {"bowtie-integration-tests/envsonschema": TestResult.VALID},
        {"bowtie-integration-tests/envsonschema": TestResult.INVALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_filter(envsonschema):
    async with bowtie("-i", envsonschema, "-k", "baz") as send:
        results, stderr = await send(
            """
            {"description": "foo", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "bar", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "baz", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [
        {"bowtie-integration-tests/envsonschema": TestResult.VALID},
    ], stderr
    assert stderr != ""


@pytest.mark.asyncio
async def test_smoke_pretty(envsonschema):
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
            · allow-everything schema: ✗✗
            · allow-nothing schema: ✓
        """,
        ).lstrip("\n")
    ), stderr


@pytest.mark.asyncio
async def test_smoke_json(envsonschema):
    jsonout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
                "description": "allow-everything schema",
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                },
                "tests": [
                    {"description": "First", "instance": 1},
                    {"description": "Second", "instance": "foo"},
                ],
            },
            "result": {"results": [{"valid": False}, {"valid": False}]},
        },
        {
            "case": {
                "description": "allow-nothing schema",
                "schema": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "not": {},
                },
                "tests": [{"description": "First", "instance": 12}],
            },
            "result": {"results": [{"valid": False}]},
        },
    ], stderr


@pytest.mark.asyncio
async def test_smoke_quiet(envsonschema):
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "--quiet",
        "-i",
        envsonschema,
        exit_code=-1,  # because indeed envsonschema gets answers wrong.
    )
    assert stdout == "", stderr


@pytest.mark.asyncio
async def test_info_pretty(envsonschema):
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
async def test_info_json(envsonschema):
    jsonout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "info",
        "--format",
        "json",
        "-i",
        envsonschema,
        json=True,
    )
    assert jsonout == {
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
async def test_validate(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("a.json").write_text("12")
    tmp_path.joinpath("b.json").write_text('"foo"')

    stdout, _ = await run(
        sys.executable,
        "-m",
        "bowtie",
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

    validate_stdout, _ = await run(
        sys.executable,
        "-m",
        "bowtie",
        "validate",
        "-i",
        envsonschema,
        "--expect",
        "valid",
        tmp_path / "schema.json",
        tmp_path / "one.json",
        tmp_path / "two.json",
    )

    jsonout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
            "bowtie-integration-tests/envsonschema",
            dict(failed=2, skipped=0, errored=0),
        ],
    ]


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
    run_stdout, run_stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        envsonschema,
        "-i",
        always_valid,
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    jsonout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "valid",
                    },
                ],
                [
                    12.5,
                    {
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "invalid",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "error",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "error",
                    },
                ],
                [
                    37,
                    {
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "error",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "skipped",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "skipped",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "error",
                    },
                ],
                [
                    12,
                    {
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "invalid",
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
                        "bowtie-integration-tests/always_valid": "valid",
                        "bowtie-integration-tests/envsonschema": "error",
                    },
                ],
            ],
        ],
    ], run_stderr


@pytest.mark.asyncio
async def test_badges(envsonschema, tmp_path):
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    run_stdout, _ = await run(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        envsonschema,
        stdin=dedent(raw.strip("\n")),
    )

    badges = tmp_path / "badges"
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "badges",
        badges,
        stdin=run_stdout,
    )

    assert {path.relative_to(badges) for path in badges.rglob("*")} == {
        Path("python-envsonschema"),
        Path("python-envsonschema/supported_versions.json"),
        Path("python-envsonschema/compliance"),
        Path("python-envsonschema/compliance/Draft_2020-12.json"),
    }


@pytest.mark.asyncio
async def test_badges_nothing_ran(envsonschema, tmp_path):
    run_stdout, _ = await run(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        envsonschema,
        stdin="",
        exit_code=-1,  # no test cases run causes a non-zero here
    )

    badges = tmp_path / "badges"
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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

    run_stdout, run_stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        always_valid,
        "-V",
        stdin=dedent(raw.strip("\n")),
    )

    jsonout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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
                [12, {"bowtie-integration-tests/always_valid": "valid"}],
                [12.5, {"bowtie-integration-tests/always_valid": "valid"}],
            ],
        ],
    ], run_stderr


@pytest.mark.asyncio
async def test_no_such_image():
    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
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

    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "-i",
        "no-such-image",
        exit_code=-1,
    )
    assert (
        "'ghcr.io/bowtie-json-schema/no-such-image' is not a known Bowtie implementation.\n"  # noqa: E501
        in stderr
    ), stderr

    stdout, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "validate",
        "-i",
        "no-such-image",
        "-",
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
    _, stderr = await run(
        sys.executable,
        "-m",
        "bowtie",
        "suite",
        "-i",
        envsonschema,
        tmp_path,
        exit_code=-1,
    )
    assert re.search(r"does not contain .* cases", stderr)
