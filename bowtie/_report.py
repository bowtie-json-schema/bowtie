from __future__ import annotations

from collections.abc import Iterable
import json
import sys

import attrs
import structlog

from bowtie import _commands


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
        self._write(implementations=metadata)

    def will_speak(self, dialect):
        self._log.info("Will speak dialect", dialect=dialect)

    def finished(self, count):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)

    def startup_failed(self, name):
        self._log.error("Startup failed!", logger_name=name)

    def dialect_error(self, implementation, stderr):
        self._log.error(
            "Tried to start sending test cases, but got an error.",
            logger_name=implementation.name,
            stderr=stderr,
        )

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
class Summary:

    implementations: Iterable[str]
    _combined: dict = attrs.field(factory=dict)

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

    def combined(self):
        return [(v, k) for k, v in sorted(self._combined.items())]


def from_input(input):
    """
    Create a structure suitable for the report template from an input file.
    """

    lines = (json.loads(line) for line in input)
    header = next(lines)
    summary = Summary(implementations=header["implementations"].values())

    for each in lines:
        if "case" in each:
            summary.add_case_metadata(**each)
        elif "caught" in each:
            summary.see_error(**each)
        else:
            summary.see_results(**each)
    return dict(summary=summary, results=summary.combined())
