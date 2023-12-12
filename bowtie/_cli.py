from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager, suppress
from fnmatch import fnmatch
from functools import wraps
from importlib.resources import files
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, TextIO
import asyncio
import json
import os
import sys
import zipfile

from attrs import asdict
from diagnostic import DiagnosticError
from rich import box, console, panel
from rich.table import Column, Table
from rich.text import Text
from trogon import tui  # type: ignore[reportMissingTypeStubs]
from url import URL, RelativeURLWithoutBase
import aiodocker
import click
import referencing.jsonschema
import referencing_loaders
import rich
import structlog
import structlog.typing

from bowtie import GITHUB, _report
from bowtie._commands import ReportableResult as Result, Seq, Test, TestCase
from bowtie._core import (
    DialectRunner,
    GotStderr,
    Implementation,
    NoSuchImage,
    StartupFailed,
)
from bowtie.exceptions import (
    _ProtocolError,  # type: ignore[reportPrivateUsage]
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping

    from referencing.jsonschema import SchemaRegistry

# Windows fallbacks...
_EX_CONFIG = getattr(os, "EX_CONFIG", 1)
_EX_NOINPUT = getattr(os, "EX_NOINPUT", 1)

IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"
TEST_SUITE_URL = GITHUB / "json-schema-org/JSON-Schema-Test-Suite"

DRAFT2020 = URL.parse("https://json-schema.org/draft/2020-12/schema")
DRAFT2019 = URL.parse("https://json-schema.org/draft/2019-09/schema")
DRAFT7 = URL.parse("http://json-schema.org/draft-07/schema#")
DRAFT6 = URL.parse("http://json-schema.org/draft-06/schema#")
DRAFT4 = URL.parse("http://json-schema.org/draft-04/schema#")
DRAFT3 = URL.parse("http://json-schema.org/draft-03/schema#")

DIALECT_SHORTNAMES: Mapping[str, URL] = {
    "2020": DRAFT2020,
    "202012": DRAFT2020,
    "2020-12": DRAFT2020,
    "draft2020-12": DRAFT2020,
    "draft202012": DRAFT2020,
    "2019": DRAFT2019,
    "201909": DRAFT2019,
    "2019-09": DRAFT2019,
    "draft2019-09": DRAFT2019,
    "draft201909": DRAFT2019,
    "7": DRAFT7,
    "draft7": DRAFT7,
    "6": DRAFT6,
    "draft6": DRAFT6,
    "4": DRAFT4,
    "draft4": DRAFT4,
    "3": DRAFT3,
    "draft3": DRAFT3,
}
TEST_SUITE_DIALECT_URLS = {
    DRAFT2020: TEST_SUITE_URL / "tree/main/tests/draft2020-12",
    DRAFT2019: TEST_SUITE_URL / "tree/main/tests/draft2019-09",
    DRAFT7: TEST_SUITE_URL / "tree/main/tests/draft7",
    DRAFT6: TEST_SUITE_URL / "tree/main/tests/draft6",
    DRAFT4: TEST_SUITE_URL / "tree/main/tests/draft4",
    DRAFT3: TEST_SUITE_URL / "tree/main/tests/draft3",
}
LATEST_DIALECT_NAME = "draft2020-12"

# Magic constants assumed/used by the official test suite
SUITE_REMOTE_BASE_URI = URL.parse("http://localhost:1234")

#: Should match the magic value used to validate `schema`s in `schemas/io.json`
CURRENT_DIALECT_URI = URL.parse("tag:bowtie.report,2023:ihop:__dialect__")

FORMAT = click.option(
    "--format",
    "-f",
    "format",
    help="What format to use for the output",
    default=lambda: "pretty" if sys.stdout.isatty() else "json",
    show_default="pretty if stdout is a tty, otherwise JSON",
    type=click.Choice(["json", "pretty"]),
)
_F = Literal["json", "pretty"]


@tui(help="Open a simple interactive TUI for executing Bowtie commands.")
@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie", package_name="bowtie-json-schema")
def main():
    """
    A meta-validator for the JSON Schema specifications.

    Bowtie gives you access to JSON Schema across every programming
    language and implementation.

    It lets you compare implementations to each other, or to known correct
    results from the JSON Schema test suite.

    If you don't know where to begin, ``bowtie validate`` (for checking what
    any given implementations think of your schema) or ``bowtie suite`` (for
    running the official test suite against implementations) are likely good
    places to start.

    Full documentation can also be found at https://docs.bowtie.report
    """
    _redirect_structlog()


P = ParamSpec("P")


def subcommand(fn: Callable[P, int | None]):
    """
    Define a Bowtie subcommand which returns its exit code.
    """

    @main.command()
    @click.pass_context
    @wraps(fn)
    def run(context: click.Context, *args: P.args, **kwargs: P.kwargs) -> None:
        exit_code = fn(*args, **kwargs)
        context.exit(0 if exit_code is None else exit_code)

    return run


@subcommand
@click.option(
    "--input",
    default="-",
    type=click.File(mode="r"),
)
@click.argument(
    "output",
    default=Path("badges"),
    type=click.Path(path_type=Path),
)
def badges(input: TextIO, output: Path):
    """
    Generate Bowtie badges from a previous run.
    """
    report_data = _report.from_input(input)
    summary = report_data["summary"]
    if summary.is_empty:
        error = DiagnosticError(
            code="empty-report",
            message="The Bowtie report is empty.",
            causes=[f"{input.name} contains no test result data."],
            hint_stmt=(
                "If you are piping data into bowtie badges, "
                "check to ensure that what you've run has succeeded, "
                "otherwise it may be emitting no report data."
            ),
        )
        rich.print(error, file=sys.stderr)
        return _EX_NOINPUT

    try:
        output.mkdir()
    except FileExistsError:
        error = DiagnosticError(
            code="already-exists",
            message="Badge output directory already exists.",
            causes=[f"{output} is an existing directory."],
            hint_stmt=(
                "If you intended to replace its contents with new badges, "
                "delete the directory first."
            ),
        )
        rich.print(error, file=sys.stderr)
        return _EX_NOINPUT

    dialect = report_data["run_info"].dialect
    summary.generate_badges(output, dialect)


@subcommand
@FORMAT
@click.option(
    "--show",
    "-s",
    help="""Configure whether to display validation results
    (whether instances are valid or not) or test failure results
    (whether the validation results match expected validation results)""",
    default="validation",
    show_default=True,
    type=click.Choice(["failures", "validation"]),
)
@click.argument(
    "input",
    default="-",
    type=click.File(mode="r"),
)
def summary(input: TextIO, format: _F, show: str):
    """
    Generate an (in-terminal) summary of a Bowtie run.
    """
    try:
        summary = _report.from_input(input)["summary"]
    except _report.EmptyReport:
        error = DiagnosticError(
            code="empty-report",
            message="The Bowtie report is empty.",
            causes=[f"{input.name} contains no test result data."],
            hint_stmt=(
                "If you are piping data into bowtie summary, "
                "check to ensure that what you've run has succeeded, "
                "otherwise it may be emitting no report data."
            ),
        )
        rich.print(error, file=sys.stderr)
        return _EX_NOINPUT

    if show == "failures":
        results = _ordered_failures(summary)
        to_table = _failure_table

        def to_serializable(
            value: Iterable[tuple[tuple[str, str], _report.Count]],
        ):
            return [(metadata, asdict(counts)) for metadata, counts in value]

    else:
        results = _validation_results(summary)
        to_table = _validation_results_table
        to_serializable = list  # type: ignore[reportGeneralTypeIssues]

    match format:
        case "json":
            click.echo(json.dumps(to_serializable(results), indent=2))  # type: ignore[reportGeneralTypeIssues]
        case "pretty":
            table = to_table(summary, results)  # type: ignore[reportGeneralTypeIssues]
            console.Console().print(table)


def _ordered_failures(
    summary: _report._Summary,  # type: ignore[reportPrivateUsage]
) -> Iterable[tuple[tuple[str, str], _report.Count]]:
    counts = (
        (
            (implementation["name"], implementation["language"]),
            summary.counts[implementation["image"]],
        )
        for implementation in summary.implementations
    )
    return sorted(
        counts,
        key=lambda each: (each[1].unsuccessful_tests, each[0][0]),
    )


def _failure_table(
    summary: _report._Summary,  # type: ignore[reportPrivateUsage]
    results: list[tuple[tuple[str, str], _report.Count]],
):
    test = "tests" if summary.total_tests != 1 else "test"
    table = Table(
        "Implementation",
        "Skips",
        "Errors",
        "Failures",
        title="Bowtie",
        caption=f"{summary.total_tests} {test} ran\n",
    )
    for (implementation, language), counts in results:
        table.add_row(
            Text.assemble(implementation, (f" ({language})", "dim")),
            str(counts.skipped_tests),
            str(counts.errored_tests),
            str(counts.failed_tests),
        )
    return table


def _validation_results(
    summary: _report._Summary,  # type: ignore[reportPrivateUsage]
) -> Iterable[tuple[Any, Iterable[tuple[Any, list[str]]]]]:
    for case, _, case_results in summary.case_results():
        results: list[tuple[Any, list[str]]] = []
        for case_result in case_results:
            descriptions: list[str] = []
            for implementation in summary.implementations:
                valid = case_result[1].get(implementation["image"])
                if valid is None or valid[1] == "errored":
                    description = "error"
                elif valid[1] == "skipped":
                    description = "skipped"
                elif valid[0].valid:
                    description = "valid"
                else:
                    description = "invalid"
                descriptions.append(description)
            results.append((case_result[0]["instance"], descriptions))
        yield case["schema"], results


def _validation_results_table(
    summary: _report._Summary,  # type: ignore[reportPrivateUsage]
    results: Iterable[tuple[Any, Iterable[tuple[Any, dict[str, str]]]]],
):
    test = "tests" if summary.total_tests != 1 else "test"
    table = Table(
        Column(header="Schema", vertical="middle"),
        "",
        title="Bowtie",
        caption=f"{summary.total_tests} {test} ran",
    )

    for schema, case_results in results:
        subtable = Table("Instance", box=box.SIMPLE_HEAD)
        for implementation in summary.implementations:
            subtable.add_column(
                Text.assemble(
                    implementation["name"],
                    (f" ({implementation['language']})", "dim"),
                ),
            )

        for instance, ordered_results in case_results:
            subtable.add_row(json.dumps(instance), *ordered_results)

        table.add_row(json.dumps(schema, indent=2), subtable)
        table.add_section()

    return table


def bowtie_schemas_registry(dialect: URL) -> SchemaRegistry:
    resources = referencing_loaders.from_traversable(files("bowtie.schemas"))
    base = referencing.jsonschema.EMPTY_REGISTRY.with_resources(resources)

    specification = referencing.jsonschema.specification_with(str(dialect))
    return base.with_resource(
        uri=str(CURRENT_DIALECT_URI),
        resource=specification.create_resource({"$ref": str(dialect)}),
    )


def validator_for_dialect(dialect: URL = DRAFT2020):
    from jsonschema.validators import (
        validator_for,  # type: ignore[reportUnknownVariableType]
    )

    registry = bowtie_schemas_registry(dialect=dialect)

    # TODO: Maybe here too there should be an easier way to get an
    #        internally-identified schema under the given specification.
    #        Maybe not though, and it might be safer to just always use
    #        external IDs.

    def validate(instance: Any, schema: referencing.jsonschema.Schema) -> None:
        Validator = validator_for(schema)  # type: ignore[reportUnknownVariableType]
        validator = Validator(schema, registry=registry)  # type: ignore[reportUnknownVariableType]
        errors = list(validator.iter_errors(instance))  # type: ignore[reportUnknownVariableType]
        if errors:
            raise _ProtocolError(errors=errors)  # type: ignore[reportPrivateUsage]

    return validate


def do_not_validate(dialect: URL | None = None) -> Callable[..., None]:
    return lambda *args, **kwargs: None


IMPLEMENTATION = click.option(
    "--implementation",
    "-i",
    "image_names",
    type=lambda name: name if "/" in name else f"{IMAGE_REPOSITORY}/{name}",  # type: ignore[reportUnknownLambdaType]
    help="A docker image which implements the bowtie IO protocol.",
    required=True,
    multiple=True,
)
DIALECT = click.option(
    "--dialect",
    "-D",
    "dialect",
    help=(
        "A URI or shortname identifying the dialect of each test case."
        f"Shortnames include: {sorted(DIALECT_SHORTNAMES)}."
    ),
    type=lambda dialect: (  # type: ignore[reportUnknownLambdaType]
        DIALECT_SHORTNAMES[dialect]  # type: ignore[reportUnknownArgumentType]
        if dialect in DIALECT_SHORTNAMES
        else URL.parse(dialect)  # type: ignore[reportUnknownArgumentType]
    ),
    default=LATEST_DIALECT_NAME,
    show_default=True,
)
FILTER = click.option(
    "-k",
    "filter",
    type=lambda pattern: f"*{pattern}*",  # type: ignore[reportUnknownLambdaType]
    help="Only run cases whose description match the given glob pattern.",
)
FAIL_FAST = click.option(
    "-x",
    "--fail-fast",
    is_flag=True,
    default=False,
    help="Fail immediately after the first error or disagreement.",
)
SET_SCHEMA = click.option(
    "--set-schema/--no-set-schema",
    "-S",
    "set_schema",
    show_default=True,
    default=False,
    help=(
        "Explicitly set $schema in all (non-boolean) case schemas sent to "
        "implementations. Note this of course means what is passed to "
        "implementations will differ from what is provided in the input."
    ),
)
TIMEOUT = click.option(
    "--read-timeout",
    "-T",
    "read_timeout_sec",
    metavar="SECONDS",
    default=2.0,
    show_default=True,
    help=(
        "An explicit timeout to wait for each implementation to respond "
        "to *each* instance being validated. Set this to 0 if you wish "
        "to wait forever, though note that this means you may end up waiting "
        "... forever!"
    ),
)
VALIDATE = click.option(
    "--validate-implementations",
    "-V",
    "make_validator",
    # I have no idea why Click makes this so hard, but no combination of:
    #     type, default, is_flag, flag_value, nargs, ...
    # makes this work without doing it manually with callback.
    callback=lambda _, __, v: validator_for_dialect if v else do_not_validate,  # type: ignore[reportUnknownLambdaType]
    is_flag=True,
    help=(
        "When speaking to implementations (provided via -i), validate "
        "the requests and responses sent to them under Bowtie's JSON Schema "
        "specification. Generally, this option protects against broken Bowtie "
        "implementations and can be left at its default (of off) unless "
        "you are developing a new implementation container."
    ),
)
EXPECT = click.option(
    "--expect",
    show_default=True,
    show_choices=True,
    default="any",
    type=click.Choice(["valid", "invalid", "any"], case_sensitive=False),
    help=(
        "Expect the given input to be considered valid or invalid, "
        "or else (with 'any') to allow either result."
    ),
)


@subcommand
@IMPLEMENTATION
@DIALECT
@FILTER
@FAIL_FAST
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.argument(
    "input",
    default="-",
    type=click.File(mode="rb"),
)
def run(input: Iterable[str], filter: str, dialect: URL, **kwargs: Any):
    """
    Run a sequence of cases provided on standard input.
    """
    cases = (
        TestCase.from_dict(dialect=dialect, **json.loads(line))
        for line in input
    )
    if filter:
        cases = (case for case in cases if fnmatch(case.description, filter))
    return asyncio.run(_run(**kwargs, cases=cases, dialect=dialect))


@subcommand
@IMPLEMENTATION
@DIALECT
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@EXPECT
@click.argument("schema", type=click.File(mode="rb"))
@click.argument("instances", nargs=-1, type=click.File(mode="rb"))
def validate(
    schema: TextIO,
    instances: Iterable[TextIO],
    expect: str,
    **kwargs: Any,
):
    """
    Validate one or more instances under a given schema across implementations.
    """
    case = TestCase(
        description="bowtie validate",
        schema=json.load(schema),
        tests=[
            Test(
                description=str(i),
                instance=json.load(instance),
                valid=dict(valid=True, invalid=False, any=None)[expect],
            )
            for i, instance in enumerate(instances, 1)
        ],
    )
    return asyncio.run(_run(fail_fast=False, **kwargs, cases=[case]))


@subcommand
@FORMAT
@IMPLEMENTATION
def info(**kwargs: Any):
    """
    Retrieve a particular implementation (harness)'s metadata.
    """
    return asyncio.run(_info(**kwargs))


async def _info(image_names: list[str], format: _F):
    exit_code = 0
    async with _start(
        image_names=image_names,
        make_validator=validator_for_dialect,
        reporter=_report.Reporter(),
    ) as starting:
        for each in asyncio.as_completed(starting):
            try:
                implementation = await each
            except NoSuchImage as error:
                exit_code |= _EX_CONFIG
                click.echo(
                    f"❗ (error): {error.name!r} is not a known Bowtie implementation.",  # noqa: E501
                )
                continue

            if implementation.metadata is None:
                exit_code |= _EX_CONFIG
                click.echo("  ❗ (error): startup failed")
                continue

            metadata = dict(
                sorted(
                    implementation.metadata.items(),
                    key=lambda kv: (
                        kv[0] != "name",
                        kv[0] != "language",
                        kv[0] != "version",
                        kv[0] == "dialects",
                        kv[0],
                    ),
                ),
            )

            match format:
                case "json":
                    click.echo(json.dumps(metadata, indent=2))
                case "pretty":
                    click.echo(
                        "\n".join(
                            f"{k}: {json.dumps(v, indent=2)}"
                            for k, v in metadata.items()
                        ),
                    )
    return exit_code


@subcommand
@click.option(
    "-q",
    "--quiet",
    "echo",
    # I have no idea why Click makes this so hard, but no combination of:
    #     type, default, is_flag, flag_value, nargs, ...
    # makes this work without doing it manually with callback.
    callback=lambda _, __, v: click.echo if not v else lambda *_, **__: None,  # type: ignore[reportUnknownLambdaType]
    is_flag=True,
    help="Don't print any output, just exit with nonzero status on failure.",
)
@FORMAT
@IMPLEMENTATION
def smoke(**kwargs: Any):
    """
    Smoke test one or more implementations for basic correctness.
    """
    return asyncio.run(_smoke(**kwargs))


async def _smoke(
    image_names: list[str],
    format: _F,
    echo: Callable[..., None],
):
    reporter = _report.Reporter(write=lambda **_: None)  # type: ignore[reportUnknownArgumentType]
    exit_code = 0

    match format:
        case "json":

            def finish() -> None:
                echo(json.dumps(serializable, indent=2))

        case "pretty":

            def finish():
                if exit_code:
                    echo("\n❌ some failures", file=sys.stderr)
                else:
                    echo("\n✅ all passed", file=sys.stderr)

    async with _start(
        image_names=image_names,
        make_validator=validator_for_dialect,
        reporter=reporter,
    ) as starting:
        for each in asyncio.as_completed(starting):
            try:
                implementation = await each
            except NoSuchImage as error:
                exit_code |= _EX_CONFIG
                echo(
                    f"❗ (error): {error.name!r} is not a known Bowtie implementation.",  # noqa: E501
                    file=sys.stderr,
                )
                continue

            echo(f"Testing {implementation.name!r}...", file=sys.stderr)

            if implementation.metadata is None:
                exit_code |= _EX_CONFIG
                echo("  ❗ (error): startup failed", file=sys.stderr)
                continue

            # FIXME: Sort by newer dialect
            dialect = implementation.dialects[0]
            runner = await implementation.start_speaking(dialect)

            cases = [
                TestCase(
                    description="allow-everything schema",
                    schema={"$schema": str(dialect)},
                    tests=[
                        Test(description="First", instance=1, valid=True),
                        Test(description="Second", instance="foo", valid=True),
                    ],
                ),
                TestCase(
                    description="allow-nothing schema",
                    schema={"$schema": str(dialect), "not": {}},
                    tests=[
                        Test(description="First", instance=12, valid=False),
                    ],
                ),
            ]

            match format:
                case "json":
                    serializable: list[dict[str, Any]] = []

                    def see(seq: Seq, case: TestCase, response: Result):
                        serializable.append(  # noqa: B023
                            {
                                "case": case.without_expected_results(),
                                "response": dict(
                                    errored=response.errored,
                                    failed=response.failed,
                                ),
                            },
                        )

                case "pretty":

                    def see(seq: Seq, case: TestCase, response: Result):
                        if response.errored:
                            message = "❗ (error)"
                            response.report(
                                reporter=reporter.case_started(
                                    seq=seq,
                                    case=case,
                                ),
                            )
                        elif response.failed:
                            message = "✗ (failed)"
                        else:
                            message = "✓"
                        echo(f"  {message}: {case.description}")

            for seq, case in enumerate(cases):
                response = await case.run(seq=seq, runner=runner)
                if response.errored or response.failed:
                    exit_code |= os.EX_DATAERR
                see(seq, case, response)

    finish()
    return exit_code


def path_and_ref_from_gh_path(path: list[str]):
    subpath: list[str] = []
    while path[-1] != "tests":
        subpath.append(path.pop())
    subpath.append(path.pop())
    # remove tree/ or blob/
    return "/".join(reversed(subpath)).rstrip("/"), "/".join(path[1:])


class _TestSuiteCases(click.ParamType):
    name = "json-schema-org/JSON-Schema-Test-Suite test cases"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[Iterable[TestCase], URL, dict[str, Any]]:
        if not isinstance(value, str):
            return value

        # Convert dialect URIs or shortnames to test suite URIs
        value = DIALECT_SHORTNAMES.get(value, value)
        value = TEST_SUITE_DIALECT_URLS.get(value, value)

        try:
            with suppress(TypeError):
                value = URL.parse(value)
        except RelativeURLWithoutBase:
            cases, dialect = self._cases_and_dialect(path=Path(value))
            run_metadata = {}
        else:
            # Sigh. PyCQA/isort#1839
            # isort: off
            from github3 import (  # type: ignore[reportMissingTypeStubs]
                GitHub,
            )
            from github3.exceptions import NotFoundError  # type: ignore[reportMissingTypeStubs]

            # isort: on

            gh = GitHub(token=os.environ.get("GITHUB_TOKEN", ""))
            org, repo_name, *rest = value.path_segments
            repo = gh.repository(org, repo_name)  # type: ignore[reportUnknownMemberType]

            path, ref = path_and_ref_from_gh_path(rest)
            data = BytesIO()
            repo.archive(format="zipball", path=data, ref=ref)  # type: ignore[reportUnknownMemberType]
            data.seek(0)
            with zipfile.ZipFile(data) as zf:
                (contents,) = zipfile.Path(zf).iterdir()
                cases, dialect = self._cases_and_dialect(path=contents / path)
                cases = list(cases)

            try:
                commit = repo.commit(ref)  # type: ignore[reportOptionalMemberAccess]
            except NotFoundError:
                commit_info = ref
            else:
                # TODO: Make this the tree URL maybe, but I see tree(...)
                #       doesn't come with an html_url
                commit_info = {"text": commit.sha, "href": commit.html_url}  # type: ignore[reportOptionalMemberAccess]
            run_metadata: dict[str, Any] = {"Commit": commit_info}

        if dialect is not None:
            return cases, dialect, run_metadata

        self.fail(
            f"{value} does not contain JSON Schema Test Suite cases.",
            param,
            ctx,
        )

    def _cases_and_dialect(self, path: Any):
        if path.name.endswith(".json"):
            paths, version_path = [path], path.parent
        else:
            paths, version_path = _glob(path, "*.json"), path

        remotes = version_path.parent.parent / "remotes"
        dialect = DIALECT_SHORTNAMES.get(version_path.name)
        cases = suite_cases_from(paths=paths, remotes=remotes, dialect=dialect)

        return cases, dialect


@subcommand
@IMPLEMENTATION
@FILTER
@FAIL_FAST
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.argument("input", type=_TestSuiteCases())
def suite(
    input: tuple[Iterable[TestCase], URL, dict[str, Any]],
    filter: str,
    **kwargs: Any,
):
    """
    Run test cases from the official JSON Schema test suite.

    Supports a number of possible inputs:

        * file paths found on the local file system containing tests, e.g.:

            - ``{PATH}/tests/draft7`` to run the draft 7 version's tests out of a local checkout of the test suite

            - ``{PATH}/tests/draft7/foo.json`` to run just one file from a checkout

        * URLs to the test suite repository hosted on GitHub, e.g.:

            - ``https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/``
              to run a version directly from any branch which exists in GitHub

            - ``https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/foo.json``
              to run a single file directly from a branch which exists in GitHub

        * short name versions of the previous URLs (similar to those providable
          to ``bowtie validate`` via its ``--dialect`` option), e.g.:

            - ``7``, to run the draft 7 tests directly from GitHub (as in the
              URL example above)

    """  # noqa: E501
    cases, dialect, metadata = input
    if filter:
        cases = (case for case in cases if fnmatch(case.description, filter))

    task = _run(**kwargs, dialect=dialect, cases=cases, run_metadata=metadata)
    return asyncio.run(task)


async def _run(
    image_names: list[str],
    cases: Iterable[TestCase],
    dialect: URL,
    fail_fast: bool,
    set_schema: bool,
    run_metadata: dict[str, Any] = {},  # noqa: B006
    reporter: _report.Reporter = _report.Reporter(),
    **kwargs: Any,
) -> int:
    exit_code = 0
    acknowledged: list[Implementation] = []
    runners: list[DialectRunner] = []
    async with _start(
        image_names=image_names,
        reporter=reporter,
        **kwargs,
    ) as starting:
        reporter.will_speak(dialect=dialect)
        for each in asyncio.as_completed(starting):
            try:
                implementation = await each
            except StartupFailed as error:
                exit_code = _EX_CONFIG
                reporter.startup_failed(name=error.name, stderr=error.stderr)
                continue
            except NoSuchImage as error:
                exit_code = _EX_CONFIG
                reporter.no_such_image(name=error.name)
                continue

            try:
                if dialect in implementation.dialects:
                    try:
                        runner = await implementation.start_speaking(dialect)
                    except GotStderr as error:
                        exit_code = _EX_CONFIG
                        reporter.dialect_error(
                            implementation=implementation,
                            stderr=error.stderr.decode(),
                        )
                    else:
                        runner.warn_if_unacknowledged(reporter=reporter)
                        acknowledged.append(implementation)
                        runners.append(runner)
                else:
                    reporter.unsupported_dialect(
                        implementation=implementation,
                        dialect=dialect,
                    )
            except StartupFailed as error:
                exit_code = _EX_CONFIG
                reporter.startup_failed(name=error.name, stderr=error.stderr)

        if not runners:
            exit_code = _EX_CONFIG
            reporter.no_implementations()
        else:
            reporter.ready(
                _report.RunInfo.from_implementations(
                    implementations=acknowledged,
                    dialect=dialect,
                    metadata=run_metadata,
                ),
            )

            seq = 0
            should_stop = False
            for seq, case, case_reporter in sequenced(cases, reporter):
                if set_schema and not isinstance(case.schema, bool):
                    case.schema["$schema"] = str(dialect)

                responses = [
                    case.run(seq=seq, runner=runner) for runner in runners
                ]
                for each in asyncio.as_completed(responses):
                    response = await each
                    response.report(reporter=case_reporter)

                    if fail_fast:
                        # Stop after this case, since we still have futures out
                        should_stop = response.errored or response.failed

                if should_stop:
                    break
            reporter.finished(count=seq, did_fail_fast=should_stop)
            if not seq:
                exit_code = os.EX_NOINPUT
    return exit_code


@asynccontextmanager
async def _start(image_names: Iterable[str], **kwargs: Any):
    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())

        yield [
            stack.enter_async_context(
                Implementation.start(
                    docker=docker,
                    image_name=image_name,
                    **kwargs,
                ),
            )
            for image_name in image_names
        ]


