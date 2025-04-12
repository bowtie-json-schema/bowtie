from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, TypedDict
import importlib.metadata
import json
import sys

from attrs import asdict, field, frozen
from attrs.filters import exclude
from rpds import HashTrieMap
from url import URL
import structlog.stdlib

from bowtie._commands import Seq, SeqCase, SeqResult, Unsuccessful
from bowtie._core import Dialect, TestCase, sortable_version_key
from bowtie._direct_connectable import Direct

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from typing import Any, Literal, Self, TextIO

    from bowtie._commands import AnyTestResult
    from bowtie._connectables import ConnectableId
    from bowtie._core import Example, ImplementationInfo, Test


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


def writer(file: TextIO = sys.stdout) -> Callable[..., Any]:
    return lambda **result: file.write(f"{json.dumps(result)}\n")  # type: ignore[reportUnknownArgumentType]


@frozen
class Reporter:
    _write: Callable[..., Any] = field(default=writer(), alias="write")
    _log: structlog.stdlib.BoundLogger = field(
        factory=structlog.stdlib.get_logger,
    )

    def schema_without_dialect(
        self,
        implementation: str,
        dialect: Dialect,
        schema: Any,
    ):
        self._log.warn(
            (
                f"The schema {schema!r} does not indicate its dialect via "
                "the $schema keyword. "
                f"This implementation does not support external dialect "
                "configuration, so validation results may not properly "
                "take the current dialect into account."
            ),
            logger_name=implementation,
            dialect=dialect.pretty_name,
        )

    def ready(self, run_metadata: RunMetadata):
        self._log.debug("Will speak", dialect=run_metadata.dialect)
        self._write(**run_metadata.serializable())

    def finished(self, did_fail_fast: bool):
        self._write(did_fail_fast=did_fail_fast)

    def case_started(self, seq_case: SeqCase, dialect: Dialect):
        self._write(**seq_case.serializable())
        log = self._log.bind(
            case=seq_case.case.description,
            schema=seq_case.case.schema,
        )

        if not seq_case.matches_dialect(dialect):
            log.warning(
                "$schema keyword does not seem to match the expected dialect",
                expected=dialect,
            )

        def got_result(result: SeqResult):
            bound = log.bind(logger_name=result.implementation)
            serialized = result.log_and_be_serialized(log=bound)
            self._write(**serialized)

        return got_result


