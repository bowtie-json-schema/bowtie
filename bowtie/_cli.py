from __future__ import annotations

from collections.abc import Callable, Iterable, ValuesView
from contextlib import AsyncExitStack, asynccontextmanager
from fnmatch import fnmatch
from functools import wraps
from pathlib import Path
from pprint import pformat
from statistics import mean, median, quantiles
from textwrap import dedent
from typing import TYPE_CHECKING, Literal, ParamSpec, Protocol
import asyncio
import json
import logging
import os
import sys

from attrs import asdict
from click.shell_completion import CompletionItem
from diagnostic import DiagnosticError
from jsonschema_lexer import JSONSchemaLexer
from pygments.lexers.data import (  # type: ignore[reportMissingTypeStubs]
    JsonLexer,
)
from rich import box, console, panel
from rich.syntax import Syntax
from rich.table import Column, Table
from rich.text import Text
from rich_click.utils import CommandGroupDict, OptionGroupDict
from url import URL, RelativeURLWithoutBase
import rich_click as click
import structlog
import structlog.typing

from bowtie import _connectables, _report, _suite
from bowtie._commands import SeqCase, Unsuccessful
from bowtie._core import (
    Dialect,
    Example,
    Implementation,
    NoSuchImplementation,
    StartupFailed,
    Test,
    TestCase,
    validator_registry,
)
from bowtie.exceptions import DialectError, ProtocolError, UnsupportedDialect

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Mapping,
        Sequence,
        Set,
    )
    from os import PathLike
    from typing import IO, Any, TextIO

    from click.decorators import FC
    from referencing.jsonschema import Schema, SchemaResource

    from bowtie._commands import AnyTestResult
    from bowtie._connectables import ConnectableId
    from bowtie._core import DialectRunner, ImplementationInfo, MakeValidator


class _EX:
    def __getattr__(self, attr: str) -> int:
        return getattr(os, f"EX_{attr}", 1)  # Windows fallbacks...


EX = _EX()

STDERR = console.Console(stderr=True)


# rich-click's CommandGroupDict seems to be missing some covariance, as using a
# regular dict here makes pyright complain.
_COMMAND_GROUPS = dict(
    bowtie=[
        CommandGroupDict(
            name="Basic Commands",
            commands=["validate", "suite", "summary", "info"],
        ),
        CommandGroupDict(
            name="Advanced Usage",
            commands=["filter-dialects", "filter-implementations", "run"],
        ),
        CommandGroupDict(
            name="Plumbing Commands",
            commands=["badges", "smoke"],
        ),
    ],
)
_OPTION_GROUPS = {
    f"bowtie {command}": [
        *[
            OptionGroupDict(name=group, options=[f"--{o}" for o in options])
            for group, options in groups
        ],
        OptionGroupDict(
            name="Connection & Communication Options",
            options=["--read-timeout", "--validate-implementations"],
        ),
        OptionGroupDict(name="Help", options=["--help"]),
    ]
    for command, groups in [
        (
            "validate",
            [
                ("Required", ["implementation"]),
                ("Schema Behavior Options", ["dialect", "set-schema"]),
                ("Validation Metadata Options", ["description", "expect"]),
            ],
        ),
        (
            "suite",
            [
                ("Required", ["implementation"]),
                (
                    "Test Run Options",
                    ["fail-fast", "filter", "max-error", "max-fail"],
                ),
                ("Test Modification Options", ["set-schema"]),
            ],
        ),
        ("info", [("Basic Options", ["implementation", "format"])]),
        ("smoke", [("Basic Options", ["implementation", "quiet", "format"])]),
        (
            "filter-dialects",
            [
                ("Required", ["implementation"]),
                ("Filters", ["dialect", "latest", "boolean-schemas"]),
            ],
        ),
        (
            "filter-implementations",
            [
                ("Required", ["implementation"]),
                ("Filters", ["supports-dialect", "language"]),
            ],
        ),
        (
            "run",
            [
                ("Required", ["implementation"]),
                ("Schema Behavior Options", ["dialect", "set-schema"]),
                (
                    "Test Run Options",
                    ["fail-fast", "filter", "max-error", "max-fail"],
                ),
            ],
        ),
    ]
}


