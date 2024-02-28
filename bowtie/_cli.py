from __future__ import annotations

from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from fnmatch import fnmatch
from functools import cache, wraps
from importlib.resources import files
from pathlib import Path
from pprint import pformat
from typing import TYPE_CHECKING, Literal, ParamSpec, Protocol
import asyncio
import json
import logging
import os
import sys

from aiodocker import Docker
from attrs import asdict
from diagnostic import DiagnosticError
from referencing.jsonschema import EMPTY_REGISTRY
from rich import box, console, panel
from rich.table import Column, Table
from rich.text import Text
from url import URL, RelativeURLWithoutBase
import click
import referencing_loaders
import rich
import structlog
import structlog.typing

from bowtie import _containers, _report, _suite
from bowtie._commands import SeqCase, Unsuccessful
from bowtie._core import (
    Dialect,
    GotStderr,
    Implementation,
    NoSuchImplementation,
    StartupFailed,
    Test,
    TestCase,
)
from bowtie.exceptions import ProtocolError

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Mapping, Sequence
    from typing import Any, TextIO

    from referencing.jsonschema import Schema, SchemaRegistry, SchemaResource

    from bowtie._commands import AnyTestResult, ImplementationId
    from bowtie._core import DialectRunner, ImplementationInfo, MakeValidator

# Windows fallbacks...
_EX_CONFIG = getattr(os, "EX_CONFIG", 1)
_EX_DATAERR = getattr(os, "EX_DATAERR", 1)
_EX_NOINPUT = getattr(os, "EX_NOINPUT", 1)

IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"
LANG_MAP = {
    "cpp": "c++",
    "js": "javascript",
    "ts": "typescript",
}

FORMAT = click.option(
    "--format",
    "-f",
    "format",
    help="What format to use for the output",
    default=lambda: "pretty" if sys.stdout.isatty() else "json",
    show_default="pretty if stdout is a tty, otherwise JSON",
    type=click.Choice(["json", "pretty", "markdown"]),
)
_F = Literal["json", "pretty", "markdown"]


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie", package_name="bowtie-json-schema")
@click.option(
    "--log-level",
    "-L",
    help="How verbose should Bowtie be?",
    default="warning",
    show_default="warning",
    type=click.Choice(
        [
            "debug",
            "info",
            "warning",
            "error",
            "critical",
        ],
    ),
)
def main(log_level: str):
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
    _redirect_structlog(log_level=getattr(logging, log_level.upper()))


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


class ImplementationSubcommand(Protocol):
    def __call__(
        self,
        implementations: Iterable[Implementation],
        **kwargs: Any,
    ) -> Awaitable[int | None]: ...


SILENT = _report.Reporter(write=lambda **_: None)  # type: ignore[reportUnknownArgumentType])


def implementation_subcommand(reporter: _report.Reporter = SILENT):
    """
    Define a Bowtie subcommand which starts up some implementations.

    Runs the wrapped function with only the successfully started
    implementations.
    """

    def wrapper(fn: ImplementationSubcommand):
        @subcommand
        @IMPLEMENTATION()
        @TIMEOUT
        @wraps(fn)
        def cmd(image_names: list[str], **kwargs: Any) -> int:
            return asyncio.run(
                _run_implementations(
                    image_names=image_names,
                    fn=fn,
                    reporter=reporter,
                    **kwargs,
                ),
            )

        return cmd

    return wrapper


def all_implementations_subcommand(reporter: _report.Reporter = SILENT):
    """
    Define a Bowtie subcommand which starts up all implementations.

    Runs the wrapped function with only the successfully started
    implementations.
    """

    def build_images_list(implementations: list[str]) -> list[str]:
        return [f"{IMAGE_REPOSITORY}/{impl}" for impl in implementations]

    def wrapper(fn: ImplementationSubcommand):
        @subcommand
        @TIMEOUT
        @IMPLEMENTATION(required=False)
        @wraps(fn)
        def cmd(image_names: list[str], **kwargs: Any) -> int:
            if not kwargs.get("dialects") and not kwargs.get("languages"):
                raise click.UsageError(
                    "Please provide either '--supports-dialect' filter "
                    "or '--language' filter",
                )
            if sys.stdin.isatty():
                if not image_names:
                    known_implementations = list(Implementation.known())
                    images: list[str] = build_images_list(
                        known_implementations,
                    )
                else:
                    images = image_names
            else:
                implementations = [
                    line.rstrip("/")
                    for line in sys.stdin.read().strip().split("\n")
                ]
                images: list[str] = build_images_list(implementations)
            return asyncio.run(
                _run_implementations(
                    image_names=images,
                    fn=fn,
                    reporter=reporter,
                    **kwargs,
                ),
            )

        return cmd

    return wrapper


