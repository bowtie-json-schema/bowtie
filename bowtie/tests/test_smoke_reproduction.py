"""
Regression tests for reproducing smoke-test reference failures.
"""

import asyncio
import json
import os
import shlex
import sys

import pytest

from bowtie import _smoke
from bowtie._core import Dialect, TestCase as BowtieTestCase


def reference_failure_result():
    """
    Construct a smoke result with the exact case to be replayed.
    """
    dialect = Dialect.by_short_name()["draft7"]
    uri = "http://bowtie.report/cli/smoke/ref-to-string"
    case = BowtieTestCase.from_dict(
        dialect=dialect,
        description="Reference failing on O'Reilly's case",
        schema={"$schema": str(dialect.uri), "$ref": uri},
        registry={uri: {"type": "string"}},
        tests=[
            {"description": "string", "instance": "valid", "valid": True},
            {"description": "non-string", "instance": 37, "valid": False},
        ],
    )
    result = _smoke.Result(
        id="bowtie.tests.miniatures:no_registry_support",
        dialects=_smoke.DialectResults(),
        ref=(dialect, case, None),
        connectable_id="direct:bowtie.tests.miniatures:no_registry_support",
    )
    return result, case


def test_ref_reproduction_serializes_the_original_case():
    result, case = reference_failure_result()
    command = result.ref_reproduction_command()
    assert command is not None

    # Unfold the explicit POSIX line continuations before parsing.
    unfolded = command.replace("\\\n", "")
    printer, runner = unfolded.split("|", maxsplit=1)
    assert json.loads("".join(shlex.split(printer)[2:])) == (
        case.serializable()
    )
    assert shlex.split(runner) == [
        "bowtie",
        "run",
        "-i",
        "direct:bowtie.tests.miniatures:no_registry_support",
        "--dialect",
        "draft7",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("width", [100, 120])
async def test_ref_reproduction_survives_rich_terminal_rendering(width):
    """
    A command copied from the pretty smoke panel must retain valid syntax.

    Exercise the actual CLI renderer, not just ref_reproduction_command().
    """
    environment = dict(
        os.environ,
        TERMINAL_WIDTH=str(width),
        COLUMNS=str(width),
        PYTHONUTF8="1",
    )
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        "-m",
        "bowtie",
        "smoke",
        "--format",
        "pretty",
        "-i",
        "direct:bowtie.tests.miniatures:no_registry_support",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=environment,
    )
    output, error = await process.communicate()
    assert process.returncode == 0, error.decode()

    # Strip Rich panel borders and padding as a user would when copying.
    lines = []
    copying = False
    panel_borders = 2
    for line in output.decode("utf-8").splitlines():
        if line.count("│") < panel_borders:
            continue
        displayed = line.split("│", maxsplit=2)[1].strip()
        if displayed.startswith("printf '%s'"):
            copying = True
        if copying:
            lines.append(displayed)
            if displayed.startswith("--dialect "):
                break

    assert lines, output.decode()
    assert lines[-1].startswith("--dialect "), output.decode()
    # Backslash-newline continuation must survive the rendered terminal.
    command = "\n".join(lines).replace("\\\n", "")
    printer, runner = command.split("|", maxsplit=1)
    case = json.loads("".join(shlex.split(printer)[2:]))
    assert case["schema"]["$ref"] == (
        "http://bowtie.report/cli/smoke/ref-to-string"
    )
    assert case["registry"][case["schema"]["$ref"]] == {"type": "string"}
    assert [test["valid"] for test in case["tests"]] == [True, False]
    assert shlex.split(runner) == [
        "bowtie",
        "run",
        "-i",
        "direct:bowtie.tests.miniatures:no_registry_support",
        "--dialect",
        "v1",
    ]


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell reproducer")
async def test_ref_reproduction_command_runs_the_failed_case():
    result, case = reference_failure_result()
    command = result.ref_reproduction_command()
    assert command is not None
    # Use the active interpreter instead of relying on PATH.
    command = command.replace(
        "bowtie run",
        f"{shlex.quote(sys.executable)} -m bowtie run",
        1,
    )
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    output, error = await process.communicate()

    assert process.returncode == 0, error.decode()
    text = output.decode()
    assert case.schema["$ref"] in text
    assert '"registry"' in text
    assert '"results"' in text