@click.rich_config(
    help_config=click.RichHelpConfiguration(
        command_groups=_COMMAND_GROUPS,
        option_groups=_OPTION_GROUPS,
        style_commands_table_column_width_ratio=(1, 3),
        # Otherwise there's an uncomfortable amount of internal whitespace.
        max_width=120,
    ),
)
@click.group(
    context_settings=dict(help_option_names=["--help", "-h"]),
    # needing to explicitly dedent here, as well as the extra newline
    # before "Full documentation" both seem like rich-click bugs.
    epilog=dedent(
        """
        If you don't know where to begin, `bowtie validate --help` or
        `bowtie suite --help` are likely good places to start.

        Full documentation can also be found at https://docs.bowtie.report
        """,
    ),
)
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

    Bowtie gives you access to the JSON Schema ecosystem across every
    programming language and implementation.

    It lets you compare implementations either to each other or to known
    correct results from the official JSON Schema test suite.
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
        start: Callable[
            [],
            AsyncIterator[tuple[ConnectableId, Implementation]],
        ],
        **kwargs: Any,
    ) -> Awaitable[int | None]: ...


SILENT = _report.Reporter(write=lambda **_: None)  # type: ignore[reportUnknownArgumentType])


def implementation_subcommand(
    reporter: _report.Reporter = SILENT,
    default_implementations: Set[str] = Implementation.known(),
):
    """
    Define a Bowtie subcommand which starts up some implementations.

    Runs the wrapped function with only the successfully started
    implementations.
    """

    def wrapper(fn: ImplementationSubcommand):
        async def run(
            connectables: Iterable[_connectables.Connectable],
            read_timeout_sec: float,
            make_validator: MakeValidator = make_validator,
            **kw: Any,
        ) -> int:
            exit_code = 0

            async def start():
                nonlocal exit_code

                successful = 0
                async with _start(
                    connectables=connectables,
                    make_validator=make_validator,
                    reporter=reporter,
                    read_timeout_sec=read_timeout_sec,
                ) as implementations:
                    for each in implementations:  # FIXME: respect --quiet
                        try:
                            connectable_implementation = await each
                        except (NoSuchImplementation, StartupFailed) as error:
                            exit_code |= EX.CONFIG
                            STDERR.print(error)
                            continue

                        successful += 1
                        yield connectable_implementation

                    if not successful and default_implementations:
                        # TODO: show a diagnostic that collects crash causes
                        exit_code |= EX.CONFIG
                        return

            # FIXME: Convert this to an instance presumably, but for now we
            #        just want this data available in the functions,
            #        and introducing another type is annoying when most of the
            #        complexity has to do with _run / _start still existing --
            #        we need to finish removing them.
            start.connectables = [each.to_terse() for each in connectables]  # type: ignore[reportFunctionMemberAccess]

            fn_exit_code = await fn(start=start, **kw)
            return exit_code | (fn_exit_code or 0)

        @subcommand
        @click.option(
            "--implementation",
            "-i",
            "connectables",
            type=_connectables.ClickParam(),
            default=lambda: (
                default_implementations
                if sys.stdin.isatty() or "CI" in os.environ
                else [line.strip() for line in sys.stdin]
            ),
            multiple=True,
            metavar="IMPLEMENTATION",
            help=(
                "A connectable ID for a JSON Schema implementation supported "
                "by Bowtie. May be repeated multiple times to select multiple "
                "implementations to run."
                "Run `bowtie filter-implementations` for the full list of "
                "supported implementations."
            ),
        )
        @TIMEOUT
        @wraps(fn)
        def cmd(
            connectables: Iterable[_connectables.Connectable],
            **kwargs: Any,
        ) -> int:
            return asyncio.run(run(connectables=connectables, **kwargs))

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
    Generate Bowtie badges for implementations using a previous Bowtie run.

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
        STDERR.print(error)
        return EX.CONFIG

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
                STDERR.print(error)
                return EX.DATAERR

            badge_name = f"{dialect.short_name}.json"

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
                    STDERR.print(error)
                    return EX.CONFIG

    for dir, dialects in supported_versions.items():
        badge = _report.supported_version_badge(dialects=dialects)
        dir.joinpath("supported_versions.json").write_text(json.dumps(badge))


