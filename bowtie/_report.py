from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, TextIO, TypedDict
import importlib.metadata
import json
import sys

from attrs import asdict, field, frozen, mutable
from url import URL
import structlog.stdlib

from bowtie import _commands

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from pathlib import Path

    from bowtie._core import Implementation


class EmptyReport(Exception):
    pass


class _InvalidBowtieReport(Exception):
    pass


_DIALECT_URI_TO_SHORTNAME = {
    URL.parse("https://json-schema.org/draft/2020-12/schema"): "Draft 2020-12",
    URL.parse("https://json-schema.org/draft/2019-09/schema"): "Draft 2019-09",
    URL.parse("http://json-schema.org/draft-07/schema#"): "Draft 7",
    URL.parse("http://json-schema.org/draft-06/schema#"): "Draft 6",
    URL.parse("http://json-schema.org/draft-04/schema#"): "Draft 4",
    URL.parse("http://json-schema.org/draft-03/schema#"): "Draft 3",
}


def writer(file: TextIO = sys.stdout) -> Callable[..., Any]:
    return lambda **result: file.write(f"{json.dumps(result)}\n")  # type: ignore[reportUnknownArgumentType]


@frozen
class Reporter:
    _write: Callable[..., Any] = field(default=writer(), alias="write")
    _log: structlog.stdlib.BoundLogger = field(
        factory=structlog.stdlib.get_logger,
    )

    def unsupported_dialect(
        self,
        implementation: Implementation,
        dialect: URL,
    ):
        self._log.warn(
            "Unsupported dialect, skipping implementation.",
            logger_name=implementation.name,
            dialect=dialect,
        )

    def unacknowledged_dialect(
        self,
        implementation: str,
        dialect: URL,
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
        self._write(**run_info.serializable())

    def will_speak(self, dialect: URL):
        self._log.debug("Will speak", dialect=dialect)

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
            response=response,
        )

    def case_started(self, seq: _commands.Seq, case: _commands.TestCase):
        return CaseReporter.case_started(
            case=case,
            seq=seq,
            write=self._write,
            log=self._log.bind(
                seq=seq,
                case=case.description,
                schema=case.schema,
            ),
        )


@frozen
class CaseReporter:
    _write: Callable[..., Any] = field(alias="write")
    _log: structlog.stdlib.BoundLogger = field(alias="log")

    @classmethod
    def case_started(
        cls,
        log: structlog.stdlib.BoundLogger,
        write: Callable[..., None],
        case: _commands.TestCase,
        seq: _commands.Seq,
    ) -> CaseReporter:
        self = cls(log=log, write=write)
        self._write(case=case.serializable(), seq=seq)
        return self

    def got_results(self, results: _commands.CaseResult):
        for result in results.results:
            if result.errored:
                self._log.error(
                    "",
                    logger_name=results.implementation,
                    **result.context,  # type: ignore[reportGeneralTypeIssues]
                )
        self._write(**asdict(results))

    def skipped(self, skipped: _commands.CaseSkipped):
        self._write(**asdict(skipped))

    def no_response(self, implementation: str):
        self._log.error("No response", logger_name=implementation)

    def case_errored(self, results: _commands.CaseErrored):
        implementation, context = results.implementation, results.context
        message = "" if results.caught else "uncaught error"
        self._log.error(message, logger_name=implementation, **context)
        self._write(**asdict(results))


@mutable
class Count:
    total_cases: int = 0
    errored_cases: int = 0

    total_tests: int = 0
    failed_tests: int = 0
    errored_tests: int = 0
    skipped_tests: int = 0

    @property
    def unsuccessful_tests(self):
        """
        Any test which was not a successful result, including skips.
        """
        return self.errored_tests + self.failed_tests + self.skipped_tests


