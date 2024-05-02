from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, TypedDict
import importlib.metadata
import json
import sys

from attrs import asdict, field, frozen
from attrs.filters import exclude
from rpds import HashTrieMap
import structlog.stdlib

from bowtie._commands import (
    Seq,
    SeqCase,
    SeqResult,
    StartedDialect,
    Unsuccessful,
)
from bowtie._core import Dialect, TestCase, validator_registry

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping, Sequence
    from typing import Any, Literal, Self, TextIO

    from bowtie._commands import AnyTestResult, ImplementationId
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

    def unacknowledged_dialect(
        self,
        implementation: str,
        dialect: Dialect,
        response: StartedDialect,
    ):
        self._log.warn(
            (
                "Implicit dialect not acknowledged. "
                "Proceeding, but implementation may not have configured "
                "itself to handle schemas without $schema."
            ),
            logger_name=implementation,
            dialect=dialect.pretty_name,
            response=response,
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
    implementations: Sequence[ImplementationInfo] = field(
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
            dialect=Dialect.from_str(dialect),
            implementations=[
                ImplementationInfo.from_dict(image=image, **data)
                for image, data in implementations.items()
            ],
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
        # TODO: Support some interface for enabling/disabling validation.
        validator = validator_registry().for_uri(
            "tag:bowtie.report,2024:report",
        )

        iterator = iter(input)
        header = next(iterator, None)
        if header is None:
            raise EmptyReport()
        validator.validate(header)
        metadata = RunMetadata.from_dict(**header)

        validator = metadata.dialect.current_dialect_resource() @ validator

        results: HashTrieMap[
            ImplementationId,
            HashTrieMap[Seq, SeqResult],
        ] = HashTrieMap.fromkeys(  # type: ignore[reportUnknownMemberType]
            (each.id for each in metadata.implementations),
            HashTrieMap(),
        )
        cases: HashTrieMap[Seq, TestCase] = HashTrieMap()

        for data in iterator:
            validator.validate(data)
            match data:
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
            Iterable[tuple[Example | Test, Mapping[str, AnyTestResult]]],
        ]
    ]:
        for seq, case in sorted(self._cases.items()):
            test_results: list[
                tuple[Example | Test, Mapping[str, AnyTestResult]]
            ] = []
            for i, test in enumerate(case.tests):
                test_result = {
                    each.id: self._results[each.id][seq].result_for(i)
                    for each in self.implementations
                }
                test_results.append((test, test_result))
            yield case, test_results

    def compliance_badges(self) -> Iterable[tuple[ImplementationInfo, Badge]]:
        for implementation in self.implementations:
            unsuccessful = self.unsuccessful(implementation.id)
            passed = self.total_tests - unsuccessful.total
            percentage = 100 * (passed / self.total_tests)
            r, g, b = 100 - int(percentage), int(percentage), 0
            yield implementation, Badge(
                schemaVersion=1,
                label=self.metadata.dialect.pretty_name,
                message="%d%% Passing" % int(percentage),
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