_F = Literal["json", "pretty", "markdown"]


def format_option(**option_kwargs: Any) -> Callable[[FC], FC]:
    if not option_kwargs:
        option_kwargs = dict(
            default=lambda: "pretty" if sys.stdout.isatty() else "json",
            show_default="pretty if stdout is a tty, otherwise JSON",
            type=click.Choice(["json", "pretty", "markdown"]),
        )

    def _format_option(fn: FC) -> FC:
        def show_schema(
            ctx: click.Context,
            param: click.Parameter | None,
            value: bool,
        ) -> None:
            if not value or ctx.resilient_parsing:
                return
            uri = f"tag:bowtie.report,2024:cli:{ctx.command.name}"
            schema = validator_registry().schema(uri)
            # FIXME: Syntax highlight? But rich appears to be doing some
            #        bizarre line wrapping, even if I disable a bunch of random
            #        options (crop, no_wrap, word_wrap in Syntax, ...) which
            #        fails the integration tests.
            click.echo(json.dumps(schema, indent=2))
            ctx.exit()

        return click.option(
            "--format",
            "-f",
            "format",
            help="What format to use for the output",
            **option_kwargs,
        )(
            click.option(
                "--schema",
                callback=show_schema,
                expose_value=False,
                is_eager=True,
                is_flag=True,
                help="Show the JSON Schema for this command's JSON output.",
            )(fn),
        )

    return _format_option


class _Report(click.File):
    """
    Select a previously produced Bowtie report.
    """

    name = "report"
    mode = "r"

    def convert(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        value: str | PathLike[str] | IO[Any] | _report.Report,
        param: click.Parameter | None,
        ctx: click.Context,
    ) -> _report.Report:
        if isinstance(value, _report.Report):
            return value

        input = super().convert(value, param, ctx)
        try:
            return _report.Report.from_serialized(input)
        except _report.EmptyReport:
            error = DiagnosticError(
                code="empty-report",
                message="The Bowtie report is empty.",
                causes=[f"{input.name} contains no test result data."],
                hint_stmt=(
                    "If you are piping in report data, "
                    "check to ensure that what you've run has succeeded, "
                    "otherwise it may be emitting no report data."
                ),
            )
            STDERR.print(error)
            ctx.exit(EX.NOINPUT)
        except json.JSONDecodeError as err:
            error = DiagnosticError(
                code="report-not-json",
                message="The Bowtie report looks corrupt.",
                causes=[f"{input.name} is not valid JSON.", str(err)],
                hint_stmt=(
                    "If you are piping in report data, "
                    "the command producing the report has likely failed "
                    "and the real error is above this one. "
                    "Otherwise, ensure you are passing in a report generated "
                    "by Bowtie."
                ),
            )
            STDERR.print(error)
            ctx.exit(EX.DATAERR)
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
            STDERR.print(error)
            ctx.exit(EX.DATAERR)


@subcommand
@format_option()
@click.option(
    "--show",
    "-s",
    default="validation",
    show_default=True,
    type=click.Choice(["failures", "validation"]),
    help=(
        "Configure whether to display validation results "
        "(whether instances are valid or not) or test failure results "
        "(whether the validation results match expected validation results)"
    ),
)
@click.argument("report", default="-", type=_Report())
def summary(report: _report.Report, format: _F, show: str):
    """
    Generate an (in-terminal) summary of a Bowtie run.
    """
    if show == "failures":
        results = report.worst_to_best()
        to_table = _failure_table
        to_markdown_table = _failure_table_in_markdown

        def to_serializable(  # type: ignore[reportRedeclaration]
            value: Iterable[
                tuple[ConnectableId, ImplementationInfo, Unsuccessful],
            ],
        ):
            return [(id, asdict(counts)) for id, _, counts in value]

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


