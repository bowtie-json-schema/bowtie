from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import Any, TypedDict
import importlib.metadata
import json
import sys

import attrs
import structlog

from bowtie import _commands


class _InvalidBowtieReport(Exception):
    pass


def writer(file=sys.stdout):
    return lambda **result: file.write(f"{json.dumps(result)}\n")


@attrs.frozen
class Reporter:

    _write: Callable = attrs.field(default=writer())
    _log: structlog.BoundLogger = attrs.field(factory=structlog.get_logger)

    def unsupported_dialect(self, implementation, dialect):
        self._log.warn(
            "Unsupported dialect, skipping implementation.",
            logger_name=implementation.name,
            dialect=dialect,
        )

    def unacknowledged_dialect(self, implementation, dialect, response):
        self._log.warn(
            (
                "Implicit dialect not acknowledged. "
                "Proceeding, but implementation may not have configured "
                "itself to handle schemas without $schema."
            ),
            logger_name=implementation,
            dialect=dialect,
            response=response,
        )

    def ready(self, run_info):
        self._write(
            **{k.lstrip("_"): v for k, v in attrs.asdict(run_info).items()},
        )

    def will_speak(self, dialect):
        self._log.info("Will speak", dialect=dialect)

    def finished(self, count, did_fail_fast):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)
        self._write(did_fail_fast=did_fail_fast)

    def no_such_image(self, name):
        self._log.error("Not a known Bowtie implementation.", logger_name=name)

    def startup_failed(self, name, stderr):
        self._log.exception("Startup failed!", logger_name=name, stderr=stderr)

    def dialect_error(self, implementation, stderr):
        self._log.error(
            "Tried to start sending test cases, but got an error.",
            logger_name=implementation.name,
            stderr=stderr,
        )

    def no_implementations(self):
        self._log.error("No implementations started successfully!")

    def invalid_response(self, request, response, implementation, error):
        self._log.exception(
            "Invalid response",
            logger_name=implementation.name,
            exc_info=error,
            request=request,
        )

    def case_started(self, seq, case):
        return _CaseReporter.case_started(
            case=case,
            seq=seq,
            write=self._write,
            log=self._log.bind(
                seq=seq,
                case=case.description,
                schema=case.schema,
            ),
        )


@attrs.frozen
class _CaseReporter:

    _write: Callable = attrs.field(alias="write")
    _log: structlog.BoundLogger = attrs.field(alias="log")

    @classmethod
    def case_started(cls, log, write, case: _commands.TestCase, seq: int):
        self = cls(log=log, write=write)
        self._write(case=attrs.asdict(case), seq=seq)
        return self

    def got_results(self, results):
        self._write(**attrs.asdict(results))

    def skipped(self, skipped):
        self._write(**attrs.asdict(skipped))

    def no_response(self, implementation):
        self._log.error("No response", logger_name=implementation)

    def errored(self, results: _commands.CaseErrored):
        implementation, context = results.implementation, results.context
        message = "" if results.caught else "uncaught error"
        self._log.error(message, logger_name=implementation, **context)
        self.got_results(results)


@attrs.mutable
class Count:

    total_cases: int = 0
    errored_cases: int = 0

    total_tests: int = 0
    failed_tests: int = 0
    errored_tests: int = 0
    skipped_tests: int = 0


