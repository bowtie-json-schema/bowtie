from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from contextlib import AsyncExitStack, asynccontextmanager
from fnmatch import fnmatch
from functools import wraps
from io import TextIOWrapper
from pathlib import Path
from pprint import pformat
from statistics import mean, median, quantiles
from textwrap import dedent
from time import perf_counter_ns
from typing import IO, TYPE_CHECKING, Any, Literal, ParamSpec, Protocol, cast
import asyncio
import json
import logging
import os
import sys
import tarfile

from click.shell_completion import CompletionItem
from diagnostic import DiagnosticError
from inflect import engine as InflectEngine
from rich import box, console, panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Column, Table
from rich.text import Text
from rich_click.utils import CommandGroupDict, OptionGroupDict
from url import URL, RelativeURLWithoutBase
import httpx
import rich_click as click
import structlog
import structlog.typing

from bowtie import DOCS, HOMEPAGE, _benchmarks, _connectables, _report, _suite
from bowtie._commands import SeqCase, TestResult, Unsuccessful
from bowtie._core import (
    Dialect,
    Example,
    Implementation,
    Test,
    TestCase,
    convert_table_to_markdown,
)
from bowtie._direct_connectable import Direct
from bowtie.exceptions import (
    CannotConnect,
    DialectError,
    NoSuchImplementation,
    StartupFailed,
    UnsupportedDialect,
)

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Mapping,
        Sequence,
        Set,
    )
    from os import PathLike
    from typing import TextIO

    from click.decorators import FC
    from httpx import Response
    from referencing.jsonschema import SchemaResource

    from bowtie._commands import AnyTestResult, SeqResult
    from bowtie._connectables import Connectable, ConnectableId
    from bowtie._core import DialectRunner, ImplementationInfo
    from bowtie._registry import ValidatorRegistry


class _EX:
    def __getattr__(self, attr: str) -> int:
        return getattr(os, f"EX_{attr}", 1)  # Windows fallbacks...


EX = _EX()

STDOUT = console.Console()
STDERR = console.Console(stderr=True)

STARTUP_ERRORS = (CannotConnect, NoSuchImplementation, StartupFailed)


