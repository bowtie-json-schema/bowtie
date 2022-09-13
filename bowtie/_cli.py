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

from bowtie._core import Implementation, Reporter, report_on


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
    "--implementation", "-i", "implementations",
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


async def _run(implementations, reporter, cases, hide_results, fail_fast):
    reporter.run_starting(implementations=implementations)

    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())
        runners = [
            await stack.enter_async_context(
                Implementation.start(docker=docker, image_name=each),
            ) for each in implementations
        ]
        reporter.ready(implementations=runners)

        seq = 0
        for seq, case, case_reporter in sequenced(cases, reporter):

            should_stop = False

            if hide_results:
                for test in case["tests"]:
                    # TODO: Re-emit me later
                    test.pop("valid", None)

            responses = [each.run_case(seq=seq, case=case) for each in runners]
            for each in asyncio.as_completed(responses):
                response = await each
                response.report(reporter=case_reporter)
                if fail_fast and not response.succeeded:
                    should_stop = True

            if should_stop:
                break
        reporter.finished(count=seq)
    return seq


def sequenced(cases, reporter):
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)
