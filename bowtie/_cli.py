from collections import defaultdict
from contextlib import AsyncExitStack
import asyncio
import json
import sys

import aiodocker
import click
import structlog

from bowtie._core import Implementation

log = structlog.get_logger()


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie")
def main():
    """
    A meta-validator for the JSON Schema specifications.
    """


@main.command()
@click.option(
    "--implementation", "-i", "implementations",
    help="A docker image which implements the bowtie IO protocol.",
    multiple=True,
)
def run(**kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    cases = (json.loads(line) for line in sys.stdin.buffer)
    asyncio.run(_run(**kwargs, cases=cases))


async def _run(implementations, cases):
    async with AsyncExitStack() as stack:
        log.debug("Starting", implementations=implementations)
        docker = await stack.enter_async_context(aiodocker.Docker())
        streams = [
            await stack.enter_async_context(
                Implementation.start(docker=docker, image_name=each),
            ) for each in implementations
        ]
        log.debug("Ready", implementations=streams)

        for seq, case in enumerate(cases, 1):
            log.debug("Running", seq=seq, case=case["description"])
            responses = await asyncio.gather(
                *(each.run_case(seq=seq, case=case) for each in streams),
            )
            tests = defaultdict(lambda: defaultdict(list))
            for each in responses:
                if not each["succeeded"]:
                    log.error("ERROR", **each)
                    continue

                results = each["response"]["tests"]
                for test, got in zip(case["tests"], results):
                    tests[test["description"]][got["valid"]].append(
                        each["implementation"],
                    )

            results = {
                k: dict(v) if len(v) > 1 else next(iter(v))
                for k, v in tests.items()
            }
            log.msg(
                "Responded",
                seq=seq,
                description=case["description"],
                results=results,
            )
        log.msg("Finished", count=seq)
