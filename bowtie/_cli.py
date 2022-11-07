from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from fnmatch import fnmatch
from importlib import resources
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin
import asyncio
import json
import os
import sys
import zipfile

from rich import console, panel
import aiodocker
import click
import jinja2
import structlog

from bowtie import _report
from bowtie._commands import Test, TestCase
from bowtie._core import GotStderr, Implementation, StartupFailed
from bowtie.exceptions import _ProtocolError

IMAGE_REPOSITORY = "ghcr.io/bowtie-json-schema"
TEST_SUITE_URL = "https://github.com/json-schema-org/json-schema-test-suite"

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
LATEST_DIALECT_NAME = "draft2020-12"


@click.group(context_settings=dict(help_option_names=["--help", "-h"]))
@click.version_option(prog_name="bowtie", package_name="bowtie-json-schema")
def main():
    """
    A meta-validator for the JSON Schema specifications.
    """

    redirect_structlog()


@main.command()
@click.argument(
    "input",
    default="-",
    type=click.File(mode="r"),
)
@click.option(
    "--out",
    "-o",
    "output",
    help="Where to write the outputted report HTML.",
    default="bowtie-report.html",
    type=click.File("w"),
)
def report(input, output):
    """
    Generate a Bowtie report from a previous run.
    """

    env = jinja2.Environment(
        loader=jinja2.PackageLoader("bowtie"),
        undefined=jinja2.StrictUndefined,
        keep_trailing_newline=True,
    )
    template = env.get_template("report.html.j2")
    output.write(template.render(**_report.from_input(input)))


def validator_for_dialect(dialect: str | None = None):
    from jsonschema.validators import RefResolver, validator_for

    text = resources.read_text("bowtie.schemas", "io-schema.json")
    root_schema = json.loads(text)
    resolver = RefResolver.from_schema(root_schema)
    Validator = validator_for(root_schema)
    Validator.check_schema(root_schema)

    if dialect is None:
        dialect = Validator.META_SCHEMA["$id"]

    def validate(instance, schema):
        resolver.store["urn:current-dialect"] = {"$ref": dialect}
        validator = Validator(schema, resolver=resolver)
        try:
            errors = list(validator.iter_errors(instance))
        except Exception:  # XXX: Warn after Reporter disappears
            pass
        else:
            if errors:
                raise _ProtocolError(errors=errors)

    return validate


def do_not_validate(dialect: str | None = None):
    return lambda *args, **kwargs: None


IMPLEMENTATION = click.option(
    "--implementation",
    "-i",
    "image_names",
    type=lambda name: name if "/" in name else f"{IMAGE_REPOSITORY}/{name}",
    help="A docker image which implements the bowtie IO protocol.",
    multiple=True,
)
DIALECT = click.option(
    "--dialect",
    "-D",
    "dialect",
    help=(
        "A URI or shortname identifying the dialect of each test case."
        f"Shortnames include: {sorted(DIALECT_SHORTNAMES)}."
    ),
    type=lambda dialect: DIALECT_SHORTNAMES.get(dialect, dialect),
    default=LATEST_DIALECT_NAME,
)
FILTER = click.option(
    "-k",
    "filter",
    type=lambda pattern: f"*{pattern}*",
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
    "make_validator",
    # I have no idea why Click makes this so hard, but no combination of:
    #     type, default, is_flag, flag_value, nargs, ...
    # makes this work without doing it manually with callback.
    callback=lambda _, __, v: validator_for_dialect if v else do_not_validate,
    is_flag=True,
    help=(
        "When speaking to implementations (provided via -i), validate "
        "the requests and responses sent to them under Bowtie's JSON Schema "
        "specification. Generally, this option protects against broken Bowtie "
        "implementations and can be left at its default (of off) unless "
        "you are developing a new implementation container."
    ),
)


@main.command()
@click.pass_context
@IMPLEMENTATION
@DIALECT
@FILTER
@FAIL_FAST
@SET_SCHEMA
@VALIDATE
@click.argument(
    "input",
    default="-",
    type=click.File(mode="rb"),
)
def run(context, input, filter, **kwargs):
    """
    Run a sequence of cases provided on standard input.
    """

    cases = (TestCase.from_dict(**json.loads(line)) for line in input)
    if filter:
        cases = (
            case for case in cases if fnmatch(case["description"], filter)
        )

    exit_code = asyncio.run(_run(**kwargs, cases=cases))
    context.exit(exit_code)


