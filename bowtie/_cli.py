from contextlib import AsyncExitStack
from fnmatch import fnmatch
import asyncio
import json
import os
import sys

import aiodocker
import click
import jinja2
import structlog

from bowtie._core import (
    Implementation,
    Reporter,
    UnsupportedDialect,
    report_on,
)

DRAFT2020 = "https://json-schema.org/draft/2020-12/schema"
DRAFT2019 = "https://json-schema.org/draft/2019-09/schema"
DRAFT7 = "http://json-schema.org/draft-07/schema#"
DRAFT6 = "http://json-schema.org/draft-06/schema#"
DRAFT4 = "http://json-schema.org/draft-04/schema#"
DRAFT3 = "http://json-schema.org/draft-03/schema#"

DIALECT_SHORTNAMES = {
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


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie")
def main():
    """
    A meta-validator for the JSON Schema specifications.
    """


@main.command()
@click.argument(
    "input",
    default="-",
    type=click.File(mode="r"),
)
@click.option(
    "--out", "-o", "output",
    help="Where to write the outputted report HTML.",
    default="bowtie-report.html",
    type=click.File("w"),
)
def report(input, output):
    """
    Generate a Bowtie report from a previous run.
    """

    env = jinja2.Environment(
        loader=jinja2.PackageLoader("bowtie", "template"),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template("report.html.j2")
    output.write(template.render(**report_on(input)))


@main.command()
@click.pass_context
@click.option(
    "--implementation", "-i", "image_names",
    help="A docker image which implements the bowtie IO protocol.",
    multiple=True,
)
@click.option(
    "-k", "filter",
    type=lambda pattern: f"*{pattern}*",
    help="Only run cases whose description match the given glob pattern.",
)
@click.option(
    "-x", "--fail-fast",
    is_flag=True,
    default=False,
    help="Fail immediately after the first error or disagreement.",
)
@click.option(
    "--dialect", "-D", "dialect",
    help=(
        "A URI or shortname identifying the dialect of each test case."
        f"Shortnames include: {sorted(DIALECT_SHORTNAMES)}."
    ),
    type=lambda dialect: DIALECT_SHORTNAMES.get(dialect, dialect),
    default="2020-12",
)
@click.option(
    "--set-schema/--no-set-schema", "-S",
    "set_schema",
    default=False,
    help=(
        "Explicitly set $schema in all (non-boolean) case schemas sent to "
        "implementations. Note this of course means what is passed to "
        "implementations will differ from what is provided in the input."
    ),
)
@click.option(
    "--hide-expected-results/--include-expected-results",
    "hide_results",
    default=True,
    help=(
        "Don't pass expected results to implementations under test. "
        "Doing so generally should have no expected change in behavior."
    ),
)
@click.argument(
    "input",
    default="-",
    type=click.File(mode="rb"),
)
def run(context, input, filter, **kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    out = sys.stderr
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(
                fmt="%Y-%m-%d %H:%M.%S", utc=False,
            ),
            structlog.dev.ConsoleRenderer(
                colors=getattr(out, "isatty", lambda: False)(),
            ),
        ],
        logger_factory=structlog.PrintLoggerFactory(out),
    )
    cases = (json.loads(line) for line in input)
    if filter:
        cases = (
            case for case in cases
            if fnmatch(case["description"], filter)
        )

    reporter = Reporter()
    count = asyncio.run(_run(**kwargs, reporter=reporter, cases=cases))
    if not count:
        context.exit(os.EX_DATAERR)


async def _run(
    image_names,
    cases,
    reporter: Reporter,
    dialect: str,
    hide_results: bool,
    fail_fast: bool,
    set_schema: bool,
):
    reporter.run_starting(implementations=image_names)

    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())

        starting = [
            stack.enter_async_context(
                Implementation.start(
                    docker=docker,
                    image_name=image_name,
                    dialect=dialect,
                ),
            ) for image_name in image_names
        ]
        implementations = []
        for each in asyncio.as_completed(starting):
            try:
                implementation = await each
            except UnsupportedDialect as error:
                reporter.unsupported_dialect(error)
            else:
                implementations.append(implementation)
        reporter.ready(implementations=implementations)

        seq = 0
        should_stop = False
        for seq, case, case_reporter in sequenced(cases, reporter):
            if hide_results:
                for test in case["tests"]:
                    # TODO: Re-emit me later
                    test.pop("valid", None)
            if set_schema and not isinstance(case["schema"], bool):
                case["schema"]["$schema"] = dialect

            responses = [
                each.run_case(seq=seq, case=case) for each in implementations
            ]
            for each in asyncio.as_completed(responses):
                response = await each
                response.report(reporter=case_reporter)
                if fail_fast and not response.succeeded:
                    # Stop after this case, since we still have awaitables out
                    should_stop = True

            if should_stop:
                break
        reporter.finished(count=seq)
    return seq


def sequenced(cases, reporter):
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)