# rich-click's CommandGroupDict seems to be missing some covariance,
# as using a regular dict here makes pyright complain.
_COMMAND_GROUPS = {
    "bowtie": [
        CommandGroupDict(
            name="Basic Commands",
            commands=["validate", "suite", "summary", "info"],
        ),
        CommandGroupDict(
            name="Advanced Usage",
            commands=[
                "filter-dialects",
                "filter-implementations",
                "latest-report",
                "run",
                "statistics",
                "trend",
            ],
        ),
        CommandGroupDict(
            name="Plumbing Commands",
            commands=["badges", "smoke"],
        ),
        CommandGroupDict(
            name="Benchmarking Commands",
            commands=["perf", "filter-benchmarks"],
        ),
    ],
}
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
                (
                    "Filters",
                    [
                        "supports-dialect",
                        "language",
                        "direct",
                        "implementation",
                    ],
                ),
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
        (
            "perf",
            [
                ("Required", ["implementation"]),
                (
                    "Benchmark Configuration Options",
                    [
                        "benchmark-file",
                        "dialect",
                        "keywords",
                        "loops",
                        "runs",
                        "test-suite",
                        "values",
                        "warmups",
                    ],
                ),
                (
                    "Basic Options",
                    ["format", "max-fail", "quiet"],
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
        f"""
        If you don't know where to begin, `bowtie validate --help` or
        `bowtie suite --help` are likely good places to start.

        Full documentation can also be found at {DOCS}
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


class Starter(Protocol):

    connectables: Iterable[Connectable]

    def __call__(
        self,
        connectables: Iterable[Connectable] = [],
    ) -> AsyncIterator[tuple[ConnectableId, Implementation]]: ...


class ImplementationSubcommand(Protocol):
    def __call__(
        self,
        start: Starter,
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
            connectables: Iterable[Connectable],
            registry: ValidatorRegistry[Any] = Direct.from_id(
                "python-jsonschema",
            ).registry(),
            **kw: Any,
        ) -> int:
            exit_code = 0

            async def start(
                connectables: Iterable[Connectable] = connectables,
            ):
                nonlocal exit_code

                successful = 0
                async with _start(
                    connectables=connectables,
                    registry=registry,
                    reporter=reporter,
                ) as implementations:
                    for each in implementations:  # FIXME: respect --quiet
                        try:
                            connectable_implementation = await each
                        except STARTUP_ERRORS as error:
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
            start.connectables = connectables  # type: ignore[reportFunctionMemberAccess]

            fn_exit_code = await fn(start=start, **kw)  # type: ignore[reportArgumentType]
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
                "implementations to run. "
                "Run `bowtie filter-implementations` for the full list of "
                "supported implementations."
            ),
        )
        @wraps(fn)
        def cmd(
            connectables: Iterable[Connectable],
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
                dir = outdir / each.id

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
            uri = URL.parse(f"tag:bowtie.report,2024:cli:{ctx.command.name}")
            schema = Direct.from_id("python-jsonschema").registry().schema(uri)
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
        exit_code = (
            EX.DATAERR
            if any(
                unsuccessful.failed or unsuccessful.errored
                for _, __, unsuccessful in results
            )
            else 0
        )
        to_table = _failure_table
        to_markdown_table = _failure_table_in_markdown

        def to_serializable(  # type: ignore[reportRedeclaration]
            value: Iterable[
                tuple[ConnectableId, ImplementationInfo, Unsuccessful],
            ],
        ):
            return [(id, u.counts()) for id, _, u in value]

    else:
        results = report.cases_with_results()
        exit_code = 0
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
            STDOUT.print(table)
        case "markdown":
            table = to_markdown_table(report, results)  # type: ignore[reportGeneralTypeIssues]
            STDOUT.print(table)

    return exit_code


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

    implementation_counts = Counter(
        each.id for each in report.implementations.values()
    )
    for _, each, unsuccessful in results:
        table.add_row(
            Text.assemble(
                each.name,
                (
                    (f" {each.version}", "dim")
                    if implementation_counts[each.id] > 1
                    else ("", "")
                ),
                (f" ({each.language})", "dim"),
            ),
            str(len(unsuccessful.skipped)),
            str(len(unsuccessful.errored)),
            str(len(unsuccessful.failed)),
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

    implementation_counts = Counter(
        each.id for each in report.implementations.values()
    )
    for _, each, unsuccessful in results:
        rows.append(
            [
                f"{each.name}"
                + (
                    f" {each.version}"
                    if implementation_counts[each.id] > 1
                    else ""
                )
                + f" ({each.language})",
                str(len(unsuccessful.skipped)),
                str(len(unsuccessful.errored)),
                str(len(unsuccessful.failed)),
            ],
        )

    return "\n".join(
        [
            "# Bowtie Failures Summary",
            convert_table_to_markdown(columns, rows),
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
    implementation_counts = Counter(
        each.id for each in implementations.values()
    )

    for case, test_results in results:
        subtable = Table("Instance", box=box.SIMPLE_HEAD)
        for implementation in implementations.values():
            subtable.add_column(
                Text.assemble(
                    implementation.name,
                    (
                        (f" {implementation.version}", "dim")
                        if implementation_counts[implementation.id] > 1
                        else ("", "")
                    ),
                    (f" ({implementation.language})", "dim"),
                ),
            )

        for test, test_result in test_results:
            subtable.add_row(
                test.syntax(),
                *(Text(test_result[id].description) for id in implementations),
            )

        table.add_row(case.syntax(report.metadata.dialect), subtable)
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
    implementation_counts = Counter(
        each.id for each in implementations.values()
    )
    inner_table_columns.extend(
        f"{implementation.name}"
        + (
            f" {implementation.version}"
            if implementation_counts[implementation.id] > 1
            else ""
        )
        + f" ({implementation.language})"
        for implementation in implementations.values()
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
        inner_markdown_table = convert_table_to_markdown(
            inner_table_columns,
            inner_table_rows,
        )
        schema_name = json.dumps(case.schema, indent=2)
        row_data = [schema_name, inner_markdown_table]
        rows_data.append(row_data)

    for idx, row_data in enumerate(rows_data):
        final_content += (
            f"### {idx+1}. Schema:\n ```json\n{row_data[0]}\n```\n\n"
        )
        final_content += "### Results:"
        final_content += row_data[1]
        final_content += "\n"

    return final_content


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
@click.argument(
    "report",
    default=lambda: (
        "-"
        if not sys.stdin.isatty()
        else _report.Report.from_serialized(
            asyncio.run(Dialect.latest().latest_report()).iter_lines(),
        )
    ),
    type=_Report(),
)
def statistics(
    report: _report.Report,
    n: int,
    format: _F,
):
    """
    Show summary statistics for a Bowtie generated report.

    If stdin is a TTY, the most recent public report for the latest JSON Schema
    dialect is downloaded.
    Otherwise, if it *is not* a TTY (e.g. if it is a pipe) then it should
    contain report data.

    Piping input via:

      $ bowtie latest-report --dialect <some-dialect> | bowtie statistics

    can be useful to retrieve the latest report for a specific dialect.
    """
    dialect, ran_on_date = report.metadata.dialect, report.metadata.started
    unsuccessful = report.compliance_by_implementation().values()
    statistics = dict(
        median=median(unsuccessful),
        mean=mean(unsuccessful),
        **(  # quantiles only make sense for n < len(data)
            {"quantiles": quantiles(unsuccessful, n=n)}
            if n < len(unsuccessful)
            else {}
        ),
    )
    match format:
        case "json":
            statistics = {
                "dialect": str(dialect.uri),
                "ran_on": ran_on_date.isoformat(),
                **statistics,
            }
            click.echo(json.dumps(statistics, indent=2))
        case "pretty":
            click.echo(
                f"Dialect: {dialect.pretty_name}\n"
                f"Ran on: {ran_on_date.strftime('%x %X %Z')}\n",
            )
            for k, v in statistics.items():
                click.echo(f"{k}: {v}")
        case "markdown":
            heading = (
                f"## Dialect: {dialect.pretty_name}\n\n"
                f"### Ran on: {ran_on_date.strftime('%x %X %Z')}\n"
            )
            markdown = convert_table_to_markdown(
                columns=["Metric", "Value"],
                rows=[[k, str(v)] for k, v in statistics.items()],
            )
            click.echo(heading + markdown)


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


def _set_dialect_via_schema(ctx: click.Context, _, value: _Dialect):
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
        else Dialect.latest()
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
        "implementations to run. "
        "Run `bowtie filter-implementations` for the full list of "
        "supported implementations."
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
VALIDATE = click.option(
    "--validate-implementations",
    "-V",
    "registry",
    # I have no idea why Click makes this so hard, but no combination of:
    #     type, default, is_flag, flag_value, nargs, ...
    # makes this work without doing it manually with callback.
    callback=lambda _, __, v: (  # type: ignore[reportUnknownLambdaType]
        Direct.from_id("python-jsonschema" if v else "null").registry()
    ),
    is_flag=True,
    help=(
        "When speaking to implementations (provided via -i), validate "
        "the requests and responses sent to them under Bowtie's JSON Schema "
        "specification. Generally, this option protects against broken Bowtie "
        "implementations and can be left at its default (of off) unless "
        "you are developing a new implementation container."
    ),
)

_inflect_engine = InflectEngine()

POSSIBLE_DIALECT_SHORTNAMES = _inflect_engine.join(sorted(Dialect.by_alias()))  # type: ignore[reportArgumentType]


def pretty_names_str_for(dialects: Iterable[Dialect]) -> str:
    return (
        "all known dialects"
        if list(dialects) == list(Dialect.known())
        else _inflect_engine.join(
            [dialect.pretty_name for dialect in dialects],  # type: ignore[reportArgumentType]
        )
    )


def dialect_option(
    default: Dialect | None = Dialect.latest(),
    **kwargs: Any,
):
    if default is not None:
        kwargs.update(default=default, show_default=default.pretty_name)

    return click.option(
        "--dialect",
        "-D",
        "dialect",
        type=_Dialect(),
        metavar="URI_OR_NAME",
        help=(
            "A URI or shortname identifying the dialect of each test. "
            f"Possible shortnames include: {POSSIBLE_DIALECT_SHORTNAMES}."
        ),
        **kwargs,
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
@dialect_option()
@IMPLEMENTATION
@FILTER
@fail_fast
@SET_SCHEMA
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
@dialect_option(default=None, callback=_set_dialect_via_schema)
@IMPLEMENTATION
@SET_SCHEMA
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


def _set_benchmarker_callable(
    ctx: click.Context,
    value: Any,
    callable: Callable[..., Any],
) -> Any:
    if value:
        ctx.params["benchmarker_callable"] = callable
    return value


@subcommand
@IMPLEMENTATION
@dialect_option()
@format_option()
@click.option(
    "--runs",
    "-r",
    "runs",
    type=int,
    default=3,
    show_default=True,
    help="Number of runs used to run benchmarks.",
)
@click.option(
    "--values",
    "-v",
    "values",
    type=click.IntRange(min=2),
    default=2,
    show_default=True,
    help="Number of values per run.",
)
@click.option(
    "--warmups",
    "-w",
    "warmups",
    type=int,
    default=1,
    show_default=True,
    help="Number of skipped values per run used to warmup the benchmark.",
)
@click.option(
    "--loops",
    "-l",
    "loops",
    type=int,
    default=1,
    show_default=True,
    help="Number of loops per value.",
)
@click.option(
    "--quiet",
    "-q",
    "quiet",
    is_flag=True,
    default=False,
    show_default=True,
    help="Enable quiet mode (Only output the final result).",
)
@click.option(
    "--keywords",
    "-k",
    "keywords",
    callback=lambda ctx, __, value: (  # type: ignore[reportUnknownLambdaType]
        _set_benchmarker_callable(
            ctx,  # type: ignore[reportUnknownArgumentType]
            value,
            _benchmarks.Benchmarker.for_keywords,
        )
    ),
    is_flag=True,
    show_default=True,
    help=(
        "Run keyword specific benchmarks to learn about how "
        "various implementations implement the keyword."
    ),
)
@click.option(
    "-b",
    "--benchmark-file",
    "benchmark_files",
    callback=lambda ctx, __, value: (  # type: ignore[reportUnknownLambdaType]
        _set_benchmarker_callable(
            ctx,  # type: ignore[reportUnknownArgumentType]
            value,
            _benchmarks.Benchmarker.for_benchmark_files,
        )
    ),
    multiple=True,
    help=(
        "Allows running benchmark from a file. "
        "Specify the path of the benchmark file"
    ),
)
@click.option(
    "--test-suite",
    "-t",
    "test_suite",
    callback=lambda ctx, __, value: (  # type: ignore[reportUnknownLambdaType]
        _set_benchmarker_callable(
            ctx,  # type: ignore[reportUnknownArgumentType]
            value,
            _benchmarks.Benchmarker.from_test_cases,
        )
    ),
    type=_suite.ClickParam(),
    default=None,
    help="Run Benchmarks over the official JSON Schema Test Suite.",
)
@click.argument(
    "benchmark",
    type=JSON(),
    required=False,
    callback=lambda ctx, __, value: (  # type: ignore[reportUnknownLambdaType]
        _set_benchmarker_callable(
            ctx,  # type: ignore[reportUnknownArgumentType]
            value,
            _benchmarks.Benchmarker.from_input,
        )
    ),
)
def perf(
    connectables: Iterable[_connectables.Connectable],
    dialect: Dialect,
    format: _F,
    quiet: bool,
    benchmarker_callable: Callable[..., Any] = (
        _benchmarks.Benchmarker.from_default_benchmarks
    ),
    **kwargs: Any,
):
    """
    Perform performance measurements across supported implementations.
    """
    if kwargs.get("test_suite"):
        cases, enforced_dialect, _ = kwargs["test_suite"]
        dialect = enforced_dialect
        kwargs["cases"] = cases

    try:
        benchmarker = benchmarker_callable(dialect=dialect, **kwargs)
        asyncio.run(
            benchmarker.start(
                connectables=connectables,
                dialect=dialect,
                quiet=quiet,
                format=format,
            ),
        )
    except (_benchmarks.BenchmarkError, _benchmarks.BenchmarkLoadError) as err:
        STDERR.print(err)
        return EX.DATAERR

    return 0


@subcommand
@dialect_option()
@click.option(
    "-t",
    "--benchmark-type",
    type=click.Choice(["default", "keyword"]),
    default=None,
    show_default=True,
    help=("Specify the type of benchmark to filter."),
)
@click.option(
    "-n",
    "--name",
    "benchmark_names",
    type=str,
    multiple=True,
    help=(
        "Filter the benchmarks with given name. "
        "Use the option multiple times to filter multiple benchmarks."
    ),
)
def filter_benchmarks(
    dialect: Dialect,
    benchmark_type: str | None,
    benchmark_names: Iterable[str],
):
    """
    Output benchmarks matching the specified criteria.
    """
    files: list[Path] = _benchmarks.get_benchmark_files(
        benchmark_type,
        benchmarks=benchmark_names,
        dialect=dialect,
    )
    for file in files:
        STDOUT.file.write(f"{file}\n")


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
        "Only include implementations supporting the given dialect URI "
        "or dialect shortname. "
        f"Possible shortnames include: {POSSIBLE_DIALECT_SHORTNAMES}."
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
    help="Only include implementations in the given programming language.",
)
@click.option(
    "--direct",
    "filter_connectable",
    is_flag=True,
    callback=lambda _, __, value: (  # type: ignore[reportUnknownLambdaType]
        (lambda connectable: connectable.kind == "direct")  # type: ignore[reportUnknownLambdaType]
        if value
        else (lambda connectable: True)  # type: ignore[reportUnknownLambdaType]
    ),
    help=(
        "Only include implementations with direct connectable functionality "
        "(i.e. which can run without the presence of a container runtime)."
    ),
)
async def filter_implementations(
    start: Starter,
    dialects: Sequence[Dialect],
    languages: Set[str],
    filter_connectable: Callable[[Connectable], bool],
    format: Literal["plain", "json"],
):
    """
    Output implementations which match the given criteria.

    Useful for piping or otherwise using the resulting output for further
    Bowtie commands.
    """
    filtered = (c for c in start.connectables if filter_connectable(c))
    if not dialects and languages == KNOWN_LANGUAGES:
        # speed up `bowtie filter-implementations`with no args or with --direct
        matching = [each.to_terse() for each in filtered]
    else:
        matching: Sequence[str] = [
            name
            async for name, each in start(connectables=filtered)
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
    start: Starter,
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


@subcommand
@dialect_option()
def latest_report(dialect: Dialect):
    """
    Output the latest published report from Bowtie's website.
    """

    async def write(response: Awaitable[Response]):
        async for chunk in (await response).aiter_bytes():
            click.echo(chunk)

    asyncio.run(write(dialect.latest_report()))


def _info_links_table_for(metadata: dict[str, Any]):
    table = Table(
        Column(style="spring_green4"),
        box=None,
        padding=(0, 1, 0, 0),
        show_header=False,
    )

    table.add_row("homepage", metadata["homepage"])
    table.add_row("source", metadata["source"])
    table.add_row("issues", metadata["issues"])

    if "documentation" in metadata:
        table.add_row("documentation", metadata["documentation"])

    for link in metadata.get("links", []):
        table.add_row(link["description"], link["url"])

    return table


def _info_table_for(metadata: dict[str, Any]):
    table = Table(
        Column(style="cyan bold"),
        box=box.ROUNDED,
        show_header=False,
        border_style="bright_black",
    )

    table.add_row(
        "implementation",
        f"{metadata["name"]} [grey58]{metadata.get("version", "")}[/grey58]",
    )
    table.add_row(
        "language",
        f"{metadata["language"]} [grey58]{metadata.get("language_version", "")}[/grey58]",  # noqa: E501
    )
    table.add_row(
        "dialects",
        "\n".join(
            Dialect.from_str(dialect).pretty_name
            for dialect in cast("list[str]", metadata.get("dialects"))
        ),
        end_section=True,
    )
    table.add_row("links", _info_links_table_for(metadata))

    if "os" in metadata:
        table.caption = Text(
            f"Ran on {metadata["os"]} {metadata.get("os_version", "")}",
            style="bright_black",
        )

    return table


@implementation_subcommand()  # type: ignore[reportArgumentType]
@format_option()
@click.option(
    "--versions/--no-versions",
    "show_versions",
    help="Also show all implementation versions which Bowtie supports.",
)
async def info(
    start: Starter,
    format: _F,
    show_versions: bool,
):
    """
    Show information about a supported implementation.
    """
    serializable: dict[ConnectableId, dict[str, Any]] = {}

    async for _, each in start():
        metadata = [(k, v) for k, v in each.info.serializable().items() if v]
        if show_versions:
            metadata.append(("versions", await each.get_versions()))

        metadata.sort(
            key=lambda kv: (
                kv[0] != "name",
                kv[0] != "language",
                kv[0] != "version",
                kv[0] == "links",
                kv[0] == "versions",
                kv[0] == "dialects",
                kv[0],
            ),
        )

        match format:
            case "json":
                serializable[each.id] = dict(metadata)
            case "pretty":
                table = _info_table_for(dict(metadata))
                STDOUT.print(table, "\n")
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


async def download_versions_of(id: ConnectableId) -> frozenset[str]:
    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        SpinnerColumn(finished_text=""),
        BarColumn(bar_width=None),
        TextColumn(
            "[progress.percentage]{task.percentage:>3.0f}%",
        ),
        "•",
        DownloadColumn(),
        "•",
        TimeElapsedColumn(),
        console=STDOUT,
        transient=True,
    )
    task = progress.add_task(
        description=f"Fetching versions of {id}",
        total=None,
    )

    async with httpx.AsyncClient(timeout=10) as client:
        with progress:
            try:
                url = (
                    HOMEPAGE / "implementations" / id / "matrix-versions.json"
                )
                response = await client.get(str(url))
                response.raise_for_status()
            except httpx.HTTPStatusError as err:
                progress.update(
                    task,
                    description=(
                        f"[bold red]Could not fetch versions of "
                        f"{id}: {err.response.status_code}"
                    ),
                    completed=None,
                    total=None,
                    advance=None,
                )
                return frozenset()
            else:
                content = response.content
                content_length = len(content)

                progress.update(
                    task,
                    description=(
                        f"Successfully fetched all versions of {id}!"
                    ),
                    completed=content_length,
                    total=content_length,
                    advance=content_length,
                )
                return frozenset(json.loads(content))


async def download_and_parse_reports_for(
    id: ConnectableId,
    versions: Set[str],
    dialects: Iterable[Dialect],
) -> Iterable[tuple[str, Dialect, _report.Report]]:
    pretty_names_str = pretty_names_str_for(dialects)

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        SpinnerColumn(finished_text=""),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        "•",
        MofNCompleteColumn(),
        "•",
        TimeElapsedColumn(),
        console=STDOUT,
        transient=True,
    )

    if versions:
        total_files = len(versions) * len(list(dialects))
        actual_downloaded_files = 0

        task = progress.add_task(
            description=(
                "Preparing to download and parse versioned "
                f"reports of {id} for {pretty_names_str}"
            ),
            total=total_files,
        )

        async with httpx.AsyncClient(timeout=10) as client:

            async def download_and_parse_versioned_report_for(
                version: str,
                dialect: Dialect,
            ):
                try:
                    url = (
                        HOMEPAGE
                        / "implementations"
                        / id
                        / f"v{version}"
                        / f"{dialect.short_name}.json"
                    )
                    response = await client.get(str(url))
                    response.raise_for_status()
                    progress.update(
                        task,
                        description=(
                            f"Downloading and Parsing: "
                            f"v{version}/{dialect.short_name}.json"
                        ),
                    )
                except httpx.HTTPStatusError:
                    report = _report.Report.empty(dialect=dialect)
                    progress.update(task, advance=1)
                    return version, dialect, report
                else:
                    nonlocal actual_downloaded_files
                    actual_downloaded_files += 1

                    report = _report.Report.from_serialized(
                        response.iter_lines(),
                    )
                    progress.update(task, advance=1)
                    return version, dialect, report

            with progress:
                responses = await asyncio.gather(
                    *[
                        download_and_parse_versioned_report_for(
                            version,
                            dialect,
                        )
                        for version in versions
                        for dialect in dialects
                    ],
                )

                progress.update(
                    task,
                    description=(
                        "Successfully downloaded and parsed all versioned "
                        f"reports of {id} for {pretty_names_str}!"
                    ),
                    completed=actual_downloaded_files,
                    total=actual_downloaded_files,
                )
                return responses
    else:
        total_files = len(list(dialects))

        task = progress.add_task(
            description=(
                f"Preparing to download and parse latest "
                f"reports of {id} for {pretty_names_str}"
            ),
            total=total_files,
        )

        async def download_and_parse_latest_report_for(dialect: Dialect):
            try:
                response = await dialect.latest_report()
                response.raise_for_status()
                progress.update(
                    task,
                    description=(
                        f"Downloading and Parsing: "
                        f"latest/{dialect.short_name}.json"
                    ),
                )
            except httpx.HTTPStatusError:
                report = _report.Report.empty(dialect=dialect)
                progress.update(task, advance=1)
                return "latest", dialect, report
            else:
                report = _report.Report.from_serialized(response.iter_lines())
                progress.update(task, advance=1)
                return "latest", dialect, report

        with progress:
            responses = await asyncio.gather(
                *[
                    download_and_parse_latest_report_for(dialect)
                    for dialect in dialects
                ],
            )

            progress.update(
                task,
                description=(
                    f"Successfully downloaded and parsed all latest "
                    f"reports of {id} for {pretty_names_str}!"
                ),
                completed=total_files,
                total=total_files,
            )
            return responses


def _trend_table_for(
    id: ConnectableId,
    versions: Set[str],
    dialects_trend: dict[Dialect, _report.Report],
) -> Table:
    main_table = Table(show_lines=True)
    main_table.add_column(
        "Dialect",
        justify="center",
        vertical="middle",
    )
    main_table.add_column(
        f"Trend Data of {id} versions",
        justify="center",
    )

    def add_sub_table_row(
        sub_table: Table,
        version: str,
        unsuccessful: Unsuccessful,
    ):
        sub_table.add_row(
            version,
            str(len(unsuccessful.skipped)),
            str(len(unsuccessful.errored)),
            str(len(unsuccessful.failed)),
        )

    for dialect, report in dialects_trend.items():
        test = "tests" if report.total_tests != 1 else "test"
        sub_table = Table(
            "Version",
            "Skips",
            "Errors",
            "Failures",
            caption=f"{report.total_tests} {test} ran",
            show_edge=False,
        )

        if versions:
            for version, unsuccessful in report.latest_to_oldest():
                add_sub_table_row(sub_table, version, unsuccessful)
        else:
            implementation = report.implementations[id]
            version = implementation.version or "latest"
            unsuccessful = report.unsuccessful(id)
            add_sub_table_row(sub_table, version, unsuccessful)

        main_table.add_row(dialect.pretty_name, sub_table)

    return main_table


def _trend_table_in_markdown_for(
    id: ConnectableId,
    versions: Set[str],
    dialects_trend: dict[Dialect, _report.Report],
) -> str:
    rows_data: list[list[str]] = []

    inner_table_columns = [
        "Version",
        "Skips",
        "Errors",
        "Failures",
    ]

    def create_inner_table_row(
        version: str,
        unsuccessful: Unsuccessful,
    ):
        return [
            version,
            str(len(unsuccessful.skipped)),
            str(len(unsuccessful.errored)),
            str(len(unsuccessful.failed)),
        ]

    for dialect, report in dialects_trend.items():
        test = "tests" if report.total_tests != 1 else "test"
        inner_table_rows: list[list[str]] = []
        if versions:
            for version, unsuccessful in report.latest_to_oldest():
                inner_table_rows.append(
                    create_inner_table_row(version, unsuccessful),
                )
        else:
            implementation = report.implementations[id]
            version = implementation.version or "latest"
            unsuccessful = report.unsuccessful(id)
            inner_table_rows.append(
                create_inner_table_row(version, unsuccessful),
            )

        inner_markdown_table = convert_table_to_markdown(
            inner_table_columns,
            inner_table_rows,
        )
        row_data = [
            dialect.pretty_name,
            inner_markdown_table,
            f"**{report.total_tests} {test} ran**",
        ]
        rows_data.append(row_data)

    return f"## Trend Data of {id} versions:\n\n" + "\n\n".join(
        [
            f"### Dialect: {row_data[0]}\n{row_data[1]}\n\n{row_data[2]}"
            for row_data in rows_data
        ],
    )


class _VersionedReportsTar(click.File):
    """
    Select a tar containing previously produced versioned Bowtie reports.
    """

    name = "versioned_reports_tar"
    mode = "rb"

    def convert(  # type: ignore[reportIncompatibleMethodOverride]
        self,
        value: str | PathLike[str] | IO[Any],
        param: click.Parameter | None,
        ctx: click.Context,
    ) -> tuple[frozenset[str], Iterable[tuple[str, Dialect, _report.Report]]]:
        input = super().convert(value, param, ctx)

        id = cast(
            "_connectables.Connectable",
            ctx.params.get("connectable"),
        ).to_terse()

        try:
            with tarfile.open(fileobj=input) as tar:
                members = tar.getmembers()

                if not any(
                    member.name.startswith(f"./{id}/") for member in members
                ):
                    STDERR.print(
                        f"Couldn't find a '{id}' directory in {input.name}.",
                    )
                    ctx.exit(EX.DATAERR)

                versions: frozenset[str] = frozenset()
                try:
                    versions_content = tar.extractfile(
                        f"./{id}/matrix-versions.json",
                    )
                except KeyError:
                    STDERR.print(
                        "No versions detected (couldn't find a "
                        "'matrix-versions.json' file in ",
                        f"{id} directory of {input.name}.)",
                    )
                    ctx.exit(EX.DATAERR)
                else:
                    if versions_content:
                        versions = frozenset(json.load(versions_content))

                versions_dirs = [
                    member.name
                    for member in members
                    if member.isdir()
                    and (
                        member.name.removeprefix(f"./{id}/").removeprefix("v")
                    )
                    in versions
                ]
                if not versions_dirs:
                    STDERR.print(
                        f"Couldn't find any versions sub-directories in {id} "
                        f"directory of {input.name} as per listed by its "
                        "matrix-versions.json file.",
                    )
                    ctx.exit(EX.DATAERR)

                progress = Progress(
                    TextColumn("[bold blue]{task.description}"),
                    SpinnerColumn(finished_text=""),
                    BarColumn(bar_width=None),
                    TextColumn(
                        "[progress.percentage]{task.percentage:>3.0f}%",
                    ),
                    "•",
                    MofNCompleteColumn(),
                    "•",
                    TimeElapsedColumn(),
                    console=STDOUT,
                    transient=True,
                )
                dialects = (
                    cast(
                        "Iterable[Dialect] | None",
                        ctx.params.get("dialects"),
                    )
                    or Dialect.known()
                )
                pretty_names_str = pretty_names_str_for(dialects)
                task = progress.add_task(
                    description=(
                        f"Preparing to parse all versioned reports of "
                        f"{id} for {pretty_names_str} found in {input.name}"
                    ),
                    total=len(versions) * len(list(dialects)),
                )

                actual_parsed_files = 0
                versioned_reports: Iterable[
                    tuple[str, Dialect, _report.Report]
                ] = []

                with progress:
                    for version in versions:
                        for dialect in dialects:
                            progress.update(
                                task,
                                description=(
                                    f"Parsing: "
                                    f"v{version}/{dialect.short_name}.json"
                                ),
                            )
                            try:
                                report_content = tar.extractfile(
                                    f"./{id}/v{version}/{dialect.short_name}.json",
                                )
                            except KeyError:
                                versioned_reports.append(
                                    (
                                        version,
                                        dialect,
                                        _report.Report.empty(dialect=dialect),
                                    ),
                                )
                            else:
                                if report_content:
                                    versioned_reports.append(
                                        (
                                            version,
                                            dialect,
                                            _report.Report.from_serialized(
                                                TextIOWrapper(
                                                    report_content,
                                                    encoding="utf-8",
                                                ),
                                            ),
                                        ),
                                    )
                                    actual_parsed_files += 1
                            progress.update(task, advance=1)
                    progress.update(
                        task,
                        description=(
                            f"Successfully parsed all versioned reports "
                            f"of {id} for {pretty_names_str} found in "
                            f"{input.name}"
                        ),
                        completed=actual_parsed_files,
                        total=actual_parsed_files,
                    )
                    return versions, versioned_reports
        except tarfile.TarError:
            STDERR.print(f"Failed to process {input.name}.")
            ctx.exit(EX.DATAERR)


@subcommand
@click.option(
    "--implementation",
    "-i",
    "connectable",
    required=True,
    multiple=False,
    default=None,
    type=_connectables.ClickParam(),
    metavar="IMPLEMENTATION",
    help=(
        "A connectable ID for a JSON Schema implementation supported "
        "by Bowtie. Run `bowtie filter-implementations` for the full "
        "list of supported implementations."
    ),
)
@click.option(
    "--dialect",
    "-D",
    "dialects",
    multiple=True,
    default=lambda: Dialect.known(),
    type=_Dialect(),
    metavar="URI_OR_NAME",
    help=(
        "A URI or shortname identifying the dialect of the test suite "
        "you wish to see the trend data for. Possible shortnames include: "
        f"{POSSIBLE_DIALECT_SHORTNAMES}. If none specified then defaults "
        "to all known dialects."
    ),
)
@click.argument(
    "versioned_reports_tar",
    default=None,
    type=_VersionedReportsTar(mode="rb"),
    required=False,
)
@format_option()
def trend(
    connectable: Connectable,
    dialects: Iterable[Dialect],
    versioned_reports_tar: (
        tuple[
            frozenset[str],
            Iterable[tuple[str, Dialect, _report.Report]],
        ]
        | None
    ),
    format: _F,
):
    """
    Show trend data of an implementation across its multiple versions.
    """
    id = connectable.to_terse()

    if not versioned_reports_tar:

        async def download_versions_and_parse_reports_for(
            id: ConnectableId,
            dialects: Iterable[Dialect],
        ):
            versions = await download_versions_of(id)
            downloaded_versioned_reports = (
                await download_and_parse_reports_for(
                    id,
                    versions,
                    dialects,
                )
            )
            return versions, downloaded_versioned_reports

        versions, versioned_reports = asyncio.run(
            download_versions_and_parse_reports_for(id, dialects),
        )
    else:
        versions, versioned_reports = versioned_reports_tar

    if all(report.is_empty for _, _, report in versioned_reports):
        click.echo(
            f"None of the versions of '{id}' "
            f"support {pretty_names_str_for(dialects)}.",
        )
        return

    if versions:
        combine_versioned_reports_for = (
            _report.Report.combine_versioned_reports_for
        )
        dialects_trend = {
            dialect: combined_versions_report
            for dialect in sorted(dialects, reverse=True)
            if (
                combined_versions_report := combine_versioned_reports_for(
                    [report for _, _, report in versioned_reports],
                    dialect,
                )
            )
            and not combined_versions_report.is_empty
        }
    else:
        dialects_trend = {
            dialect: latest_report
            for _, dialect, latest_report in versioned_reports
            if not latest_report.is_empty
            and latest_report.implementations.get(id)
        }

    match format:
        case "json":
            serializable: Iterable[
                tuple[
                    ConnectableId,
                    Iterable[tuple[str, Iterable[tuple[str, dict[str, int]]]]],
                ]
            ] = [
                (
                    id,
                    [
                        (
                            dialect.short_name,
                            [
                                (
                                    version or "latest",
                                    {
                                        "failed": len(unsuccessful.failed),
                                        "errored": len(unsuccessful.errored),
                                        "skipped": len(unsuccessful.skipped),
                                    },
                                )
                                for version, unsuccessful in (
                                    report.latest_to_oldest()
                                    if versions
                                    else [
                                        (
                                            report.implementations[id].version,
                                            report.unsuccessful(id),
                                        ),
                                    ]
                                )
                            ],
                        )
                        for dialect, report in dialects_trend.items()
                    ],
                ),
            ]
            click.echo(json.dumps(serializable, indent=2))
        case "pretty":
            STDOUT.print(
                _trend_table_for(id, versions, dialects_trend),
            )
        case "markdown":
            STDOUT.print(
                _trend_table_in_markdown_for(id, versions, dialects_trend),
            )


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
async def smoke(start: Starter, format: _F, echo: Callable[..., None]) -> int:
    """
    Smoke test implementations for basic correctness against Bowtie's protocol.
    """
    results = [
        (implementation.id, implementation.info, await implementation.smoke())
        async for _, implementation in start()
    ]

    match results, format:
        case [(_, _, result)], "json":
            echo(json.dumps(result.serializable(), indent=2))
        case _, "json":
            output = {id: result.serializable() for id, _, result in results}
            echo(json.dumps(output, indent=2))
        case [(_, _, result)], "pretty":
            STDOUT.print(result)
        case _, "pretty":
            for _, _, each in results:
                STDOUT.print(each)
        case _, "markdown":
            for _, info, result in results:
                echo(f"# {info.name} ({info.language})\n")

                if result.success:
                    echo("Smoke test *succeeded!*")
                else:
                    echo("Smoke test **failed!**")

                epilog: Sequence[
                    tuple[Dialect, Sequence[tuple[TestCase, SeqResult]]]
                ] = []

                echo("\n## Dialects\n")
                for dialect, failures in result.for_each_dialect():
                    if failures:
                        epilog.append((dialect, failures))
                        suffix = " **(failed)**"
                    else:
                        suffix = ""
                    echo(f"* {dialect.pretty_name}{suffix}")

                if epilog:
                    echo("\n## Failures\n")

                    for dialect, failures in epilog:
                        output = dedent(
                            f"""
                            <details>
                            <summary>{dialect.pretty_name}</summary>
                            """,
                        )
                        echo(output)

                        for case, each in failures:
                            output = dedent(
                                f"""
                                ### Schema

                                ```json
                                {json.dumps(case.schema)}
                                ```

                                #### Instances

                                """,
                            )
                            echo(output)

                            # FIXME: This will be nicer if/when Unsuccessful
                            #        contains the unsuccessful results.
                            for i, test in enumerate(case.tests):
                                result = each.result_for(i)
                                if TestResult(valid=test.expected()) != result:  # type: ignore[reportArgumentType]
                                    echo(f"* `{test.instance}`")

                        echo("\n</details>")

    return 0 if all(result.success for _, _, result in results) else EX.DATAERR


@subcommand
@IMPLEMENTATION
@FILTER
@fail_fast
@SET_SCHEMA
@VALIDATE
@click.argument("input", type=_suite.ClickParam(), metavar="DIALECT")
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
    connectables: Iterable[Connectable],
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
            except STARTUP_ERRORS as error:
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

        # Just to complement bowtie perf (not for other purposes)
        time_taken_by_implementations = 0
        time_output_file = (
            Path(os.environ["TIME_OUTPUT_FILE"])
            if "TIME_OUTPUT_FILE" in os.environ
            else None
        )

        for count, case in enumerate(maybe_set_schema(dialect)(cases), 1):
            seq_case = SeqCase(seq=count, case=case)
            got_result = reporter.case_started(seq_case, dialect)

            responses = [seq_case.run(runner=runner) for runner in runners]
            st_time = perf_counter_ns()

            for each in asyncio.as_completed(responses):
                result = await each
                got_result(result=result)
                unsucessful += result.unsuccessful()
                time_taken_by_implementations += perf_counter_ns() - st_time
                if (max_fail and len(unsucessful.failed) >= max_fail) or (
                    max_error and len(unsucessful.errored) >= max_error
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
            exit_code |= EX.NOINPUT
            STDERR.print("[bold red]No test cases ran.[/]")
        elif count > 1:  # XXX: Ugh, this should be removed when Reporter dies
            STDERR.print(f"Ran [green]{count}[/] test cases.")

        if time_output_file:
            with time_output_file.open("a") as file:
                file.write(f"{time_taken_by_implementations}\n")

    return exit_code


@asynccontextmanager
async def _start(
    connectables: Iterable[Connectable],
    **kwargs: Any,
):
    async def _connected(
        connectable: Connectable,
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
