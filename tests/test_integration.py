from contextlib import asynccontextmanager
from io import BytesIO
from pathlib import Path
from pprint import pformat
from textwrap import dedent, indent
import asyncio
import json
import os
import sys
import tarfile

from aiodocker.exceptions import DockerError
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


def strimplementation(name, contents, files={}):  # noqa: B006
    fileobj = BytesIO()
    with tarfile.TarFile(fileobj=fileobj, mode="w") as tar:
        contents = dedent(contents).encode("utf-8")
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(contents)
        tar.addfile(info, BytesIO(contents))

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
        FROM alpine:3.16
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
    printf '{"implementation": {"name": "always-valid", "language": "sh", "homepage": "urn:example", "issues": "urn:example", "dialects": ["https://json-schema.org/draft/2020-12/schema"]}, "ready": true, "version": 1}\n'
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
    contents="FROM alpine:3.16\nENTRYPOINT true\n",
)
fail_on_start = strimplementation(
    name="fail_on_start",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf 'BOOM!\n' >&2
    """,
)
fail_on_run = strimplementation(
    name="fail_on_run",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf '{"implementation": {"dialects": ["urn:foo"]}, "ready": true, "version": 1}\n' && read && printf 'BOOM!\n' >&2
    """,  # noqa: E501
)
wrong_version = strimplementation(
    name="wrong_version",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf '{"implementation": {"dialects": ["urn:foo"]}, "ready": true, "version": 0}\n' && read >&2
    """,  # noqa: E501
)
hit_the_network = strimplementation(
    name="hit_the_network",
    contents=r"""
    FROM alpine:3.16
    CMD read && printf '{"implementation": {"dialects": ["urn:foo"]}, "ready": true, "version": 1}\n' && read && printf '{"ok": true}\n' && read && wget --timeout=1 -O - http://example.com >&2 && printf '{"seq": 0, "results": [{"valid": true}]}\n' && read
    """,  # noqa: E501
)


def _failed(message, stderr):
    indented = indent(stderr.decode(), prefix=" " * 2)
    pytest.fail(f"{message}. stderr contained:\n\n{indented}")


@asynccontextmanager
async def bowtie(*args, succeed=True, expecting_errors=False):
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
            header = next(lines, None)
            if header is None:
                _failed("No report produced", stderr)
            try:
                RunInfo(**header)
            except _InvalidBowtieReport:
                _failed("Invalid report", stderr)
        else:
            assert proc.returncode != 0

        successful, errors, cases = [], [], []
        for each in sorted(lines, key=lambda e: e.get("implementation", "")):
            if "results" in each:
                successful.append(each["results"])
            elif "case" in each:
                cases.append(each)
            elif "did_fail_fast" in each:
                continue
            else:
                errors.append(each)

        assert errors if expecting_errors else not errors, pformat(errors)
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
    async with bowtie("-i", envsonschema, expecting_errors=True) as send:
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
async def test_handles_broken_start_implementations(
    fail_on_start,
    envsonschema,
):
    async with bowtie("-i", fail_on_start, "-i", envsonschema) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            {"description": "2", "schema": {}, "tests": [{"description": "bar", "instance": {}}] }
            """,  # noqa: E501
        )

    assert b"startup failed" in stderr.lower(), stderr
    assert b"BOOM!" in stderr, stderr
    assert returncode != 0, stderr
    assert results == [[{"valid": False}], [{"valid": False}]]


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
    async with bowtie("-i", envsonschema, expecting_errors=True) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "error:", "schema": {}, "tests": [{"description": "crash:1", "instance": {}}] }
            {"description": "4", "schema": {}, "tests": [{"description": "error:message=boom", "instance": {}}] }
            {"description": "works", "schema": {}, "tests": [{"description": "valid:1", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == [
        [{"context": {"message": "boom"}, "errored": True, "skipped": False}],
        [{"valid": True}],
    ], stderr
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
    async with bowtie(
        "-i",
        hit_the_network,
        "--dialect",
        "urn:foo",
        expecting_errors=True,
    ) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "foo", "instance": {}}] }
            """,  # noqa: E501
        )

    assert results == []
    assert b"bad address" in stderr.lower(), stderr


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
        succeed=False,
    ) as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "1", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [], stderr
    assert b"VersionMismatch: (1, 0)" in stderr, stderr
    assert returncode != 0, stderr


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
async def test_filter(envsonschema):
    async with bowtie("-i", envsonschema, "-k", "baz") as send:
        returncode, results, _, _, stderr = await send(
            """
            {"description": "foo", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            {"description": "bar", "schema": {}, "tests": [{"description": "valid:0", "instance": 7, "valid": true}] }
            {"description": "baz", "schema": {}, "tests": [{"description": "valid:1", "instance": {}, "valid": true}] }
            """,  # noqa: E501
        )

    assert results == [[{"valid": True}]], stderr
    assert stderr != ""
    assert returncode == 0, stderr


@pytest.mark.asyncio
async def test_smoke_pretty(envsonschema):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "--format",
        "pretty",
        "-i",
        envsonschema,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, _ = await proc.communicate()
    # FIXME: This != 0 is because indeed envsonschema gets answers wrong
    #        Change to asserting about the smoke stdout once that's there.
    assert proc.returncode != 0


@pytest.mark.asyncio
async def test_smoke_json(envsonschema):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "--format",
        "json",
        "-i",
        envsonschema,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    # FIXME: This != 0 is because indeed envsonschema gets answers wrong
    #        Change to asserting about the smoke stdout once that's there.
    assert proc.returncode == 0, (stdout, stderr)
    assert json.loads(stdout) == [
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
            "response": {"errored": False, "failed": True},
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
            "response": {"errored": False, "failed": False},
        },
    ]


@pytest.mark.asyncio
async def test_info_pretty(envsonschema):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "info",
        "--format",
        "pretty",
        "-i",
        envsonschema,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    assert proc.returncode == 0, (stdout, stderr)
    assert stdout.decode() == dedent(
        """\
        name: "envsonschema"
        language: "python"
        homepage: "https://github.com/bowtie-json-schema/bowtie/"
        issues: "https://github.com/bowtie-json-schema/bowtie/issues"
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
    assert stderr == b""


@pytest.mark.asyncio
async def test_info_json(envsonschema):
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "info",
        "--format",
        "json",
        "-i",
        envsonschema,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    assert proc.returncode == 0, (stdout, stderr)
    assert json.loads(stdout) == {
        "name": "envsonschema",
        "language": "python",
        "homepage": "https://github.com/bowtie-json-schema/bowtie/",
        "issues": "https://github.com/bowtie-json-schema/bowtie/issues",
        "dialects": [
            "https://json-schema.org/draft/2020-12/schema",
            "https://json-schema.org/draft/2019-09/schema",
            "http://json-schema.org/draft-07/schema#",
            "http://json-schema.org/draft-06/schema#",
            "http://json-schema.org/draft-04/schema#",
            "http://json-schema.org/draft-03/schema#",
        ],
    }
    assert stderr == b""


@pytest.mark.asyncio
async def test_validate(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("a.json").write_text("12")
    tmp_path.joinpath("b.json").write_text('"foo"')

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "validate",
        "-i",
        envsonschema,
        tmp_path / "schema.json",
        tmp_path / "a.json",
        tmp_path / "b.json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, _ = await proc.communicate()
    assert proc.returncode == 0


@pytest.mark.asyncio
async def test_summary_show_failures(envsonschema, tmp_path):
    tmp_path.joinpath("schema.json").write_text("{}")
    tmp_path.joinpath("instance.json").write_text("12")

    validate = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "validate",
        "-i",
        envsonschema,
        tmp_path / "schema.json",
        tmp_path / "instance.json",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    validate_stdout, _ = await validate.communicate()

    summary_failures = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "summary",
        "--format",
        "json",
        "--show",
        "failures",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await summary_failures.communicate(validate_stdout)
    assert stderr == b""
    assert json.loads(stdout) == [
        [
            ["envsonschema", "python"],
            dict(
                errored_cases=0,
                total_cases=1,
                total_tests=1,
                failed_tests=0,
                skipped_tests=0,
                errored_tests=0,
            ),
        ],
    ]


@pytest.mark.asyncio
async def test_summary_show_validation(envsonschema, always_valid, tmp_path):
    run = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        envsonschema,
        "-i",
        always_valid,
        "-V",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    raw = """
        {"description":"one","schema":{"type": "integer"},"tests":[{"description":"valid:1","instance":12},{"description":"valid:0","instance":12.5}]}
        {"description":"two","schema":{"type": "string"},"tests":[{"description":"crash:1","instance":"{}"}]}
        {"description":"crash:1","schema":{"type": "number"},"tests":[{"description":"three","instance":"{}"}, {"description": "another", "instance": 37}]}
        {"description":"four","schema":{"type": "array"},"tests":[{"description":"skip:message=foo","instance":""}]}
        {"description":"skip:message=bar","schema":{"type": "boolean"},"tests":[{"description":"five","instance":""}]}
        {"description":"six","schema":{"type": "array"},"tests":[{"description":"error:message=boom","instance":""}, {"description":"valid:0", "instance":12}]}
        {"description":"error:message=boom","schema":{"type": "array"},"tests":[{"description":"seven","instance":""}]}
    """  # noqa: E501
    lines = dedent(raw.strip("\n")).encode("utf-8")
    run_stdout, run_stderr = await run.communicate(lines)

    summary_validation = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "summary",
        "--format",
        "json",
        "--show",
        "validation",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await summary_validation.communicate(run_stdout)
    assert stderr == b""
    assert json.loads(stdout) == [
        [
            {"type": "integer"},
            [
                [12, ["valid", "valid"]],
                [12.5, ["invalid", "valid"]],
            ],
        ],
        [
            {"type": "string"},
            [
                ["{}", ["error", "valid"]],
            ],
        ],
        [
            {"type": "number"},
            [
                ["{}", ["error", "valid"]],
                [37, ["error", "valid"]],
            ],
        ],
        [
            {"type": "array"},
            [
                ["", ["skipped", "valid"]],
            ],
        ],
        [
            {"type": "boolean"},
            [
                ["", ["skipped", "valid"]],
            ],
        ],
        [
            {"type": "array"},
            [
                ["", ["error", "valid"]],
                [12, ["invalid", "valid"]],
            ],
        ],
        [
            {"type": "array"},
            [
                ["", ["error", "valid"]],
            ],
        ],
    ], run_stderr.decode()


@pytest.mark.asyncio
async def test_no_such_image():
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "run",
        "-i",
        "no-such-image",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    assert stdout == b""
    assert (
        b"[error    ] Not a known Bowtie implementation. [ghcr.io/bowtie-json-schema/no-such-image] \n"  # noqa: E501
        in stderr
    )
    assert proc.returncode != 0

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "-i",
        "no-such-image",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    assert (
        b"'ghcr.io/bowtie-json-schema/no-such-image' is not a known Bowtie implementation.\n"  # noqa: E501
        in stderr
    )
    assert proc.returncode != 0

    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "validate",
        "-i",
        "no-such-image",
        "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate(b"{}")
    assert stdout == b""
    assert (
        b"[error    ] Not a known Bowtie implementation. [ghcr.io/bowtie-json-schema/no-such-image] \n"  # noqa: E501
        in stderr
    )
    assert proc.returncode != 0
