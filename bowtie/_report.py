from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
import importlib.metadata
import json
import sys

from attrs import asdict, field, frozen
from rpds import HashTrieMap
from url import URL
import structlog.stdlib

from bowtie._commands import (
    Seq,
    SeqCase,
    SeqResult,
    StartedDialect,
    Unsuccessful,
)
from bowtie._core import TestCase

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from pathlib import Path
    from typing import Any, Self, TextIO

    from bowtie._commands import AnyTestResult, Command, ImplementationId
    from bowtie._core import Implementation, ImplementationInfo, Test


class InvalidReport(Exception):
    """
    The report is invalid.
    """


class EmptyReport(InvalidReport):
    """
    The report was totally empty.
    """


class DuplicateCase(InvalidReport):
    """
    A `Seq` appeared twice in the report.
    """


class MissingFooter(InvalidReport):
    """
    A report is missing its footer.

    Even though that only tells us whether the report failed fast, it might
    mean there's actual data missing too.
    """


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
        response: StartedDialect,
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

    def ready(self, run_metadata: RunMetadata):
        self._write(**run_metadata.serializable())

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
        cmd: Command[Any],
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

    def case_started(self, seq_case: SeqCase):
        log = self._log.bind(
            seq=seq_case.seq,
            case=seq_case.case.description,
            schema=seq_case.case.schema,
        )
        return CaseReporter.case_started(
            seq_case=seq_case,
            write=self._write,
            log=log,
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
        seq_case: SeqCase,
    ) -> CaseReporter:
        self = cls(log=log, write=write)
        self._write(**seq_case.serializable())
        return self

    def got_result(self, result: SeqResult):
        log = self._log.bind(logger_name=result.implementation)
        serialized = result.log_and_be_serialized(log=log)
        self._write(**serialized)


@frozen
class RunMetadata:
    dialect: URL
    implementations: Sequence[ImplementationInfo] = field(
        repr=lambda value: f"({len(value)} implementations)",
        alias="implementations",
    )
    bowtie_version: str = field(
        default=importlib.metadata.version("bowtie-json-schema"),
        eq=False,
        repr=False,
    )
    metadata: Mapping[str, Any] = field(factory=dict, repr=False)
    started: datetime = field(
        factory=lambda: datetime.now(timezone.utc),
        eq=False,
        repr=False,
    )

    @classmethod
    def from_dict(
        cls,
        dialect: str,
        implementations: dict[str, dict[str, Any]],
        started: str | None = None,
        **kwargs: Any,
    ) -> RunMetadata:
        from bowtie._core import ImplementationInfo

        if started is not None:
            kwargs["started"] = datetime.fromisoformat(started)
        return cls(
            dialect=URL.parse(dialect),
            implementations=[
                ImplementationInfo.from_dict(image=image, **data)
                for image, data in implementations.items()
            ],
            **kwargs,
        )

    @property
    def dialect_shortname(self):
        return _DIALECT_URI_TO_SHORTNAME.get(self.dialect, self.dialect)

    def serializable(self):
        as_dict = {k.lstrip("_"): v for k, v in asdict(self).items()}
        as_dict.update(
            dialect=str(as_dict.pop("dialect")),
            started=as_dict.pop("started").isoformat(),
            # FIXME: This transformation is to support the UI parsing
            implementations={
                i.id: i.serializable() for i in self.implementations
            },
        )
        return as_dict


