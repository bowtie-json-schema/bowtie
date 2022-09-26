import json
import sys

import attrs
import structlog

from bowtie._commands import TestCase


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
            logger_name=implementation.name,
            dialect=dialect,
            response=response,
        )

    def ready(self, implementations, dialect):
        metadata = {
            implementation.name: dict(
                implementation.metadata, image=implementation.name,
            ) for implementation in implementations
        }
        self._write(implementations=metadata)

    def will_speak(self, dialect):
        self._log.info("Will speak dialect", dialect=dialect)

    def finished(self, count):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.msg("Finished", count=count)

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
    def case_started(cls, log, write, case: TestCase, seq: int):
        self = cls(log=log, write=write)
        self._write(case=attrs.asdict(case), seq=seq)
        return self

    def got_results(self, results):
        self._write(**attrs.asdict(results))

    def backoff(self, implementation):
        self._log.warn("backing off", logger_name=implementation)

    def no_response(self, implementation):
        self._log.error("No response", logger_name=implementation)

    def errored(self, implementation, response):
        self._log.error("", logger_name=implementation, **response)

    def errored_uncaught(self, implementation, **response):
        self._log.error("uncaught", logger_name=implementation, **response)


def from_input(input):
    """
    Create a structure suitable for the report template from an input file.
    """

    lines = (json.loads(line) for line in input)
    header = next(lines)
    implementations = header["implementations"]

    combined = {}

    for each in lines:
        if "case" in each:
            combined[each["seq"]] = {
                "case": each["case"],
                "results": [(test, {}) for test in each["case"]["tests"]],
            }
            continue

        implementation = each.pop("implementation")
        case = combined[each["seq"]]

        for result, expected, (_, seen) in zip(
            each["results"],
            each["expected"],
            case["results"],
        ):
            incorrect = expected is not None and result["valid"] != expected
            seen[implementation] = result, incorrect

    return dict(
        implementations=implementations.values(),
        results=[(v, k) for k, v in sorted(combined.items())],
    )
