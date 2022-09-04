from collections import defaultdict
from contextlib import AsyncExitStack, asynccontextmanager
from time import monotonic_ns
import asyncio
import json
import sys

from attrs import define, field
import aiodocker
import click
import structlog

log = structlog.get_logger()


class StartError(Exception):
    pass


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
def run(**kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    cases = (json.loads(line) for line in sys.stdin.buffer)
    asyncio.run(_run(**kwargs, cases=cases))


@define(hash=True)
class Implementation:
    """
    A running implementation under test.
    """

    _name: str
    _stream: aiodocker.stream.Stream = field(repr=False)

    @classmethod
    @asynccontextmanager
    async def start(cls, docker, image_name):
        container = await docker.containers.create(
            config=dict(Image=image_name, OpenStdin=True),
        )
        try:
            await container.start()
            stream = container.attach(stdin=True, stdout=True, stderr=True)
            self = cls(name=image_name, stream=stream)
            await self._start()
            yield self
            await self._stop()
        finally:
            await container.delete(force=True)

    async def _start(self):
        response = await self._send(cmd="start", version=1)
        if not response["response"].get("ready"):
            raise StartError(f"{self._name} is not ready!")
        elif response["response"].get("version") != 1:
            raise StartError(f"{self._name} did not speak version 1!")

    async def run_case(self, seq, case):
        return await self._send(cmd="run", seq=seq, case=case)

    async def _stop(self):
        await self._send(cmd="stop")

    async def _send(self, **kwargs):
        started = monotonic_ns()
        cmd = f"{json.dumps(kwargs)}\n"
        await self._stream.write_in(cmd.encode("utf-8"))

        message = await self._stream.read_out()
        if message is None:
            succeeded, response = None, {}
        elif message.stream == 2:
            succeeded, data = False, [message.data]
            while message.stream == 2:
                message = await self._stream.read_out()
                if message is None:
                    break
                data.append(message.data)
            response = {"stderr": b"".join(data), "implementation": self._name}
        else:
            succeeded, response = True, json.loads(message.data)

        return {
            "succeeded": succeeded,
            "took_ns": monotonic_ns() - started,
            "response": response,
            "implementation": self._name,
        }


async def _run(implementations, cases):
    async with AsyncExitStack() as stack:
        log.msg("Starting", implementations=implementations)
        docker = await stack.enter_async_context(aiodocker.Docker())
        streams = [
            await stack.enter_async_context(
                Implementation.start(docker=docker, image_name=each),
            ) for each in implementations
        ]
        log.msg("Ready", implementations=streams)

        for seq, case in enumerate(cases):
            log.msg("Running", case=case["description"])
            responses = await run_case(streams=streams, seq=seq, case=case)
            tests = defaultdict(lambda: defaultdict(list))
            for each in responses:
                if not each["succeeded"]:
                    log.msg(
                        "ERROR",
                        stderr=each.get("stderr"),
                        implementation=each["implementation"],
                    )
                    continue

                results = each["response"]["tests"]
                for test, got in zip(case["tests"], results):
                    tests[test["description"]][got["valid"]].append(
                        each["implementation"],
                    )

            result = {
                "description": case["description"],
                "schema": case["schema"],
                "tests": {
                    k: dict(v) if len(v) > 1 else next(iter(v))
                    for k, v in tests.items()
                },
            }
            log.msg("Responded", result=result)

        responses = await run_case(streams=streams, seq=seq, case=case)
        log.msg("Last", responses=responses)


async def run_case(streams, **kwargs):
    return await asyncio.gather(*(each.run_case(**kwargs) for each in streams))