def _convert_table_to_markdown(columns: list[str], rows: list[list[str]]):
    widths = [max(len(row[i]) for row in rows) for i in range(len(columns))]
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

    return f"\n{header}\n{separator}\n{body}"


def _failure_table(
    report: _report.Report,
    results: list[tuple[ConnectableId, ImplementationInfo, Unsuccessful]],
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
    for _, each, unsuccessful in results:
        table.add_row(
            Text.assemble(each.name, (f" ({each.language})", "dim")),
            str(unsuccessful.skipped),
            str(unsuccessful.errored),
            str(unsuccessful.failed),
        )
    return table


def _failure_table_in_markdown(
    report: _report.Report,
    results: list[tuple[ConnectableId, ImplementationInfo, Unsuccessful]],
):
    test = "tests" if report.total_tests != 1 else "test"
    rows: list[list[str]] = []
    columns = [
        "Implementation",
        "Skips",
        "Errors",
        "Failures",
    ]

    for _, each, unsuccessful in results:
        rows.append(
            [
                f"{each.name} ({each.language})",
                str(unsuccessful.skipped),
                str(unsuccessful.errored),
                str(unsuccessful.failed),
            ],
        )

    return "\n".join(
        [
            "# Bowtie Failures Summary",
            _convert_table_to_markdown(columns, rows),
            "",
            f"**{report.total_tests} {test} ran**",
        ],
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
        for implementation in implementations.values():
            subtable.add_column(
                Text.assemble(
                    implementation.name,
                    (f" ({implementation.language})", "dim"),
                ),
            )

        for test, test_result in test_results:
            subtable.add_row(
                Syntax(
                    json.dumps(test.instance),
                    lexer=JsonLexer(),
                    background_color="default",
                    word_wrap=True,
                ),
                *(Text(test_result[id].description) for id in implementations),
            )

        table.add_row(
            Syntax(
                json.dumps(case.schema, indent=2),
                lexer=JSONSchemaLexer(str(report.metadata.dialect.uri)),
                background_color="default",
                word_wrap=True,
            ),
            subtable,
        )
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
        f"{id} ({implementation.language})"
        for id, implementation in implementations.items()
    )

    for case, test_results in results:
        inner_table_rows: list[list[str]] = []
        for test, test_result in test_results:
            inner_table_rows.append(
                [
                    json.dumps(test.instance),
                    *(test_result[id].description for id in implementations),
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


def make_validator():
    validators = validator_registry()

    def validate(instance: Any, schema: Schema) -> None:
        # FIXME: There's work to do upstream in referencing, but we still are
        # probably able to make this a bit better here as well
        validator = validators.for_schema(schema)
        errors = list(validator.errors_for(instance))
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

    def shell_complete(
        self,
        ctx: click.Context,
        param: click.Parameter,
        incomplete: str,
    ) -> list[CompletionItem]:
        if incomplete:  # the user typed something, so filter over everything
            suggestions = [
                (field, dialect)
                for dialect in Dialect.known()
                for field in [
                    str(dialect.uri),
                    dialect.short_name,
                    *dialect.aliases,
                ]
            ]
            suggestions = [(str(u), d) for u, d in Dialect.by_uri().items()]
        else:  # the user didn't type anything, only suggest short names
            suggestions = Dialect.by_short_name().items()

        return [
            # FIXME: pallets/click#2703
            CompletionItem(
                value=value.replace(":", "\\:"),
                help=f"the {dialect.pretty_name} dialect",
            )
            for value, dialect in suggestions
            if value.startswith(incomplete.lower())
        ]


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


def _set_dialect(ctx: click.Context, _, value: _Dialect):
    """
    Set the dialect according to a possibly present :kw:`$schema` keyword.
    """
    if value:
        return value
    schema = ctx.params.get("schema")
    dialect_from_schema: str | None = (  # type: ignore[reportUnknownVariableType]
        schema.get("$schema")  # type: ignore[reportUnknownMemberType]
        if isinstance(schema, dict)
        else None
    )
    return (
        Dialect.from_str(dialect_from_schema)  # type: ignore[reportUnknownArgumentType]
        if dialect_from_schema
        else max(Dialect.known())
    )


def _set_schema(dialect: Dialect) -> CaseTransform:
    """
    Explicitly set a dialect on schemas passing through by setting ``$schema``.
    """
    return lambda cases: (c.with_explicit_dialect(dialect) for c in cases)


def _do_nothing(*args: Any, **kwargs: Any) -> CaseTransform:
    return lambda cases: cases


IMPLEMENTATION = click.option(
    "--implementation",
    "-i",
    "connectables",
    type=_connectables.ClickParam(),
    required=True,
    multiple=True,
    metavar="IMPLEMENTATION",
    help=(
        "A connectable ID for a JSON Schema implementation supported "
        "by Bowtie. May be repeated multiple times to select multiple "
        "implementations to run."
        "Run `bowtie filter-implementations` for the full list of "
        "supported implementations."
    ),
)
DIALECT = click.option(
    "--dialect",
    "-D",
    "dialect",
    type=_Dialect(),
    callback=_set_dialect,
    show_default=True,
    metavar="URI_OR_NAME",
    help=(
        "A URI or shortname identifying the dialect of each test. Possible "
        f"shortnames include: {', '.join(sorted(Dialect.by_alias()))}."
    ),
)
FILTER = click.option(
    "--filter",
    "-k",
    default="",
    type=_Filter(),
    metavar="GLOB",
    help="Only run cases whose description match the given glob pattern.",
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


def fail_fast(fn: FC) -> FC:
    conflict = "don't provide both --fail-fast and --max-fail / --max-error"

    # Both are these are needed because parsing is order dependent :/
    def disallow_fail_fast(
        ctx: click.Context,
        _,
        value: int | None,
    ) -> int | None:
        if ctx.params.get("fail_fast"):
            if value is None:
                return 1
            raise click.UsageError(conflict)
        return value

    def disallow_max_fail(
        ctx: click.Context,
        _,
        value: int | None,
    ) -> int | None:
        if value and ctx.params.get("max_fail", 1) != 1:
            raise click.UsageError(conflict)
        return value

    N = "COUNT"
    msg = f"Stop running once {N} tests {{}} in total across implementations."
    return click.option(
        "-x",
        "--fail-fast",
        callback=disallow_max_fail,
        is_flag=True,
        default=False,
        help="Stop running immediately after the first failure or error.",
    )(
        click.option(
            "--max-fail",
            metavar=N,
            type=click.IntRange(min=1),
            callback=disallow_fail_fast,
            help=msg.format("fail"),
        )(
            click.option(
                "--max-error",
                metavar=N,
                type=click.IntRange(min=1),
                callback=disallow_fail_fast,
                help=msg.format("error"),
            )(fn),
        ),
    )


class JSON(click.File):

    name = "JSON"

    def convert(
        self,
        value: str | PathLike[str] | IO[Any],
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Any:
        return json.load(super().convert(value, param, ctx))


@subcommand
@IMPLEMENTATION
@DIALECT
@FILTER
@fail_fast
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
    Run test cases written directly in Bowtie's testing format.

    This is generally useful if you wish to hand-author which schemas to
    include in the schema registry, or otherwise exactly control the contents
    of a test case.
    """
    cases = filter(
        TestCase.from_dict(dialect=dialect, **json.loads(line))
        for line in input
    )
    return asyncio.run(_run(**kwargs, cases=cases, dialect=dialect))


@subcommand
@IMPLEMENTATION
@DIALECT
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.option(
    "-d",
    "--description",
    default="bowtie validate",
    help="A (human-readable) description for this test case.",
)
@click.option(
    "--expect",
    show_default=True,
    show_choices=True,
    default="any",
    type=click.Choice(["valid", "invalid", "any"], case_sensitive=False),
    callback=lambda _, __, value: (  # type: ignore[reportUnknownLambdaType]
        None if value == "any" else value == "valid"
    ),
    help=(
        "Expect the given input to be considered valid or invalid, "
        "or else (with 'any') to allow either result."
    ),
)
@click.argument("schema", type=JSON())
@click.argument("instances", nargs=-1, type=JSON())
def validate(
    schema: Any,
    instances: Iterable[Any],
    expect: bool | None,
    description: str,
    **kwargs: Any,
):
    """
    Validate instances under a schema across any supported implementation.
    """
    if not instances:
        return EX.NOINPUT

    tests = [Example(description="", instance=each) for each in instances]
    if expect is not None:
        tests = [test.expect(expect) for test in tests]
    case = TestCase(description=description, schema=schema, tests=tests)
    return asyncio.run(_run(fail_fast=False, **kwargs, cases=[case]))


LANGUAGE_ALIASES = {
    "cpp": "c++",
    "js": "javascript",
    "ts": "typescript",
}
KNOWN_LANGUAGES = {
    *LANGUAGE_ALIASES.values(),
    *(i.partition("-")[0] for i in Implementation.known()),
}


@implementation_subcommand()  # type: ignore[reportArgumentType]
@format_option(
    default="plain",
    show_default=True,
    type=click.Choice(["plain", "json"]),
)
@click.option(
    "--supports-dialect",
    "-d",
    "dialects",
    type=_Dialect(),
    default=frozenset(),
    metavar="URI_OR_NAME",
    multiple=True,
    help=(
        "Only include implementations supporting the given dialect or dialect "
        "short name."
    ),
)
@click.option(
    "--language",
    "-l",
    "languages",
    type=click.Choice(sorted(KNOWN_LANGUAGES), case_sensitive=False),
    callback=lambda _, __, value: (  # type: ignore[reportUnknownLambdaType]
        KNOWN_LANGUAGES
        if not value
        else frozenset(
            LANGUAGE_ALIASES.get(each, each)  # type: ignore[reportUnknownArgumentType]
            for each in value  # type: ignore[reportUnknownArgumentType]
        )
    ),
    multiple=True,
    metavar="LANGUAGE",
    help="Only include implementations in the given programming language",
)
async def filter_implementations(
    start: Callable[
        [],
        AsyncIterator[tuple[ConnectableId, Implementation]],
    ],
    dialects: Sequence[Dialect],
    languages: Set[str],
    format: Literal["plain", "json"],
):
    """
    Output implementations which match the given criteria.

    Useful for piping or otherwise using the resulting output for further
    Bowtie commands.
    """
    if not dialects and languages == KNOWN_LANGUAGES:
        matching = start.connectables  # type: ignore[reportFunctionMemberAccess]
    else:
        matching = [
            name
            async for name, each in start()
            if each.supports(*dialects) and each.info.language in languages
        ]

    match format:
        case "json":
            click.echo(json.dumps(matching, indent=2))
        case "plain":
            for name in matching:
                click.echo(name)


@implementation_subcommand(default_implementations=frozenset())  # type: ignore[reportArgumentType]
@click.option(
    "--dialect",
    "-d",
    "dialects",
    type=_Dialect(),
    default=Dialect.known(),
    metavar="URI_OR_NAME",
    multiple=True,
    help="Filter from the given list of dialects only.",
)
@click.option(
    "--latest",
    "-l",
    "latest",
    is_flag=True,
    default=False,
    help="Show only the latest dialect.",
)
@click.option(
    "--boolean-schemas/--no-boolean-schemas",
    "-b/-B",
    "booleans",
    default=None,
    help=(
        "If provided, show only dialects which do (or do not) "
        "support boolean schemas. Otherwise show either kind."
    ),
)
async def filter_dialects(
    start: Callable[
        [],
        AsyncIterator[tuple[ConnectableId, Implementation]],
    ],
    dialects: Iterable[Dialect],
    latest: bool,
    booleans: bool | None,
):
    """
    Output dialect URIs matching a given criteria.

    If any implementations are provided, filter dialects supported by all the
    given implementations.
    """
    matching = {
        dialect
        for dialect in dialects
        if booleans is None or dialect.has_boolean_schemas == booleans
    }

    async for _, implementation in start():
        matching &= implementation.info.dialects

    if not matching:
        click.echo("No dialects match.", file=sys.stderr)
        return EX.DATAERR

    for dialect in sorted(matching, reverse=True):
        click.echo(dialect.uri)
        if latest:
            break


@implementation_subcommand()  # type: ignore[reportArgumentType]
@format_option()
async def info(
    start: Callable[
        [],
        AsyncIterator[tuple[ConnectableId, Implementation]],
    ],
    format: _F,
):
    """
    Show information about a supported implementation.
    """
    serializable: dict[ConnectableId, dict[str, Any]] = {}

    async for _, each in start():
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
                serializable[each.id] = dict(metadata)
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
@format_option()
async def smoke(
    start: Callable[
        [],
        AsyncIterator[tuple[ConnectableId, Implementation]],
    ],
    format: _F,
    echo: Callable[..., None],
) -> int:
    """
    Smoke test implementations for basic correctness against Bowtie's protocol.
    """
    exit_code = 0

    async for _, implementation in start():
        echo(f"Testing {implementation.id!r}...\n", file=sys.stderr)
        serializable: list[dict[str, Any]] = []
        implementation_exit_code = 0

        async for _, results in implementation.smoke():
            async for case, result in results:
                if result.unsuccessful():
                    implementation_exit_code |= EX.DATAERR

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

def calculate_stats(
    unsuccessful: ValuesView[float],
    n: int,
):
    return {
        "median": median(unsuccessful),
        "mean": mean(unsuccessful),
        **( # quantiles only make sense for n < len(data)
            {"quantiles": quantiles(unsuccessful, n=n)}
            if n < len(unsuccessful)
            else {}
        ),
    }

@subcommand
@format_option()
@click.option(
    "--quantiles",
    "n",
    default=4,
    type=int,
    help=(
        "How many quantiles should be emitted for the compliance numbers? "
        "Computing quantiles only is sensical if this number is more than the "
        "number of implementations reported on. By default, we compute "
        "quartiles."
    ),
)
@click.option(
    "--dialect",
    "-d",
    "dialects",
    type=_Dialect(),
    default=Dialect.known(),
    metavar="URI_OR_NAME",
    multiple=True,
    help=(
        "A URI or a shortname identifying the dialect to calculate "
        f"statistics of. Possible shortnames include: "
        f"{', '.join(sorted(Dialect.by_alias()))}."
    ),
)
@click.argument(
    "report",
    default="-" if not sys.stdin.isatty() else None,
    type=_Report(),
    required=False,
)
def statistics(
    report: _report.Report | None,
    n: int,
    format: _F,
    dialects: Iterable[Dialect],
):
    """Show summary statistics for a previous report."""
    reports = {}
    if report is None:
        async def fetch_latest_report(dialect: Dialect):
            return (dialect.short_name, await dialect.latest_report())

        async def fetch_all_dialect_reports():
            return dict(
                await asyncio.gather(
                    *[fetch_latest_report(dialect) for dialect in dialects],
                ),
            )

        reports = asyncio.run(fetch_all_dialect_reports())
        report_stats = [
            {
                "dialect": dialect_name,
                **calculate_stats(
                    report.compliance_by_implementation().values(),
                    n,
                ),
            }
            for dialect_name, report in reports.items()
        ]
    else:
        unsuccessful = report.compliance_by_implementation().values()
        report_stats = calculate_stats(unsuccessful, n)

    match format:
        case "json":
            click.echo(json.dumps(report_stats, indent=2))
        case "pretty":
            if isinstance(report_stats, list):
                for stats in report_stats:
                    if "dialect" in stats:
                        click.echo(f"Dialect: {stats['dialect']}")
                    for k, v in stats.items():
                        if k != "dialect":
                            click.echo(f"  {k}: {v}")
            else:
                for k, v in report_stats.items():
                    click.echo(f"{k}: {v}")
        case "markdown":
            if isinstance(report_stats, list):
                columns = ["Dialect"] + list(report_stats[0].keys())[1:]
                rows = [
                    [str(stats["dialect"])] +
                    [str(stats[column]) for column in columns[1:]]
                    for stats in report_stats
                ]
            else:
                columns = ["", ""]
                rows = [[str(k), str(v)] for k, v in report_stats.items()]

            markdown = _convert_table_to_markdown(columns=columns, rows=rows)
            click.echo(markdown)

@subcommand
@IMPLEMENTATION
@FILTER
@fail_fast
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
    Run the official JSON Schema test suite against any implementation.

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
    task = _run(**kwargs, dialect=dialect, cases=cases, run_metadata=metadata)
    return asyncio.run(task)


async def _run(
    connectables: Iterable[_connectables.Connectable],
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
    acknowledged: Mapping[ConnectableId, ImplementationInfo] = {}
    runners: list[DialectRunner] = []
    async with _start(
        connectables=connectables,
        reporter=reporter,
        **kwargs,
    ) as starting:
        for each in starting:
            try:
                _, implementation = await each
            except (NoSuchImplementation, StartupFailed) as error:
                exit_code |= EX.CONFIG
                STDERR.print(error)
                continue

            try:
                runner = await implementation.start_speaking(dialect)
            except DialectError as error:
                exit_code |= EX.CONFIG
                STDERR.print(error)
            except UnsupportedDialect as error:
                STDERR.print(error)
            else:
                acknowledged[implementation.id] = implementation.info
                runners.append(runner)

        if not runners:
            STDERR.print(
                "[bold red]No implementations started successfully![/]",
            )
            return exit_code | EX.CONFIG

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
            got_result = reporter.case_started(seq_case, dialect)

            responses = [seq_case.run(runner=runner) for runner in runners]

            for each in asyncio.as_completed(responses):
                result = await each
                got_result(result=result)
                unsucessful += result.unsuccessful()
                if (
                    max_fail
                    and unsucessful.failed >= max_fail
                    or (max_error and unsucessful.errored >= max_error)
                ):
                    should_stop = True

            if should_stop:
                STDERR.print(
                    "[bold yellow]Stopping -- the maximum number of "
                    "unsuccessful tests was reached![/]",
                )
                break
        reporter.finished(did_fail_fast=should_stop)
        if count == 0:
            exit_code = EX.NOINPUT
            STDERR.print("[bold red]No test cases ran.[/]")
        elif count > 1:  # XXX: Ugh, this should be removed when Reporter dies
            STDERR.print(f"Ran [green]{count}[/] test cases.")
    return exit_code


@asynccontextmanager
async def _start(
    connectables: Iterable[_connectables.Connectable],
    read_timeout_sec: float,
    **kwargs: Any,
):
    async def _connected(
        connectable: _connectables.Connectable,
        **kwargs: Any,
    ):
        implementation = await stack.enter_async_context(
            connectable.connect(**kwargs),
        )
        return connectable.to_terse(), implementation

    async with AsyncExitStack() as stack:
        yield asyncio.as_completed(
            [_connected(each, **kwargs) for each in connectables],
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
