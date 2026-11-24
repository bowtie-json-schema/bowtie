"""
Regression tests for reproducing smoke-test reference failures.
"""

import asyncio
import json
import shlex
import sys

import pytest

from bowtie import _smoke
from bowtie._core import Dialect, TestCase


def reference_failure_result():
    """
    Construct a smoke result with the exact case to be replayed.
    """
    dialect = Dialect.by_short_name()["draft7"]
    uri = "http://bowtie.report/cli/smoke/ref-to-string"
    case = TestCase.from_dict(
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

    printer, runner = command.split(" | ", maxsplit=1)
    assert json.loads(shlex.split(printer)[-1]) == case.serializable()
    assert shlex.split(runner) == [
        "bowtie",
        "run",
        "-i",
        "direct:bowtie.tests.miniatures:no_registry_support",
        "--dialect",
        "draft7",
    ]


@pytest.mark.asyncio
@pytest.mark.skipif(sys.platform == "win32", reason="POSIX shell reproducer")
async def test_ref_reproduction_command_runs_the_failed_case():
    result, case = reference_failure_result()
    command = result.ref_reproduction_command()
    assert command is not None
    # Use the active interpreter rather than relying on the console script's PATH.
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