@subcommand
@click.option(
    "--site",
    default=Path("site"),
    show_default=True,
    type=click.Path(
        path_type=Path,
        file_okay=False,
        dir_okay=True,
        exists=True,
    ),
    help=(
        "The path to a previously generated collection of reports, "
        "used to generate the badges."
    ),
)
def badges(site: Path):
    """
    Generate Bowtie badges from previous runs.

    Will generate badges for any existing dialects, and ignore any for which a
    report was not generated.
    """
    outdir = site / "badges"
    try:
        outdir.mkdir()
    except FileExistsError:
        error = DiagnosticError(
            code="already-exists",
            message="Badge output directory already exists.",
            causes=[f"{outdir} is an existing directory."],
            hint_stmt=(
                "If you intended to replace its contents with new badges, "
                "delete the directory first."
            ),
        )
        rich.print(error)
        return _EX_CONFIG

    supported_versions: dict[Path, Iterable[Dialect]] = {}

    for name, dialect in Dialect.by_short_name().items():
        try:
            file = site.joinpath(f"{name}.json").open()
        except FileNotFoundError:
            continue
        with file:
            report = _report.Report.from_serialized(file)
            if report.is_empty:
                error = DiagnosticError(
                    code="empty-report",
                    message="A Bowtie report is empty.",
                    causes=[f"The {name} report contains no results."],
                    hint_stmt="Check that site generation has not failed.",
                )
                rich.print(error)
                return _EX_DATAERR

            badge_name = f"{dialect.pretty_name.replace(' ', '_')}.json"

            for each, badge in report.compliance_badges():
                dir = outdir / f"{each.language}-{each.name}"

                compliance = dir / "compliance"
                compliance.mkdir(parents=True, exist_ok=True)
                compliance.joinpath(badge_name).write_text(json.dumps(badge))

                dialects = each.dialects
                seen = supported_versions.setdefault(dir, dialects)
                if seen != dialects:
                    message = (
                        f"{dir.name} appears with different "
                        "supported dialects in the provided reports."
                    )
                    error = DiagnosticError(
                        code="inconsistent-reports",
                        message=message,
                        causes=[
                            f"{file.name} contains:\n{pformat(dialects)}",
                            f"{pformat(seen)} was previously seen.",
                        ],
                        hint_stmt=(
                            "Check that the implementation produces "
                            "consistent output and that a run has not failed."
                        ),
                    )
                    rich.print(error)
                    return _EX_CONFIG

    for dir, dialects in supported_versions.items():
        badge = _report.supported_version_badge(dialects=dialects)
        dir.joinpath("supported_versions.json").write_text(json.dumps(badge))


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
        report = _report.Report.from_serialized(input)
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
    except json.JSONDecodeError as err:
        error = DiagnosticError(
            code="report-not-json",
            message="The Bowtie report looks corrupt.",
            causes=[f"{input.name} is not valid JSON.", str(err)],
            hint_stmt=(
                "If you are piping data, the command producing the report "
                "has likely failed and the real error is above this one. "
                "Otherwise, ensure you are passing in a report generated by "
                "Bowtie."
            ),
        )
        rich.print(error, file=sys.stderr)
        return _EX_DATAERR
    except _report.MissingFooter:
        error = DiagnosticError(
            code="truncated-report",
            message="The Bowtie report looks corrupt.",
            causes=[
                f"{input.name} is missing its footer, which usually means "
                "it has been somehow truncated.",
            ],
            hint_stmt=(
                "Try running the command you used to produce the report, "
                "without piping it. If it crashes, file a bug report!"
            ),
        )
        rich.print(error, file=sys.stderr)
        return _EX_DATAERR

    if show == "failures":
        results = report.worst_to_best()
        to_table = _failure_table
        to_markdown_table = _failure_table_in_markdown

        def to_serializable(  # type: ignore[reportRedeclaration]
            value: Iterable[tuple[ImplementationInfo, Unsuccessful]],
        ):
            return [(each.id, asdict(counts)) for each, counts in value]

    else:
        results = report.cases_with_results()
        to_table = _validation_results_table
        to_markdown_table = _validation_results_table_in_markdown

        def to_serializable(
            value: Iterable[
                tuple[
                    TestCase,
                    Iterable[tuple[Test, dict[str, AnyTestResult]]],
                ]
            ],
        ):
            return [
                (
                    case.schema,
                    [
                        (
                            test.instance,
                            {k: v.description for k, v in test_result.items()},
                        )
                        for test, test_result in test_results
                    ],
                )
                for case, test_results in value
            ]

    match format:
        case "json":
            click.echo(json.dumps(to_serializable(results), indent=2))  # type: ignore[reportGeneralTypeIssues]
        case "pretty":
            table = to_table(report, results)  # type: ignore[reportGeneralTypeIssues]
            console.Console().print(table)
        case "markdown":
            table = to_markdown_table(report, results)  # type: ignore[reportGeneralTypeIssues]
            console.Console().print(table)


