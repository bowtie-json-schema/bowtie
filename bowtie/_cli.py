from collections import defaultdict
from contextlib import AsyncExitStack
import asyncio
import json
import os
import sys

import aiodocker
import click
import structlog

from bowtie._core import Implementation

_log = structlog.get_logger()


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
    count = asyncio.run(_run(**kwargs, cases=cases))
    if not count:
        _log.error("No test cases ran.")
        context.exit(os.EX_DATAERR)
    else:
        _log.msg("Finished", count=count)


async def _run(implementations, cases):
    _log.debug("Starting", implementations=implementations)

    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())
        streams = [
            await stack.enter_async_context(
                Implementation.start(docker=docker, image_name=each),
            ) for each in implementations
        ]
        _log.debug("Ready", implementations=streams)

        seq = 0
        for seq, case in enumerate(cases, 1):
            log = _log.bind(seq=seq, description=case["description"])
            log.debug("Running")

            tests = defaultdict(lambda: defaultdict(list))
            responses = [each.run_case(seq=seq, case=case) for each in streams]
            for each in asyncio.as_completed(responses):
                result = await each
                if not result["succeeded"]:
                    log.error("ERROR", **result)
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
            log.msg("Responded", results=results)
    return seq
