from collections import defaultdict
from contextlib import AsyncExitStack
import asyncio
import json
import os
import sys

import aiodocker
import click
import structlog

from bowtie._core import Implementation, Reporter


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie")
def main():
    """
    A meta-validator for the JSON Schema specifications.
    """


@main.command()
@click.pass_context
@click.option(
    "--implementation", "-i", "implementations",
    help="A docker image which implements the bowtie IO protocol.",
    multiple=True,
)
def run(context, **kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    out = sys.stderr
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(
                fmt="%Y-%m-%d %H:%M.%S", utc=False,
            ),
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.dev.ConsoleRenderer(
                colors=getattr(out, "isatty", lambda: False)(),
            ),
        ],
        logger_factory=structlog.PrintLoggerFactory(out),
    )
    cases = (json.loads(line) for line in sys.stdin.buffer)
    reporter = Reporter()
    count = asyncio.run(_run(**kwargs, reporter=reporter, cases=cases))
    if not count:
        context.exit(os.EX_DATAERR)


async def _run(implementations, reporter, cases):
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
            responses = [each.run_case(seq=seq, case=case) for each in runners]
            for each in asyncio.as_completed(responses):
                response = await each
                if not response["succeeded"]:
                    if response.get("backoff"):
                        case_reporter.backoff(response)
                    else:
                        case_reporter.errored_uncaught(response)
                    continue

                if response["response"].get("errored"):
                    case_reporter.errored(response)
                    continue

                case_reporter.got_results(
                    implementation=response["implementation"],
                    results=[
                        dict(test=test, result=result)
                        for test, result in zip(
                            case["tests"],
                            response["response"]["results"],
                        )
                    ],
                )
        reporter.finished(count=seq)
    return seq


def sequenced(cases, reporter):
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)