def _convert_table_to_markdown(
    columns: list[Any],
    rows: list[list[Any]],
):
    widths = [
        max(len(line[i]) for line in columns) for i in range(len(columns))
    ]
    rows = [[elt.center(w) for elt, w in zip(line, widths)] for line in rows]

    header = "| " + " | ".join(columns) + " |"
    border_left = "|:"
    border_center = ":|:"
    border_right = ":|"

    separator = (
        border_left
        + border_center.join(["-" * w for w in widths])
        + border_right
    )

    # body of the table
    body = [""] * len(rows)  # empty string list that we fill after
    for idx, line in enumerate(rows):
        # for each line, change the body at the correct index
        body[idx] = "| " + " | ".join(line) + " |"
    body = "\n".join(body)

    return "\n\n" + header + "\n" + separator + "\n" + body + "\n\n"


def _failure_table(
    report: _report.Report,
    results: list[tuple[ImplementationInfo, Unsuccessful]],
):
    test = "tests" if report.total_tests != 1 else "test"
    table = Table(
        "Implementation",
        "Skips",
        "Errors",
        "Failures",
        title="Bowtie",
        caption=f"{report.total_tests} {test} ran\n",
    )
    for each, unsuccessful in results:
        table.add_row(
            Text.assemble(each.name, (f" ({each.language})", "dim")),
            str(unsuccessful.skipped),
            str(unsuccessful.errored),
            str(unsuccessful.failed),
        )
    return table


def _failure_table_in_markdown(
    report: _report.Report,
    results: list[tuple[ImplementationInfo, Unsuccessful]],
):
    test = "tests" if report.total_tests != 1 else "test"
    rows: list[list[str]] = []
    columns = [
        "Implementation",
        "Skips",
        "Errors",
        "Failures",
    ]

    for each, unsuccessful in results:
        rows.append(
            [
                f"{each.name} ({each.language})",
                str(unsuccessful.skipped),
                str(unsuccessful.errored),
                str(unsuccessful.failed),
            ],
        )

    markdown_table = _convert_table_to_markdown(columns, rows)
    return (
        "# Bowtie Failures Summary"
        + markdown_table
        + f"**{report.total_tests} {test} ran**\n"
    )


def _validation_results_table(
    report: _report.Report,
    results: Iterable[
        tuple[TestCase, Iterable[tuple[Test, Mapping[str, AnyTestResult]]]],
    ],
):
    test = "tests" if report.total_tests != 1 else "test"
    table = Table(
        Column(header="Schema", vertical="middle"),
        "",
        title="Bowtie",
        caption=f"{report.total_tests} {test} ran",
    )

    # TODO: sort the columns by results?
    implementations = report.implementations

    for case, test_results in results:
        subtable = Table("Instance", box=box.SIMPLE_HEAD)
        for implementation in implementations:
            subtable.add_column(
                Text.assemble(
                    implementation.name,
                    (f" ({implementation.language})", "dim"),
                ),
            )

        for test, test_result in test_results:
            subtable.add_row(
                Text(json.dumps(test.instance)),
                *(
                    Text(test_result[each.id].description)
                    for each in implementations
                ),
            )

        table.add_row(json.dumps(case.schema, indent=2), subtable)
        table.add_section()

    return table