@attrs.mutable
class _Summary:

    implementations: Iterable[dict[str, Any]] = attrs.field(
        converter=lambda value: sorted(
            value,
            key=lambda each: (each["language"], each["name"]),
        ),
    )
    _combined: dict = attrs.field(factory=dict)
    did_fail_fast: bool = False
    counts: dict[str, Count] = attrs.field(init=False)

    def __attrs_post_init__(self):
        self.counts = {each["image"]: Count() for each in self.implementations}

    @property
    def total_cases(self):
        counts = {count.total_cases for count in self.counts.values()}
        if len(counts) != 1:
            summary = "  \n".join(
                f"  {each.rpartition('/')[2]}: {count.total_cases}"
                for each, count in self.counts.items()
            )
            raise _InvalidBowtieReport(
                f"Inconsistent number of cases run:\n\n{summary}",
            )
        return counts.pop()

    @property
    def errored_cases(self):
        return sum(count.errored_cases for count in self.counts.values())

    @property
    def total_tests(self):
        counts = {count.total_tests for count in self.counts.values()}
        if len(counts) != 1:
            raise _InvalidBowtieReport(
                f"Inconsistent number of tests run: {self.counts}",
            )
        return counts.pop()

    @property
    def failed_tests(self):
        return sum(count.failed_tests for count in self.counts.values())

    @property
    def errored_tests(self):
        return sum(count.errored_tests for count in self.counts.values())

    @property
    def skipped_tests(self):
        return sum(count.skipped_tests for count in self.counts.values())

    def add_case_metadata(self, seq, case):
        self._combined[seq] = dict(
            case=case,
            results=[(test, {}) for test in case["tests"]],
        )

    def see_error(self, implementation, seq, context, caught):
        count = self.counts[implementation]
        count.total_cases += 1
        count.errored_cases += 1

        case = self._combined[seq]["case"]
        count.total_tests += len(case["tests"])
        count.errored_tests += len(case["tests"])

    def see_result(self, result: _commands.CaseResult):
        count = self.counts[result.implementation]
        count.total_cases += 1

        combined = self._combined[result.seq]["results"]

        for (test, failed), (_, seen) in zip(result.compare(), combined):
            count.total_tests += 1
            if test.skipped:
                count.skipped_tests += 1
                seen[result.implementation] = test.reason, "skipped"  # type: ignore[reportGeneralTypeIssues]  # noqa: E501
            elif test.errored:
                count.errored_tests += 1
                seen[result.implementation] = test.reason, "errored"  # type: ignore[reportGeneralTypeIssues]  # noqa: E501
            else:
                if failed:
                    count.failed_tests += 1
                seen[result.implementation] = test, failed

    def see_skip(self, skipped: _commands.CaseSkipped):
        count = self.counts[skipped.implementation]
        count.total_cases += 1

        case = self._combined[skipped.seq]["case"]
        count.total_tests += len(case["tests"])
        count.skipped_tests += len(case["tests"])

        for _, seen in self._combined[skipped.seq]["results"]:
            message = skipped.issue_url or skipped.message or "skipped"
            seen[skipped.implementation] = message, "skipped"

    def see_maybe_fail_fast(self, did_fail_fast):
        self.did_fail_fast = did_fail_fast

    def case_results(self):
        for seq, each in sorted(self._combined.items()):
            case, results = each["case"], each["results"]
            yield seq, case["description"], case["schema"], results


@attrs.frozen
class RunInfo:

    started: str
    bowtie_version: str
    dialect: str
    _implementations: dict[str, dict] = attrs.field(alias="implementations")

    @classmethod
    def from_implementations(cls, implementations, dialect):
        return cls(
            dialect=dialect,
            bowtie_version=importlib.metadata.version("bowtie-json-schema"),
            started=datetime.now(timezone.utc).isoformat(),
            implementations={
                implementation.name: dict(
                    implementation.metadata,
                    image=implementation.name,
                )
                for implementation in implementations
            },
        )

    def create_summary(self) -> _Summary:
        """
        Create a summary object used to incrementally parse reports.
        """
        return _Summary(implementations=self._implementations.values())


class ReportData(TypedDict):
    summary: _Summary
    run_info: RunInfo


def from_input(input) -> ReportData:
    """
    Create a structure suitable for the report template from an input file.
    """

    lines = (json.loads(line) for line in input)
    run_info = RunInfo(**next(lines))
    summary = run_info.create_summary()

    for each in lines:
        if "case" in each:
            summary.add_case_metadata(**each)
        elif "caught" in each:
            summary.see_error(**each)
        elif "skipped" in each:
            del each["skipped"]
            summary.see_skip(_commands.CaseSkipped(**each))
        elif "did_fail_fast" in each:
            summary.see_maybe_fail_fast(**each)
        else:
            summary.see_result(_commands.CaseResult.from_dict(each))
    return ReportData(summary=summary, run_info=run_info)
