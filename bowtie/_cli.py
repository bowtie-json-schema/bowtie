from collections import defaultdict
from contextlib import AsyncExitStack
import asyncio
import json
import os
import sys

import aiodocker
import click

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

    cases = (json.loads(line) for line in sys.stdin.buffer)
    reporter = Reporter()
    count = asyncio.run(_run(**kwargs, reporter=reporter, cases=cases))
    if not count:
        context.exit(os.EX_DATAERR)


async def _run(implementations, reporter, cases):
    reporter.run_starting(implementations=implementations)

    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())
        streams = [
            await stack.enter_async_context(
                Implementation.start(docker=docker, image_name=each),
            ) for each in implementations
        ]
        reporter.ready(implementations=streams)

        seq = 0
        for seq, case, case_reporter in sequenced(cases, reporter):
            tests = defaultdict(lambda: defaultdict(list))
            responses = [each.run_case(seq=seq, case=case) for each in streams]
            for each in asyncio.as_completed(responses):
                result = await each
                if not result["succeeded"]:
                    if result.get("backoff"):
                        case_reporter.backoff(result)
                    else:
                        case_reporter.errored(result)
                    continue

                results = result["response"]["results"]
                for test, got in zip(case["tests"], results):
                    if got.get("skipped"):
                        bucket = tests[test["description"]]["skipped"]
                    else:
                        bucket = tests[test["description"]][got["valid"]]
                    bucket.append(result["implementation"])

            results = {
                k: dict(v) if len(v) > 1 else next(iter(v))
                for k, v in tests.items()
            }
            case_reporter.case_finished(results=results)
        reporter.finished(count=seq)
    return seq


def sequenced(cases, reporter):
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)
