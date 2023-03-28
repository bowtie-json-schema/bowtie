from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, TextIO, TypedDict
import importlib.metadata
import json
import sys

import attrs
import structlog.stdlib

from bowtie import _commands

if TYPE_CHECKING:
    from bowtie._core import Implementation


class _InvalidBowtieReport(Exception):
    pass


DRAFT2020 = "https://json-schema.org/draft/2020-12/schema"
DRAFT2019 = "https://json-schema.org/draft/2019-09/schema"
DRAFT7 = "http://json-schema.org/draft-07/schema#"
DRAFT6 = "http://json-schema.org/draft-06/schema#"
DRAFT4 = "http://json-schema.org/draft-04/schema#"
DRAFT3 = "http://json-schema.org/draft-03/schema#"


DIALECT_REVERSE_MAPPING = {
    DRAFT2020: "Draft 2020-12",
    DRAFT2019: "Draft 2019-09",
    DRAFT7: "Draft 7",
    DRAFT6: "Draft 6",
    DRAFT4: "Draft 4",
    DRAFT3: "Draft 3",
}

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


def writer(file: TextIO = sys.stdout) -> Callable[..., Any]:
    return lambda **result: file.write(f"{json.dumps(result)}\n")


@attrs.frozen
class Reporter:
    _write: Callable[..., Any] = attrs.field(default=writer())
    _log: structlog.stdlib.BoundLogger = attrs.field(
        factory=structlog.stdlib.get_logger,
    )

    def unsupported_dialect(
        self,
        implementation: Implementation,
        dialect: str,
    ):
        self._log.warn(
            "Unsupported dialect, skipping implementation.",
            logger_name=implementation.name,
            dialect=dialect,
        )

    def unacknowledged_dialect(
        self,
        implementation: str,
        dialect: str,
        response: Any,
    ):
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

    def ready(self, run_info: RunInfo):
        self._write(
            **{k.lstrip("_"): v for k, v in attrs.asdict(run_info).items()},
        )

    def will_speak(self, dialect: str):
        self._log.info("Will speak", dialect=dialect)

    def finished(self, count: int, did_fail_fast: bool):
        if not count:
            self._log.error("No test cases ran.")
        else:
            self._log.info("Finished", count=count)
        self._write(did_fail_fast=did_fail_fast)

    def no_such_image(self, name: str):
        self._log.error("Not a known Bowtie implementation.", logger_name=name)

    def startup_failed(self, name: str, stderr: str):
        self._log.exception(
            "Startup failed!",
            logger_name=name,
            **{"stderr": stderr} if stderr else {},
        )

    def dialect_error(self, implementation: Implementation, stderr: str):
        self._log.error(
            "Tried to start sending test cases, but got an error.",
            logger_name=implementation.name,
            stderr=stderr,
        )

    def no_implementations(self):
        self._log.error("No implementations started successfully!")

    def invalid_response(
        self,
        cmd: _commands.Command[Any],
        response: bytes,
        implementation: Implementation,
        error: Exception,
    ):
        self._log.exception(
            "Invalid response",
            logger_name=implementation.name,
            exc_info=error,
            request=cmd,
        )

    def case_started(self, seq: int, case: _commands.TestCase):
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
    _write: Callable[..., Any] = attrs.field(alias="write")
    _log: structlog.stdlib.BoundLogger = attrs.field(alias="log")

    @classmethod
    def case_started(
        cls,
        log: structlog.stdlib.BoundLogger,
        write: Callable[..., None],
        case: _commands.TestCase,
        seq: int,
    ):
        self = cls(log=log, write=write)
        self._write(case=attrs.asdict(case), seq=seq)
        return self

    def got_results(
        self,
        results: _commands.CaseResult | _commands.CaseErrored,
    ):
        self._write(**attrs.asdict(results))

    def skipped(self, skipped: _commands.CaseSkipped):
        self._write(**attrs.asdict(skipped))

    def no_response(self, implementation: str):
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
    _combined: dict[int, Any] = attrs.field(factory=dict)
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

    def add_case_metadata(self, seq: int, case: dict[str, Any]):
        results: list[tuple[Any, dict[str, tuple[str, str]]]] = [
            (test, {}) for test in case["tests"]
        ]
        self._combined[seq] = dict(case=case, results=results)

    def see_error(
        self,
        implementation: str,
        seq: int,
        context: dict[str, Any],
        caught: bool,
    ):
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

    def see_maybe_fail_fast(self, did_fail_fast: bool):
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
    _implementations: dict[str, dict[str, Any]] = attrs.field(
        alias="implementations",
    )

    @classmethod
    def from_implementations(
        cls,
        implementations: Iterable[Implementation],
        dialect: str,
    ):
        return cls(
            dialect=dialect,
            bowtie_version=importlib.metadata.version("bowtie-json-schema"),
            started=datetime.now(timezone.utc).isoformat(),
            implementations={
                implementation.name: dict(
                    implementation.metadata or {},
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


def from_input(input: Iterable[str]) -> ReportData:
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


def badges(report: ReportData):
    summary = report["summary"]
    dialect = report["run_info"].dialect

    counts = (
        (
            (implementation["name"], implementation["language"]),
            summary.counts[implementation["image"]],
        )
        for implementation in summary.implementations
    )

    combined = [
        (
            metadata,
            {
                "passing_percentage": (
                    each.total_tests
                    - each.failed_tests
                    - each.skipped_tests
                    - each.errored_tests
                )
                / each.total_tests,
            },
        )
        for metadata, each in counts
    ]
    passing_percentage_float = combined[0][1]["passing_percentage"]
    passing_percentage = f"{combined[0][1]['passing_percentage']:.2%}"

    if passing_percentage_float in range(90, 100):
        color = "success"
    elif passing_percentage_float in range(80, 100):
        color = "important"
    else:
        color = "critical"

    return {
        "schemaVersion": 1,
        "label": DIALECT_REVERSE_MAPPING[dialect],
        "message": passing_percentage,
        "color": color,
    }