@main.command()
@click.pass_context
@IMPLEMENTATION
def smoke(context, **kwargs):
    """
    Smoke test one or more implementations for basic correctness.
    """
    exit_code = asyncio.run(_smoke(**kwargs))
    context.exit(exit_code)


async def _smoke(image_names: list[str]):
    exit_code = 0
    async with _start(
        image_names=image_names,
        make_validator=validator_for_dialect,
        reporter=None,  # FIXME: we don't want to print anything here
    ) as starting:
        for each in asyncio.as_completed(starting):
            implementation = await each
            click.echo(f"Testing {implementation.name!r}...")

            if implementation.metadata is None:
                exit_code |= os.EX_CONFIG
                click.echo("  ❗ (error): startup failed")
                continue

            dialect = implementation.dialects[0]
            runner = await implementation.start_speaking(dialect)

            cases = [
                TestCase(
                    description="allow-everything schema",
                    schema={"$schema": dialect},
                    tests=[
                        Test(description="First", instance=1, valid=True),
                        Test(description="Second", instance="foo", valid=True),
                    ],
                ),
                TestCase(
                    description="allow-nothing schema",
                    schema={"$schema": dialect, "not": {}},
                    tests=[
                        Test(description="First", instance=12, valid=False),
                    ],
                ),
            ]
            for seq, case in enumerate(cases):
                response = await runner.run_case(seq=seq, case=case)
                if response.errored:
                    exit_code |= os.EX_DATAERR
                    message = "❗ (error)"
                elif response.failed:
                    exit_code |= os.EX_DATAERR
                    message = "✗ (failed)"
                else:
                    message = "✓"
                click.echo(f"  {message}: {case.description}")

    if exit_code:
        click.echo("\n❌ some failures")
    else:
        click.echo("\n✅ all passed")

    return exit_code


class _TestSuiteCases(click.ParamType):

    name = "json-schema-org/JSON-Schema-Test-Suite test cases"

    def convert(self, value, param, ctx):
        if not isinstance(value, (Path, str)):
            return value

        is_local_path = not value.casefold().startswith(TEST_SUITE_URL)
        if is_local_path:
            cases, dialect = self._cases_and_dialect(path=Path(value))
        else:
            from github3 import GitHub

            gh = GitHub()
            repo = gh.repository("json-schema-org", "JSON-Schema-Test-Suite")

            _, _, rest = (
                value[len(TEST_SUITE_URL) :].lstrip("/").partition("/")
            )
            ref, sep, partial = rest.partition("/tests")
            data = BytesIO()
            repo.archive(format="zipball", path=data, ref=ref)
            data.seek(0)
            with zipfile.ZipFile(data) as zf:
                (contents,) = zipfile.Path(zf).iterdir()
                path = contents / sep.strip("/") / partial.strip("/")
                cases, dialect = self._cases_and_dialect(path=path)
                cases = list(cases)

        if dialect is not None:
            return cases, dialect

        self.fail(
            f"{value} does not contain JSON Schema Test Suite cases.",
            param,
            ctx,
        )

    def _cases_and_dialect(self, path):
        if path.name.endswith(".json"):
            files, version_path = [path], path.parent
        else:
            files, version_path = _glob(path, "*.json"), path

        remotes = version_path.parent.parent / "remotes"
        cases = suite_cases_from(files=files, remotes=remotes)
        dialect = DIALECT_SHORTNAMES.get(version_path.name)

        return cases, dialect


@main.command()
@click.pass_context
@IMPLEMENTATION
@FILTER
@FAIL_FAST
@SET_SCHEMA
@VALIDATE
@click.argument("input", type=_TestSuiteCases())
def suite(context, input, filter, **kwargs):
    """
    Run test cases from the official JSON Schema test suite.

    Supports file or URL inputs like:

        * ``{ROOT}/tests/draft7`` to run a version's tests

        * ``{ROOT}/tests/draft7/foo.json`` to run just one file

        * ``https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/``
          to run a version directly from a branch which exists in GitHub

        * ``https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/foo.json``
          to run a single file directly from a branch which exists in GitHub
    """  # noqa: E501

    cases, dialect = input
    if filter:
        cases = (
            case for case in cases if fnmatch(case["description"], filter)
        )

    exit_code = asyncio.run(_run(**kwargs, dialect=dialect, cases=cases))
    context.exit(exit_code)