def sequenced(
    cases: Iterable[TestCase],
    reporter: _report.Reporter,
) -> Iterable[tuple[int, TestCase, _report.CaseReporter]]:
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)


def _remotes_from(
    path: Path,
    dialect: URL | None,
) -> Iterable[tuple[URL, Any]]:
    for each in _rglob(path, "*.json"):
        schema = json.loads(each.read_text())
        # FIXME: #40: for draft-next support
        schema_dialect = schema.get("$schema")
        if schema_dialect is not None and schema_dialect != str(dialect):
            continue
        relative = str(_relative_to(each, path)).replace("\\", "/")
        yield SUITE_REMOTE_BASE_URI / relative, schema


def suite_cases_from(
    paths: Iterable[_P],
    remotes: Path,
    dialect: URL | None,
) -> Iterable[TestCase]:
    populated = {str(k): v for k, v in _remotes_from(remotes, dialect=dialect)}
    for path in paths:
        if _stem(path) in {"refRemote", "dynamicRef", "vocabulary"}:
            registry = populated
        else:
            registry = {}

        for case in json.loads(path.read_text()):
            for test in case["tests"]:
                test["instance"] = test.pop("data")
            yield TestCase.from_dict(
                dialect=dialect,
                registry=registry,
                **case,
            )


def _stderr_processor(file: TextIO) -> structlog.typing.Processor:
    def stderr_processor(
        logger: structlog.typing.BindableLogger,
        method_name: str,
        event_dict: structlog.typing.EventDict,
    ) -> structlog.typing.EventDict:
        for each in "stderr", "traceback":
            contents = event_dict.pop(each, None)
            if contents is not None:
                implementation = event_dict["logger_name"]
                title = f"[traceback.title]{implementation} [dim]({each})"
                console.Console(file=file, color_system="truecolor").print(
                    panel.Panel(
                        contents.rstrip("\n"),
                        title=title,
                        border_style="traceback.border",
                        expand=True,
                        padding=(1, 4),
                        highlight=True,
                    ),
                )

        return event_dict

    return stderr_processor


