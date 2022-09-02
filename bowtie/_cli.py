from collections import defaultdict
from contextlib import AsyncExitStack, asynccontextmanager
from textwrap import indent
from time import monotonic_ns
import asyncio
import json
import sys

import aiodocker
import click
import structlog

log = structlog.get_logger()


class StartError(Exception):
    pass


class ImplementationError(Exception):
    def __init__(self, stderr):
        super().__init__(stderr)
        self.stderr = stderr

    def __str__(self):
        return "\n\n" + indent(self.stderr.decode(), " " * 2)


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie")
def main():
    pass


@main.command()
@click.option(
    "--implementation", "-i", "implementations",
    help="A docker image which implements the bowtie IO protocol.",
    multiple=True,
)
@click.option(
    "--test-timeout", "-T", "test_timeout",
    help="The maximum amount of seconds to wait for an individual test.",
    default=0.5,
)
def run(**kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    cases = (json.loads(line) for line in sys.stdin.buffer)
    asyncio.run(_run(**kwargs, cases=cases))


async def _run(implementations, cases, test_timeout):
    async with AsyncExitStack() as stack:
        log.msg(
            "Starting",
            implementations=implementations,
            test_timeout=test_timeout,
        )
        docker = await stack.enter_async_context(aiodocker.Docker())
        streams = {
            await stack.enter_async_context(
                bowtie(docker=docker, image=implementation),
            ): implementation for implementation in implementations
        }
        log.msg("Connected", implementations=sorted(streams.values()))

        responses = await send_all(streams=streams, cmd="start", version=1)
        log.msg("Ready", responses=responses)

        for response in responses:
            if not response.get("ready"):
                raise StartError("Not ready!")
            elif response.get("version") != 1:
                raise StartError("Wrong version!")

        for seq, case in enumerate(cases):
            log.msg("Running", case=case["description"])
            responses = await send_all(
                streams=streams,
                cmd="run",
                seq=seq,
                case=case,
            )
            tests = defaultdict(lambda: defaultdict(list))
            for response in responses:
                if response.get("error"):
                    log.msg("ERROR", stderr=response["stderr"])
                else:
                    for test, each in zip(case["tests"], response["tests"]):
                        tests[test["description"]][each["valid"]].append("")

            result = {
                "description": case["description"],
                "schema": case["schema"],
                "tests": {k: dict(v) for k, v in tests.items()},
            }
            log.msg("Responded", result=result)

        responses = await send_all(
            streams=streams,
            cmd="run",
            seq=seq,
            case=case,
        )
        log.msg("Responded", responses=responses)

        log.msg("Stopping")
        await send_all(streams=streams, cmd="stop")
        log.msg("Stopped")


@asynccontextmanager
async def bowtie(docker, image):
    config = dict(Image=image, OpenStdin=True)
    container = await docker.containers.create(config=config)

    try:
        await container.start()
        yield container.attach(stdin=True, stdout=True, stderr=True)
    finally:
        await container.delete(force=True)


async def send_all(streams, **kwargs):
    return await asyncio.gather(
        *(send(stream, **kwargs) for stream in streams),
    )


async def receive_all(streams):
    return await asyncio.gather(*(receive(stream) for stream in streams))


async def send(stream, cmd, **kwargs):
    kwargs["cmd"] = cmd
    cmd = json.dumps(kwargs).encode("utf-8")
    await stream.write_in(cmd)
    started = monotonic_ns()
    await stream.write_in(b"\n")
    response = await receive(stream) or {}
    response["took_ns"] = monotonic_ns() - started
    return response


async def receive(stream):
    message = await stream.read_out()
    if message is None:
        return

    data = [message.data]
    if message.stream == 2:
        while message.stream == 2:
            message = await stream.read_out()
            if message is None:
                break
            data.append(message.data)
        return {"error": True, "stderr": b"".join(data)}

    return json.loads(message.data)