def _validation_results_table_in_markdown(
    report: _report.Report,
    results: Iterable[
        tuple[TestCase, Iterable[tuple[Test, Mapping[str, AnyTestResult]]]],
    ],
):
    rows_data: list[list[str]] = []
    final_content = ""

    inner_table_columns = ["Instance"]
    implementations = report.implementations
    inner_table_columns.extend(
        f"{implementation.name} ({implementation.language})"
        for implementation in implementations
    )

    for case, test_results in results:
        inner_table_rows: list[list[str]] = []
        for test, test_result in test_results:
            inner_table_rows.append(
                [
                    json.dumps(test.instance),
                    *(
                        test_result[each.id].description
                        for each in implementations
                    ),
                ],
            )
        inner_markdown_table = _convert_table_to_markdown(
            inner_table_columns,
            inner_table_rows,
        )
        schema_name = json.dumps(case.schema, indent=2)
        row_data = [schema_name, inner_markdown_table]
        rows_data.append(row_data)

    for idx, row_data in enumerate(rows_data):
        final_content += f"### {idx+1}. Schema:\n {row_data[0]}\n\n"
        final_content += "### Results:"
        final_content += row_data[1]

    return final_content


@cache
def bowtie_schemas_registry() -> SchemaRegistry:
    resources = referencing_loaders.from_traversable(files("bowtie.schemas"))
    return EMPTY_REGISTRY.with_resources(resources).crawl()


def make_validator(*more_schemas: SchemaResource):
    from jsonschema.validators import (
        validator_for,  # type: ignore[reportUnknownVariableType]
    )

    registry = more_schemas @ bowtie_schemas_registry()

    def validate(instance: Any, schema: Schema) -> None:
        Validator = validator_for(schema)  # type: ignore[reportUnknownVariableType]
        # FIXME: There's work to do upstream in referencing, but we still are
        # probably able to make this a bit better here as well
        validator = Validator(schema, registry=registry)  # type: ignore[reportUnknownVariableType]
        errors = list(validator.iter_errors(instance))  # type: ignore[reportUnknownVariableType]
        if errors:
            raise ProtocolError(errors=errors)  # type: ignore[reportPrivateUsage]

    return validate


def do_not_validate(*ignored: SchemaResource) -> Callable[..., None]:
    return lambda *args, **kwargs: None