def _redirect_structlog(file: TextIO = sys.stderr):
    """
    Reconfigure structlog's defaults to go to the given location.
    """
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(
                fmt="%Y-%m-%d %H:%M.%S",
                utc=False,
            ),
            _stderr_processor(file),
            structlog.dev.ConsoleRenderer(
                colors=getattr(file, "isatty", lambda: False)(),
            ),
        ],
        logger_factory=structlog.PrintLoggerFactory(file),
    )


_P = Path | zipfile.Path


# Missing zipfile.Path methods...
def _glob(path: _P, path_pattern: str) -> Iterable[_P]:
    return (  # It's missing .match() too, so we fnmatch directly
        each for each in path.iterdir() if fnmatch(each.name, path_pattern)
    )


def _rglob(path: _P, path_pattern: str) -> Iterable[_P]:
    for each in path.iterdir():
        if fnmatch(each.name, path_pattern):
            yield each
        elif each.is_dir():
            yield from _rglob(each, path_pattern)


def _relative_to(path: _P, other: Path) -> Path:
    if hasattr(path, "relative_to"):
        return path.relative_to(other)  # type: ignore[reportGeneralTypeIssues]
    return Path(path.at).relative_to(other.at)  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]


def _stem(path: _P) -> str:  # Missing on < 3.11
    if hasattr(path, "stem"):
        return path.stem
    return Path(path.at).stem  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
