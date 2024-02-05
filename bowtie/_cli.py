from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from fnmatch import fnmatch
from functools import cache, wraps
from importlib.resources import files
from pathlib import Path
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
from trogon import tui  # type: ignore[reportMissingTypeStubs]
import click
import referencing_loaders
import rich
import structlog
import structlog.typing

from bowtie import _report, _suite
from bowtie._commands import (
    AnyTestResult,
    SeqCase,
    SeqResult,
    Unsuccessful,
)
from bowtie._containers import ContainerConnection
from bowtie._core import (
    GotStderr,
    Implementation,
    ImplementationInfo,
    NoSuchImplementation,
    StartupFailed,
    Test,
    TestCase,
    _MakeValidator,  # type: ignore[reportPrivateUsage]
)
from bowtie.exceptions import ProtocolError

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        Iterable,
        Mapping,
    )
    from typing import Any, TextIO

    from referencing.jsonschema import Schema, SchemaRegistry, SchemaResource
    from url import URL

    from bowtie._core import DialectRunner

# Windows fallbacks...
_EX_CONFIG = getattr(os, "EX_CONFIG", 1)
_EX_DATAERR = getattr(os, "EX_DATAERR", 1)
_EX_NOINPUT = getattr(os, "EX_NOINPUT", 1)

IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"
LATEST_DIALECT_NAME = "draft2020-12"

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
@click.option(
    "--log-level",
    "-L",
    help="How verbose should Bowtie be?",
    default="info",
    show_default="info",
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
        async def run(
            image_names: list[str],
            read_timeout_sec: float,
            make_validator: _MakeValidator = make_validator,
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
                for each in implementations:
                    try:
                        implementation = await each
                    except StartupFailed as error:
                        exit_code |= _EX_CONFIG
                        click.echo(  # FIXME: respect a possible --quiet
                            f"❗ (error): {error.name!r} failed to start",
                            file=sys.stderr,
                        )
                        continue
                    except NoSuchImplementation as error:
                        exit_code |= _EX_CONFIG
                        click.echo(  # FIXME: respect a possible --quiet
                            f"❗ (error): {error.name!r} is not a "
                            "known Bowtie implementation.",
                            file=sys.stderr,
                        )
                        continue

                    running.append(implementation)

                if running:
                    exit_code |= await fn(implementations=running, **kw) or 0
                else:
                    exit_code |= _EX_CONFIG

            return exit_code

        @subcommand
        @IMPLEMENTATION
        @TIMEOUT
        @wraps(fn)
        def cmd(image_names: list[str], **kwargs: Any) -> int:
            return asyncio.run(run(image_names=image_names, **kwargs))

        return cmd

    return wrapper


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
    report = _report.Report.from_serialized(input)
    if report.is_empty:
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

    report.generate_badges(output)


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

        def to_serializable(  # type: ignore[reportRedeclaration]
            value: Iterable[tuple[ImplementationInfo, Unsuccessful]],
        ):
            return [(each.id, asdict(counts)) for each, counts in value]

    else:
        results = report.cases_with_results()
        to_table = _validation_results_table

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


IMPLEMENTATION = click.option(
    "--implementation",
    "-i",
    "image_names",
    type=lambda name: name if "/" in name else f"{IMAGE_REPOSITORY}/{name}",  # type: ignore[reportUnknownLambdaType]
    required=True,
    multiple=True,
    metavar="IMPLEMENTATION",
    help="A docker image which implements the bowtie IO protocol.",
)
DIALECT = click.option(
    "--dialect",
    "-D",
    "dialect",
    type=_suite.dialect_from_str,
    default=LATEST_DIALECT_NAME,
    show_default=True,
    metavar="URI_OR_NAME",
    help=(
        "A URI or shortname identifying the dialect of each test. Possible "
        f"shortnames include: {', '.join(sorted(_suite.DIALECT_SHORTNAMES))}."
    ),
)
FILTER = click.option(
    "-k",
    "filter",
    type=lambda pattern: f"*{pattern}*",  # type: ignore[reportUnknownLambdaType]
    metavar="GLOB",
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
    return asyncio.run(_run(fail_fast=False, **kwargs, cases=[case]))


@implementation_subcommand()  # type: ignore[reportArgumentType]
@FORMAT
async def info(implementations: Iterable[Implementation], format: _F):
    """
    Retrieve a particular implementation (harness)'s metadata.
    """
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
                click.echo(json.dumps(dict(metadata), indent=2))
            case "pretty":
                click.echo(
                    "\n".join(
                        f"{k}: {json.dumps(v, indent=2)}" for k, v in metadata
                    ),
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

        match format:
            case "json":
                serializable: list[dict[str, Any]] = []

                def see(seq_case: SeqCase, result: SeqResult):  # type: ignore[reportRedeclaration]
                    serializable.append(  # noqa: B023
                        dict(
                            case=seq_case.case.without_expected_results(),
                            result=asdict(result.result),
                        ),
                    )

            case "pretty":

                def see(seq_case: SeqCase, response: SeqResult):
                    echo(f"  · {seq_case.case.description}: {response.dots()}")

        async for seq_case, result in implementation.smoke():
            if result.unsuccessful():
                exit_code |= _EX_DATAERR
            see(seq_case, result)

        match format:
            case "json":
                echo(json.dumps(serializable, indent=2))  # type: ignore[reportPossiblyUnboundVariable]

            case "pretty":
                message = "❌ some failures" if exit_code else "✅ all passed"
                echo(f"\n{message}", file=sys.stderr)

    return exit_code


@subcommand
@IMPLEMENTATION
@FILTER
@FAIL_FAST
@SET_SCHEMA
@TIMEOUT
@VALIDATE
@click.argument("input", type=_suite.ClickParam())
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
            for count, seq_case in enumerate(  # noqa: B007
                SeqCase.for_cases(cases),
                1,
            ):
                case_reporter = reporter.case_started(seq_case)
                if set_schema and not isinstance(seq_case.case.schema, bool):
                    seq_case.case.schema["$schema"] = str(dialect)

                responses = [seq_case.run(runner=runner) for runner in runners]
                for each in asyncio.as_completed(responses):
                    result = await each
                    case_reporter.got_result(result=result)

                    if fail_fast:
                        # Stop after this case, since we still have futures out
                        should_stop = result.unsuccessful().causes_stop

                if should_stop:
                    break
            reporter.finished(count=count, did_fail_fast=should_stop)
            if not count:
                exit_code = _EX_NOINPUT
    return exit_code


@asynccontextmanager
async def _start(
    image_names: Iterable[str],
    make_validator: _MakeValidator,
    read_timeout_sec: float,
    **kwargs: Any,
):
    @asynccontextmanager
    async def _client(
        docker: Docker,
        image_name: str,
    ) -> AsyncIterator[Implementation]:
        async with (
            ContainerConnection.open(
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


def _redirect_structlog(
    log_level: int = logging.INFO,
    file: TextIO = sys.stderr,
):
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