@frozen
class RunMetadata:
    dialect: Dialect
    implementations: Mapping[ConnectableId, ImplementationInfo] = field(
        repr=lambda value: (
            f"({len(value)} implementation{'s' if len(value) != 1 else ''})"
        ),
        alias="implementations",
    )
    bowtie_version: str = field(
        default=importlib.metadata.version("bowtie-json-schema"),
        eq=False,
        repr=False,
    )
    metadata: Mapping[str, Any] = field(factory=dict, repr=False)  # type: ignore[reportUnknownVariableType]
    started: datetime = field(
        factory=lambda: datetime.now(UTC),
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
            dialect=Dialect.from_str(dialect),
            implementations={
                id: ImplementationInfo.from_dict(**data)
                for id, data in implementations.items()
            },
            **kwargs,
        )

    def serializable(self):
        as_dict = asdict(
            self,
            filter=exclude("dialect"),
            recurse=False,
        )
        as_dict.update(
            dialect=self.dialect.serializable(),
            started=as_dict.pop("started").isoformat(),
            # FIXME: This transformation is to support the UI parsing
            implementations={
                id: implementation.serializable()
                for id, implementation in self.implementations.items()
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
        ConnectableId,
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
        # TODO: Support some interface for enabling/disabling validation.
        validator = (
            Direct.from_id("python-jsonschema")
            .registry()
            .for_uri(
                URL.parse("tag:bowtie.report,2024:report"),
            )
        )

        iterator = iter(input)
        header = next(iterator, None)
        if header is None:
            raise EmptyReport()
        metadata = RunMetadata.from_dict(**validator.validated(header))

        results: HashTrieMap[  # type: ignore[reportUnknownVariableType] # pyright cannot infer the type returned by HashTrieMap.fromkeys
            ConnectableId,
            HashTrieMap[Seq, SeqResult],
        ] = HashTrieMap.fromkeys(  # type: ignore[reportUnknownMemberType]
            metadata.implementations,
            HashTrieMap(),
        )
        cases: HashTrieMap[Seq, TestCase] = HashTrieMap()

        for data in iterator:
            match validator.validated(data):
                case {"seq": seq, "case": case}:
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
        implementations: Mapping[ConnectableId, ImplementationInfo] = {},
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

    @classmethod
    def combine_versioned_reports_for(
        cls,
        versioned_reports: Iterable[Report],
        dialect: Dialect,
    ) -> Report:
        versioned_reports = [
            versioned_report
            for versioned_report in versioned_reports
            if versioned_report.metadata.dialect == dialect
            and not versioned_report.is_empty
        ]
        if not versioned_reports:
            return cls.empty(dialect=dialect)

        results: HashTrieMap[
            ConnectableId,
            HashTrieMap[Seq, SeqResult],
        ] = HashTrieMap()
        implementations: dict[ConnectableId, ImplementationInfo] = {}

        for versioned_report in versioned_reports:
            ((version_id, version_info),) = (
                versioned_report.metadata.implementations.items()
            )
            implementations[version_id] = version_info
            results = results.insert(
                version_id,
                versioned_report._results[version_id],
            )

        return cls(
            cases=versioned_reports[0]._cases,
            results=results,
            metadata=RunMetadata(
                implementations=implementations,
                dialect=dialect,
            ),
            did_fail_fast=False,
        )

    @property
    def implementations(self) -> Mapping[ConnectableId, ImplementationInfo]:
        return self.metadata.implementations

    @property
    def is_empty(self):
        return not self._cases

    @property
    def total_tests(self):
        return sum(len(case.tests) for case in self._cases.values())

    def compliance_by_implementation(self):
        """
        Return the fraction of passing tests for each reported implementation.
        """
        return {
            id: 1 - (unsuccessful.total / self.total_tests)
            for id, _, unsuccessful in self.worst_to_best()
        }

    def unsuccessful(self, implementation: ConnectableId) -> Unsuccessful:
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
            (id, implementation, self.unsuccessful(id))
            for id, implementation in self.implementations.items()
        ]
        unsuccessful.sort(key=lambda each: (each[2].total, each[1].name))
        return unsuccessful

    def latest_to_oldest(self):
        """
        Versioned implementations sorted by their latest to oldest versions.
        """
        unsuccessful = [
            (implementation.version, self.unsuccessful(id))
            for id, implementation in self.implementations.items()
            if implementation.version is not None
        ]
        unsuccessful.sort(
            key=lambda version_compliance: (
                sortable_version_key(version_compliance[0])
            ),
            reverse=True,
        )
        return unsuccessful

    def cases_with_results(
        self,
    ) -> Iterable[
        tuple[
            TestCase,
            Iterable[tuple[Example | Test, Mapping[str, AnyTestResult]]],
        ]
    ]:
        for seq, case in sorted(self._cases.items()):
            test_results: list[
                tuple[Example | Test, Mapping[str, AnyTestResult]]
            ] = []
            for i, test in enumerate(case.tests):
                test_result = {
                    id: self._results[id][seq].result_for(i)
                    for id in self.implementations
                }
                test_results.append((test, test_result))
            yield case, test_results

    def compliance_badges(self) -> Iterable[tuple[ImplementationInfo, Badge]]:
        for id, implementation in self.implementations.items():
            unsuccessful = self.unsuccessful(id)
            passed = self.total_tests - unsuccessful.total
            percentage = int(100 * (passed / self.total_tests))
            r, g, b = 100 - percentage, percentage, 0
            yield implementation, Badge(
                schemaVersion=1,
                label=self.metadata.dialect.pretty_name,
                message=f"{percentage}% Passing",
                color=f"{r:02x}{g:02x}{b:02x}",
            )


class Badge(TypedDict):
    schemaVersion: Literal[1]
    label: str
    message: str
    color: str


def supported_version_badge(dialects: Iterable[Dialect]) -> Badge:
    message = ", ".join(
        each.pretty_name.removeprefix("Draft ")
        for each in sorted(dialects, reverse=True)
    )
    return Badge(
        schemaVersion=1,
        label="JSON Schema Versions",
        message=message,
        color="lightgreen",
    )