async def _run(
    image_names: list[str],
    cases,
    dialect: str,
    fail_fast: bool,
    set_schema: bool,
    make_validator: callable,
    reporter: _report.Reporter = _report.Reporter(),
):
    reporter.will_speak(dialect=dialect)
    acknowledged, runners, exit_code = [], [], 0
    async with _start(
        image_names=image_names,
        make_validator=make_validator,
        reporter=reporter,
    ) as starting:
        for each in asyncio.as_completed(starting):
            try:
                implementation = await each
            except StartupFailed as error:
                exit_code = os.EX_CONFIG
                reporter.startup_failed(name=error.name)
                continue

            try:
                if dialect in implementation.dialects:
                    try:
                        runner = await implementation.start_speaking(dialect)
                    except GotStderr as error:
                        exit_code = os.EX_CONFIG
                        reporter.dialect_error(
                            implementation=implementation,
                            stderr=error.stderr.decode(),
                        )
                    else:
                        runner.warn_if_unacknowledged(reporter=reporter)
                        acknowledged.append(implementation)
                        runners.append(runner)
                else:
                    reporter.unsupported_dialect(
                        implementation=implementation,
                        dialect=dialect,
                    )
            except StartupFailed as error:
                exit_code = os.EX_CONFIG
                reporter.startup_failed(name=error.name)

        if not runners:
            exit_code = os.EX_CONFIG
            reporter.no_implementations()
        else:
            reporter.ready(implementations=acknowledged, dialect=dialect)

            seq = 0
            should_stop = False
            for seq, case, case_reporter in sequenced(cases, reporter):
                if set_schema and not isinstance(case.schema, bool):
                    case.schema["$schema"] = dialect

                responses = [
                    each.run_case(seq=seq, case=case) for each in runners
                ]
                for each in asyncio.as_completed(responses):
                    response = await each
                    response.report(reporter=case_reporter)

                    if fail_fast:
                        # Stop after this case, since we still have futures out
                        # TODO: Combine this with the logic in the template
                        should_stop = response.errored or response.failed

                if should_stop:
                    break
            reporter.finished(count=seq, did_fail_fast=should_stop)
            if not seq:
                exit_code = os.EX_NOINPUT
    return exit_code


@asynccontextmanager
async def _start(image_names, **kwargs):
    async with AsyncExitStack() as stack:
        docker = await stack.enter_async_context(aiodocker.Docker())

        yield [
            stack.enter_async_context(
                Implementation.start(
                    docker=docker,
                    image_name=image_name,
                    **kwargs,
                ),
            )
            for image_name in image_names
        ]


def sequenced(cases, reporter):
    for seq, case in enumerate(cases, 1):
        yield seq, case, reporter.case_started(seq=seq, case=case)


def suite_cases_from(files, remotes):
    for file in files:
        if file.name == "refRemote.json":
            registry = {
                urljoin(
                    "http://localhost:1234",
                    str(_relative_to(each, remotes)).replace("\\", "/"),
                ): json.loads(each.read_text())
                for each in _rglob(remotes, "*.json")
            }
        else:
            registry = {}

        for case in json.loads(file.read_text()):
            for test in case["tests"]:
                test["instance"] = test.pop("data")
            yield TestCase.from_dict(**case, registry=registry)


def _stderr_processor(file):
    def stderr_processor(logger, method_name, event_dict):
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


def redirect_structlog(file=sys.stderr):
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
        logger_factory=structlog.PrintLoggerFactory(file),
    )


# Missing zipfile.Path methods...
def _glob(path, path_pattern):
    return (  # It's missing .match() too, so we fnmatch directly
        each for each in path.iterdir() if fnmatch(each.name, path_pattern)
    )


def _rglob(path, path_pattern):
    for each in path.iterdir():
        if fnmatch(each.name, path_pattern):
            yield each
        elif each.is_dir():
            yield from _rglob(each, path_pattern)


def _relative_to(path, other):
    if hasattr(path, "relative_to"):
        return path.relative_to(other)
    return Path(path.at).relative_to(other.at)
