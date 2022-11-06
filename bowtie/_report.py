from __future__ import annotations

from collections.abc import Iterable
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


@attrs.define
class Reporter:

    _write = attrs.field(default=writer())
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

    def ready(self, implementations, dialect):
        metadata = {
            implementation.name: dict(
                implementation.metadata,
                image=implementation.name,
            )
            for implementation in implementations
        }
        self._write(
            implementations=metadata,
            bowtie_version=importlib.metadata.version("bowtie-json-schema"),
        )

    def will_speak(self, dialect):
        self._write(dialect=dialect)

    def finished(self, count, did_fail_fast):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)
        self._write(did_fail_fast=did_fail_fast)

    def startup_failed(self, name):
        self._log.exception("Startup failed!", logger_name=name)

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


@attrs.define
class _CaseReporter:

    _write: callable
    _log: structlog.BoundLogger

    @classmethod
    def case_started(cls, log, write, case: _commands.TestCase, seq: int):
        self = cls(log=log, write=write)
        self._write(case=attrs.asdict(case), seq=seq)
        return self

    def got_results(self, results):
        self._write(**attrs.asdict(results))

    def no_response(self, implementation):
        self._log.error("No response", logger_name=implementation)

    def errored(self, results: _commands.CaseErrored):
        implementation, context = results.implementation, results.context
        message = "" if results.caught else "uncaught error"
        self._log.error(message, logger_name=implementation, **context)
        self.got_results(results)


@attrs.define
class Count:

    total_cases: int = 0
    errored_cases: int = 0

    total_tests: int = 0
    failed_tests: int = 0
    errored_tests: int = 0
    skipped_tests: int = 0


@attrs.define(slots=False)
class _Summary:

    implementations: Iterable[str]
    _combined: dict = attrs.field(factory=dict)
    did_fail_fast: bool = False

    def __attrs_post_init__(self):
        self.implementations = sorted(
            self.implementations,
            key=lambda each: (each["language"], each["name"]),
        )
        self.counts = {each["image"]: Count() for each in self.implementations}

    @property
    def total_cases(self):
        return sum(count.total_cases for count in self.counts.values())

    @property
    def errored_cases(self):
        return sum(count.errored_cases for count in self.counts.values())

    @property
    def total_tests(self):
        return sum(count.total_tests for count in self.counts.values())

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

    def see_results(self, implementation, seq, results, expected):
        count = self.counts[implementation]
        count.total_cases += 1

        got = self._combined[seq]["results"]

        for result, valid, (_, seen) in zip(results, expected, got):
            count.total_tests += 1
            failed = expected is not None and result["valid"] != valid
            if failed:
                count.failed_tests += 1
            seen[implementation] = result, failed

    def see_maybe_fail_fast(self, did_fail_fast):
        self.did_fail_fast = did_fail_fast

    def case_results(self):
        for seq, each in sorted(self._combined.items()):
            case, results = each["case"], each["results"]
            yield seq, case["description"], case["schema"], results


@attrs.define
class RunInfo:

    bowtie_version: str
    dialect: str
    _implementations: dict[str, dict]

    @classmethod
    def from_header_lines(cls, first, second):
        return cls(**first, **second)

    def create_summary(self):
        """
        Create a summary object used to incrementally parse reports.
        """
        return _Summary(implementations=self._implementations.values())


def from_input(input):
    """
    Create a structure suitable for the report template from an input file.
    """

    lines = (json.loads(line) for line in input)
    run_info = RunInfo.from_header_lines(next(lines), next(lines))
    summary = run_info.create_summary()

    for each in lines:
        if "case" in each:
            summary.add_case_metadata(**each)
        elif "caught" in each:
            summary.see_error(**each)
        elif "did_fail_fast" in each:
            summary.see_maybe_fail_fast(**each)
        else:
            summary.see_results(**each)
    return dict(summary=summary, run_info=run_info)