@mutable
class _Summary:
    implementations: Iterable[dict[str, Any]] = field(
        converter=lambda value: sorted(  # type: ignore[reportUnknownArgumentType]
            value,  # type: ignore[reportUnknownArgumentType]
            key=lambda each: (each["language"], each["name"]),  # type: ignore[reportUnknownArgumentType]
        ),
    )
    _combined: dict[int, Any] = field(factory=dict)
    did_fail_fast: bool = False
    counts: dict[str, Count] = field(init=False)

    def __attrs_post_init__(self) -> None:
        self.counts = {each["image"]: Count() for each in self.implementations}

    @property
    def is_empty(self):
        return self.total_tests == 0

    @property
    def total_cases(self):
        counts = {count.total_cases for count in self.counts.values()}
        if len(counts) != 1:
            summary = "  \n".join(
                f"  {each.rpartition('/')[2]}: {count.total_cases}"
                for each, count in self.counts.items()
            )
            raise _InvalidBowtieReport(  # noqa: TRY003
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
            raise _InvalidBowtieReport(  # noqa: TRY003
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

    def add_case_metadata(self, seq: _commands.Seq, case: dict[str, Any]):
        results: list[tuple[Any, dict[str, tuple[str, str]]]] = [
            (test, {}) for test in case["tests"]
        ]
        self._combined[seq] = dict(case=case, results=results)

    def see_error(
        self,
        implementation: str,
        seq: _commands.Seq,
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
                seen[result.implementation] = test.reason, "skipped"  # type: ignore[reportGeneralTypeIssues]
            elif test.errored:
                count.errored_tests += 1
                seen[result.implementation] = test.reason, "errored"  # type: ignore[reportGeneralTypeIssues]
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
        return (
            (each["case"], each.get("registry", {}), each["results"])
            for each in self._combined.values()
        )

    def flat_results(self):
        for seq, each in sorted(self._combined.items()):
            case = each["case"]
            yield (
                seq,
                case["description"],
                case["schema"],
                case["registry"],
                each["results"],
            )

    def generate_badges(self, target_dir: Path, dialect: URL):
        label = _DIALECT_URI_TO_SHORTNAME[dialect]
        total = self.total_tests
        for impl in self.implementations:
            dialect_versions = [URL.parse(each) for each in impl["dialects"]]
            if dialect not in dialect_versions:
                continue
            supported_drafts = ", ".join(
                _DIALECT_URI_TO_SHORTNAME[each].removeprefix("Draft ")
                for each in reversed(dialect_versions)
            )
            name = impl["name"]
            lang = impl["language"]
            counts = self.counts[impl["image"]]
            passed = (
                total
                - counts.failed_tests
                - counts.errored_tests
                - counts.skipped_tests
            )
            pct = (passed / total) * 100
            r, g, b = 100 - int(pct), int(pct), 0
            badge_per_draft = {
                "schemaVersion": 1,
                "label": label,
                "message": "%d%% Passing" % int(pct),
                "color": f"{r:02x}{g:02x}{b:02x}",
            }
            comp_dir = target_dir / f"{lang}-{name}" / "compliance"
            comp_dir.mkdir(parents=True, exist_ok=True)
            badge_path_per_draft = comp_dir / f"{label.replace(' ', '_')}.json"
            badge_path_per_draft.write_text(json.dumps(badge_per_draft))
            badge_supp_draft = {
                "schemaVersion": 1,
                "label": "JSON Schema Versions",
                "message": supported_drafts,
                "color": "lightgreen",
            }
            supp_dir = target_dir / f"{lang}-{name}"
            badge_path_supp_drafts = supp_dir / "supported_versions.json"
            badge_path_supp_drafts.write_text(json.dumps(badge_supp_draft))


@frozen
class RunInfo:
    started: str
    bowtie_version: str
    dialect: URL
    _implementations: dict[str, dict[str, Any]] = field(
        alias="implementations",
    )
    metadata: dict[str, Any] = field(factory=dict)

    @classmethod
    def from_dict(cls, dialect: str, **kwargs: Any) -> RunInfo:
        return cls(dialect=URL.parse(dialect), **kwargs)

    @classmethod
    def from_implementations(
        cls,
        implementations: Iterable[Implementation],
        **kwargs: Any,
    ) -> RunInfo:
        return cls(
            bowtie_version=importlib.metadata.version("bowtie-json-schema"),
            started=datetime.now(timezone.utc).isoformat(),
            implementations={
                implementation.name: dict(
                    implementation.metadata or {},
                    image=implementation.name,
                )
                for implementation in implementations
            },
            **kwargs,
        )

    @property
    def dialect_shortname(self):
        return _DIALECT_URI_TO_SHORTNAME.get(self.dialect, self.dialect)

    def create_summary(self) -> _Summary:
        """
        Create a summary object used to incrementally parse reports.
        """
        return _Summary(implementations=self._implementations.values())

    def serializable(self):
        as_dict = {k.lstrip("_"): v for k, v in asdict(self).items()}
        as_dict["dialect"] = str(as_dict["dialect"])
        return as_dict


class ReportData(TypedDict):
    summary: _Summary
    run_info: RunInfo


def from_input(input: Iterable[str]) -> ReportData:
    """
    Create a structure suitable for the report template from an input file.
    """
    lines = (json.loads(line) for line in input)
    header = next(lines, None)
    if header is None:
        raise EmptyReport()
    run_info = RunInfo.from_dict(**header)
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