class _Dialect(click.ParamType):
    """
    Select a JSON Schema dialect.
    """

    name = "dialect"

    def convert(
        self,
        value: str | Dialect,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Dialect:
        if not isinstance(value, str):
            return value

        dialect = Dialect.by_alias().get(value)
        if dialect is not None:
            return dialect

        try:
            url = URL.parse(value)
        except RelativeURLWithoutBase:
            pass
        else:
            dialect = Dialect.by_uri().get(url)
            if dialect is not None:
                return dialect

        self.fail(f"{value!r} is not a known dialect URI or short name.")


CaseTransform = Callable[[Iterable[TestCase]], Iterable[TestCase]]


class _Filter(click.ParamType):
    """
    Filter some test cases by a pattern.
    """

    name = "filter"

    def convert(
        self,
        value: str,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> CaseTransform:
        return lambda cases: (
            case for case in cases if fnmatch(case.description, f"*{value}*")
        )


def _set_schema(dialect: Dialect) -> CaseTransform:
    """
    Explicitly set a dialect on schemas passing through by setting ``$schema``.
    """
    return lambda cases: (c.with_explicit_dialect(dialect) for c in cases)


def _do_nothing(*args: Any, **kwargs: Any) -> CaseTransform:
    return lambda cases: cases


def _set_max_fail_and_max_error(
    ctx: click.Context,
    _,
    value: bool,
) -> None:
    if value:
        if ctx.params.get("max_fail") or ctx.params.get("max_error"):
            ctx.ensure_object(dict)
            ctx.obj["max_fail_or_error_provided"] = True
            return
        ctx.params["max_fail"] = 1
        ctx.params["max_error"] = 1
        ctx.ensure_object(dict)
        ctx.obj["fail_fast_provided"] = True
    return


def _check_fail_fast_provided(
    ctx: click.Context,
    _,
    value: int | None,
) -> int | None:
    if ctx.obj:
        if (
            "fail_fast_provided" in ctx.obj and value is not None
        ) or "max_fail_or_error_provided" in ctx.obj:
            raise click.UsageError(
                "Cannot use --fail-fast with --max-fail / --max-error",
            )
        else:
            return ctx.params["max_fail"] and ctx.params["max_error"]
    return value


def _implementation_option():
    def wrapper(required: bool = True):
        return click.option(
            "--implementation",
            "-i",
            "image_names",
            type=lambda name: (  # type: ignore[reportUnknownLambdaType]
                name if "/" in name else f"{IMAGE_REPOSITORY}/{name}"
            ),
            required=required,
            multiple=True,
            metavar="IMPLEMENTATION",
            help="A docker image which implements the bowtie IO protocol.",
        )

    return wrapper


IMPLEMENTATION = _implementation_option()


def _dialect_option():
    def wrapper(
        param_decls: list[str] = ["--dialect", "-D", "dialect"],
        multiple: bool = False,
        default: Any | None = max(Dialect.known()),
    ):
        return click.option(
            *param_decls,
            type=_Dialect(),
            default=default,
            show_default=True,
            multiple=multiple,
            metavar="URI_OR_NAME",
            help=(
                "A URI or shortname identifying the dialect of each test. "
                "Possible shortnames include: "
                f"{', '.join(sorted(Dialect.by_alias()))}."
            ),
        )

    return wrapper


DIALECT = _dialect_option()


def _get_langs() -> list[str]:
    known_implementations = list(Implementation.known())
    langs: set[str] = set()
    for impl in known_implementations:
        impl_lang = impl.split("-")[0]
        langs.add(LANG_MAP.get(impl_lang, impl_lang))
    return list(langs)


LANGUAGE = click.option(
    "--language",
    "-l",
    "languages",
    help="Filter implementations by programming languages",
    type=click.Choice(_get_langs()),
    multiple=True,
)

FILTER = click.option(
    "-k",
    "filter",
    default="",
    type=_Filter(),
    metavar="GLOB",
    help="Only run cases whose description match the given glob pattern.",
)
FAIL_FAST = click.option(
    "-x",
    "--fail-fast",
    is_flag=True,
    default=False,
    callback=_set_max_fail_and_max_error,
    help="Fail immediately after the first error or disagreement.",
)
MAX_FAIL = click.option(
    "--max-fail",
    type=click.IntRange(min=1),
    callback=_check_fail_fast_provided,
    help="Fail immediately if N tests fail in total across implementations",
)
MAX_ERROR = click.option(
    "--max-error",
    type=click.IntRange(min=1),
    callback=_check_fail_fast_provided,
    help="Fail immediately if N errors occur in total across implementations",
)
SET_SCHEMA = click.option(
    "--set-schema",
    "-S",
    "maybe_set_schema",
    # I have no idea why Click makes this so hard, but no combination of:
    #     type, default, is_flag, flag_value, nargs, ...
    # makes this work without doing it manually with callback.
    callback=lambda _, __, v: _set_schema if v else _do_nothing,  # type: ignore[reportUnknownLambdaType]
    is_flag=True,
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
    default=2.0,
    show_default=True,
    metavar="SECONDS",
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
    callback=lambda _, __, v: make_validator if v else do_not_validate,  # type: ignore[reportUnknownLambdaType]
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
@IMPLEMENTATION()
@DIALECT()
@FILTER
@FAIL_FAST
@MAX_FAIL
@MAX_ERROR
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.argument(
    "input",
    default="-",
    type=click.File(mode="rb"),
)
def run(
    input: Iterable[str],
    filter: CaseTransform,
    dialect: Dialect,
    **kwargs: Any,
):
    """
    Run a sequence of cases provided on standard input.
    """
    cases = filter(
        TestCase.from_dict(dialect=dialect, **json.loads(line))
        for line in input
    )
    return asyncio.run(_run_cases(**kwargs, cases=cases, dialect=dialect))


@subcommand
@IMPLEMENTATION()
@DIALECT()
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
    if not instances:
        return _EX_NOINPUT

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
    return asyncio.run(_run_cases(fail_fast=False, **kwargs, cases=[case]))


@all_implementations_subcommand()  # type: ignore[reportArgumentType]
@DIALECT(
    param_decls=["--supports-dialect", "-D", "dialects"],
    default=None,
    multiple=True,
)
@LANGUAGE
async def filter_implementations(
    implementations: Iterable[Implementation],
    dialects: Iterable[Dialect] | None,
    languages: list[str] | None,
):
    supporting_implementations: list[str] = []
    dialect_uris = []
    if dialects:
        dialect_uris = [(str(d.uri) for d in dialects)]

    for each in implementations:
        metadata = each.info.serializable()
        implementaion = each.info.id

        if (
            "dialects" in metadata
            and (
                not dialects
                or all(uri in metadata["dialects"] for uri in dialect_uris)
            )
            and (
                not languages
                or any(lang == each.info.language for lang in languages)
            )
        ):
            supporting_implementations.append(implementaion)

    for impl in supporting_implementations:
        click.echo(impl)


@implementation_subcommand()  # type: ignore[reportArgumentType]
@FORMAT
async def info(implementations: Sequence[Implementation], format: _F):
    """
    Retrieve a particular implementation (harness)'s metadata.
    """
    serializable: dict[ImplementationId, dict[str, Any]] = {}

    for each in implementations:
        metadata = [(k, v) for k, v in each.info.serializable().items() if v]
        metadata.sort(
            key=lambda kv: (
                kv[0] != "name",
                kv[0] != "language",
                kv[0] != "version",
                kv[0] == "links",
                kv[0] == "dialects",
                kv[0],
            ),
        )

        match format:
            case "json":
                serializable[each.name] = dict(metadata)
            case "pretty":
                click.echo(
                    "\n".join(
                        f"{k}: {json.dumps(v, indent=2)}" for k, v in metadata
                    ),
                )
            case "markdown":
                click.echo(
                    "\n".join(
                        f"**{k}**: {json.dumps(v, indent=2)}"
                        for k, v in metadata
                    ),
                )

    if format == "json":
        if len(serializable) == 1:
            (output,) = serializable.values()
        else:
            output = serializable
        click.echo(json.dumps(output, indent=2))


@implementation_subcommand()  # type: ignore[reportArgumentType]
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
async def smoke(
    implementations: Iterable[Implementation],
    format: _F,
    echo: Callable[..., None],
) -> int:
    """
    Smoke test one or more implementations for basic correctness.
    """
    exit_code = 0

    for implementation in implementations:
        echo(f"Testing {implementation.name!r}...\n", file=sys.stderr)
        serializable: list[dict[str, Any]] = []
        implementation_exit_code = 0

        async for _, results in implementation.smoke():
            async for case, result in results:
                if result.unsuccessful():
                    implementation_exit_code |= _EX_DATAERR

                match format:
                    case "json":
                        serializable.append(
                            dict(
                                case=case.without_expected_results(),
                                result=asdict(result.result),
                            ),
                        )

                    case "pretty":
                        echo(f"  · {case.description}: {result.dots()}")

                    case "markdown":
                        echo(f"* {case.description}: {result.dots()}")

        match format:
            case "json":
                echo(json.dumps(serializable, indent=2))

            case "pretty":
                message = (
                    "❌ some failures"
                    if implementation_exit_code
                    else "✅ all passed"
                )
                echo(f"\n{message}", file=sys.stderr)

            case "markdown":
                message = (
                    "**❌ some failures**"
                    if implementation_exit_code
                    else "**✅ all passed**"
                )
                echo(f"\n{message}", file=sys.stderr)

        exit_code |= implementation_exit_code

    return exit_code


@subcommand
@IMPLEMENTATION()
@FILTER
@FAIL_FAST
@MAX_FAIL
@MAX_ERROR
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.argument("input", type=_suite.ClickParam())
def suite(
    input: tuple[Iterable[TestCase], Dialect, dict[str, Any]],
    filter: CaseTransform,
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
          to `bowtie validate --dialect`, e.g.:

            - ``7``, to run the draft 7 tests directly from GitHub (as in the
              URL example above)

    """  # noqa: E501
    _cases, dialect, metadata = input
    cases = filter(_cases)
    task = _run_cases(
        **kwargs,
        dialect=dialect,
        cases=cases,
        run_metadata=metadata,
    )
    return asyncio.run(task)


async def _run_implementations(
    image_names: list[str],
    read_timeout_sec: float,
    fn: ImplementationSubcommand,
    reporter: _report.Reporter = SILENT,
    make_validator: MakeValidator = make_validator,
    **kw: Any,
) -> int:
    exit_code = 0
    start = _start(
        image_names=image_names,
        make_validator=make_validator,
        reporter=reporter,
        read_timeout_sec=read_timeout_sec,
    )

    running: list[Implementation] = []
    async with start as implementations:
        for each in implementations:  # FIXME: respect --quiet
            try:
                implementation = await each
            except StartupFailed as err:
                exit_code |= _EX_CONFIG
                stderr = panel.Panel(err.stderr, title="stderr")
                rich.print(err.diagnostic(), stderr, file=sys.stderr)
                continue
            except NoSuchImplementation as err:
                exit_code |= _EX_CONFIG
                rich.print(err.diagnostic(), file=sys.stderr)
                continue

            running.append(implementation)

        if running:
            exit_code |= await fn(implementations=running, **kw) or 0
        else:
            exit_code |= _EX_CONFIG

    return exit_code


async def _run_cases(
    image_names: list[str],
    cases: Iterable[TestCase],
    dialect: Dialect,
    fail_fast: bool,
    maybe_set_schema: Callable[[Dialect], CaseTransform],
    max_fail: int | None = None,
    max_error: int | None = None,
    run_metadata: dict[str, Any] = {},
    reporter: _report.Reporter = _report.Reporter(),
    **kwargs: Any,
) -> int:
    exit_code = 0
    acknowledged: list[ImplementationInfo] = []
    runners: list[DialectRunner] = []
    async with _start(
        image_names=image_names,
        reporter=reporter,
        **kwargs,
    ) as starting:
        reporter.will_speak(dialect=dialect)
        for each in starting:
            try:
                implementation = await each
            except StartupFailed as error:
                exit_code = _EX_CONFIG
                reporter.startup_failed(name=error.name, stderr=error.stderr)
                continue
            except NoSuchImplementation as error:
                exit_code = _EX_CONFIG
                reporter.no_such_image(name=error.name)
                continue

            if dialect in implementation.info.dialects:
                try:
                    runner = await implementation.start_speaking(dialect)
                except GotStderr as error:
                    exit_code = _EX_CONFIG
                    reporter.dialect_error(
                        implementation=implementation,
                        stderr=error.stderr.decode(),
                    )
                else:
                    acknowledged.append(implementation.info)
                    runners.append(runner)
            else:
                reporter.unsupported_dialect(
                    implementation=implementation,
                    dialect=dialect,
                )

        if not runners:
            exit_code = _EX_CONFIG
            reporter.no_implementations()
        else:
            reporter.ready(
                _report.RunMetadata(
                    implementations=acknowledged,
                    dialect=dialect,
                    metadata=run_metadata,
                ),
            )

            count = 0
            should_stop = False
            unsucessful = Unsuccessful()
            for count, case in enumerate(maybe_set_schema(dialect)(cases), 1):
                seq_case = SeqCase(seq=count, case=case)
                case_reporter = reporter.case_started(seq_case)

                responses = [seq_case.run(runner=runner) for runner in runners]
                for each in asyncio.as_completed(responses):
                    result = await each
                    case_reporter.got_result(result=result)
                    unsucessful += result.unsuccessful()
                    if max_fail and unsucessful.failed == max_fail:
                        should_stop = True
                    if max_error and unsucessful.errored == max_error:
                        should_stop = True

                if should_stop:
                    reporter.failed_fast(seq_case=seq_case)
                    break
            reporter.finished(count=count, did_fail_fast=should_stop)
            if not count:
                exit_code = _EX_NOINPUT
    return exit_code


@asynccontextmanager
async def _start(
    image_names: Iterable[str],
    make_validator: MakeValidator,
    read_timeout_sec: float,
    **kwargs: Any,
):
    @asynccontextmanager
    async def _client(
        docker: Docker,
        image_name: str,
    ) -> AsyncIterator[Implementation]:
        async with (
            _containers.Connection.open(
                docker=docker,
                image_name=image_name,
                read_timeout_sec=read_timeout_sec,
            ) as connection,
            Implementation.start(
                id=image_name,
                connection=connection,
                make_validator=make_validator,
                **kwargs,
            ) as implementation,
        ):
            yield implementation

    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(Docker())

        implementations = [
            stack.enter_async_context(_client(docker=docker, image_name=name))
            for name in image_names
        ]
        yield asyncio.as_completed(implementations)


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


def _redirect_structlog(log_level: int, file: TextIO = sys.stderr):
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
        logger_factory=structlog.WriteLoggerFactory(file),
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
    )