@frozen(eq=False)
class Report:
    r"""
    A Bowtie report, containing (amongst other things) results about cases run.

    In general, reports are assumed to be constructed by calling
    `Report.from_serialized` or an equivalent (i.e. by 'replaying' JSON output
    that was produced by Bowtie).

    When comparing reports (e.g. for equality), only the relative order of
    test cases is considered, not the exact `Seq`\ s used in the run.
    """

    _cases: HashTrieMap[Seq, TestCase] = field(alias="cases", repr=False)
    _results: HashTrieMap[
        ImplementationId,
        HashTrieMap[Seq, SeqResult],
    ] = field(
        repr=False,
        alias="results",
    )
    metadata: RunMetadata
    did_fail_fast: bool

    def __eq__(self, other: object):
        if type(other) is not Report:
            return NotImplemented

        if (  # short circuit for fewer/more cases or differing implementations
            len(self._cases) != len(other._cases)
            or self._results.keys() != other._results.keys()
        ):
            return False

        this, that = asdict(self, recurse=False), asdict(other, recurse=False)

        cases = [v for _, v in sorted(this.pop("_cases").items())]
        if cases != [v for _, v in sorted(that.pop("_cases").items())]:
            return False

        other_results = that.pop("_results")
        for name, results in this.pop("_results").items():
            ordered = [v for _, v in sorted(results.items())]
            if ordered != [v for _, v in sorted(other_results[name].items())]:
                return False
        return this == that

    @classmethod
    def from_input(cls, input: Iterable[Mapping[str, Any]]) -> Self:
        iterator = iter(input)
        header = next(iterator, None)
        if header is None:
            raise EmptyReport()
        metadata = RunMetadata.from_dict(**header)

        cases: HashTrieMap[Seq, TestCase] = HashTrieMap()
        empty: HashTrieMap[Seq, SeqResult] = HashTrieMap()
        ids = (each.id for each in metadata.implementations)
        results = HashTrieMap.fromkeys(ids, empty)

        for data in iterator:
            match data:
                case {"seq": Seq(seq), "case": case}:
                    if seq in cases:
                        raise DuplicateCase(seq)
                    case = TestCase.from_dict(dialect=metadata.dialect, **case)
                    cases = cases.insert(seq, case)
                    continue
                case {"did_fail_fast": did_fail_fast}:
                    return cls(
                        results=results,
                        cases=cases,
                        metadata=metadata,
                        did_fail_fast=did_fail_fast,
                    )
                case _:
                    result = SeqResult.from_dict(**data)

            current = results.get(result.implementation, HashTrieMap())
            results = results.insert(  # TODO: Complain if present
                result.implementation,
                current.insert(result.seq, result),
            )

        raise MissingFooter()

    @classmethod
    def from_serialized(cls, serialized: Iterable[str]) -> Self:
        return cls.from_input(json.loads(line) for line in serialized)

    @classmethod
    def empty(
        cls,
        implementations: Sequence[ImplementationInfo] = (),
        **kwargs: Any,
    ):
        """
        'The' empty report.
        """
        return cls(
            cases=HashTrieMap(),
            results=HashTrieMap(),
            metadata=RunMetadata(implementations=implementations, **kwargs),
            did_fail_fast=False,
        )

    @property
    def implementations(self) -> Sequence[ImplementationInfo]:
        return self.metadata.implementations

    @property
    def is_empty(self):
        return not self._cases

    @property
    def total_tests(self):
        return sum(len(case.tests) for case in self._cases.values())

    def unsuccessful(self, implementation: ImplementationId) -> Unsuccessful:
        """
        A count of the unsuccessful tests for the given implementation.
        """
        results = self._results[implementation].values()
        return sum((each.unsuccessful() for each in results), Unsuccessful())

    def worst_to_best(self):
        """
        All implementations ordered by number of unsuccessful tests.

        Ties are then broken alphabetically.
        """
        unsuccessful = [
            (implementation, self.unsuccessful(implementation.id))
            for implementation in self.implementations
        ]
        unsuccessful.sort(key=lambda each: (each[1].total, each[0].name))
        return unsuccessful

    def cases_with_results(
        self,
    ) -> Iterable[
        tuple[
            TestCase,
            Iterable[tuple[Test, Mapping[str, AnyTestResult]]],
        ]
    ]:
        for seq, case in sorted(self._cases.items()):
            test_results: list[tuple[Test, Mapping[str, AnyTestResult]]] = []
            for i, test in enumerate(case.tests):
                test_result = {
                    each.id: self._results[each.id][seq].result_for(i)
                    for each in self.implementations
                }
                test_results.append((test, test_result))
            yield case, test_results

    def generate_badges(self, target_dir: Path):
        label = _DIALECT_URI_TO_SHORTNAME[self.metadata.dialect]
        total = self.total_tests
        for implementation in self.implementations:
            if self.metadata.dialect not in implementation.dialects:
                continue
            shortnames = (
                _DIALECT_URI_TO_SHORTNAME[each].removeprefix("Draft ")
                for each in implementation.dialects
            )
            supported = ", ".join(sorted(shortnames))  # FIXME: proper sort
            unsuccessful = self.unsuccessful(implementation.id)
            passed = total - unsuccessful.total
            pct = (passed / total) * 100
            r, g, b = 100 - int(pct), int(pct), 0
            badge_per_draft = {
                "schemaVersion": 1,
                "label": label,
                "message": "%d%% Passing" % int(pct),
                "color": f"{r:02x}{g:02x}{b:02x}",
            }
            impl_dir = f"{implementation.language}-{implementation.name}"
            supp_dir = target_dir / impl_dir
            comp_dir = supp_dir / "compliance"
            comp_dir.mkdir(parents=True, exist_ok=True)
            badge_path_per_draft = comp_dir / f"{label.replace(' ', '_')}.json"
            badge_path_per_draft.write_text(json.dumps(badge_per_draft))
            badge_supp_draft = {
                "schemaVersion": 1,
                "label": "JSON Schema Versions",
                "message": supported,
                "color": "lightgreen",
            }
            badge_supported = supp_dir / "supported_versions.json"
            badge_supported.write_text(json.dumps(badge_supp_draft))
