from datetime import datetime, timedelta, timezone

from diff import diff
from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import data, just, sets
import pytest

from bowtie import HOMEPAGE, REPO
from bowtie._commands import CaseResult, SeqCase, SeqResult, TestResult
from bowtie._core import Dialect, Example, ImplementationInfo, Test, TestCase
from bowtie._report import Diff, IncompatibleDiff, Report, RunMetadata
from bowtie.hypothesis import (
    cases_and_results,
    dialects,
    implementations,
    known_dialects,
    report_diffs,
    reports,
    seqs,
    test_cases,
)

for crazy_pytest in [Test, TestCase, test_cases]:  # :/ :/ :/ ...
    crazy_pytest.__test__ = False


DIALECT = Dialect.by_alias()["2020"]
FOO = ImplementationInfo(
    name="foo",
    language="blub",
    image="foo",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT]),
)
BAR = ImplementationInfo(
    name="bar",
    language="crust",
    image="x/baz",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT]),
)
FOO_RUN = RunMetadata(dialect=DIALECT, implementations=[FOO])
NO_FAIL_FAST = dict(did_fail_fast=False)


def test_eq():
    data = (
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    )
    assert Report.from_input(data) == Report.from_input(data)


def test_eq_different_seqs():
    data = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    reseqed = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=200,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(reseqed)


def test_eq_different_order():
    data = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    reordered = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(reordered)


@pytest.mark.xfail(reason="We should use some other structure for results.")
def test_eq_different_seqs_different_order():
    data = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    different_seqs = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=200,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        SeqCase(
            seq=100,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=100,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(different_seqs)


def test_ne_different_results():
    data = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    different_result = [
        FOO_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.INVALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    assert Report.from_input(data) != Report.from_input(different_result)


@given(dialect=known_dialects)
def test_ne_different_implementations(dialect):
    foo = RunMetadata(
        dialect=dialect,
        implementations=[FOO],
    )
    foo_and_bar = RunMetadata(
        dialect=dialect,
        implementations=[FOO, BAR],
    )
    data = [
        SeqCase(
            seq=1,
            case=TestCase(
                description="foo",
                schema={},
                tests=[Example(description="1", instance=1)],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="foo",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqCase(
            seq=2,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    foo_report = Report.from_input([foo.serializable(), *data])
    assert Report.from_input([foo_and_bar.serializable(), *data]) != foo_report


@given(dialect=dialects())
def test_eq_different_bowtie_version(dialect):
    one = Report.empty(dialect=dialect, bowtie_version="1970-1-1")
    two = Report.empty(dialect=dialect, bowtie_version="2000-12-31")
    assert one == two


@given(dialects=sets(dialects(), min_size=2, max_size=2))
def test_ne_different_dialect(dialects):
    one, two = dialects
    assert Report.empty(dialect=one) != Report.empty(dialect=two)


@given(dialect=dialects())
def test_eq_empty(dialect):
    assert Report.empty(dialect=dialect) == Report.empty(dialect=dialect)


@given(dialect=dialects())
def test_empty_is_empty(dialect):
    report = Report.empty(dialect=dialect)
    assert report.is_empty


@given(dialect=dialects(), implementations=implementations(min_size=0))
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_empty_with_implementations_is_empty(dialect, implementations):
    report = Report.empty(dialect=dialect, implementations=implementations)
    assert report.is_empty


class TestDiff:
    @given(data())
    def test_extra_test_case(self, data):
        """
        Diffing against a report containing a strict subset of test cases
        produces a diff with just the missing test cases.
        """
        impls = data.draw(implementations())

        in_common = data.draw(cases_and_results(implementations=just(impls)))

        used = dict(seq=set(), case=set())
        for seq_case in in_common[0]:
            used["seq"].add(seq_case.seq)
            used["case"].add(seq_case.case.uniq())

        extra = data.draw(
            cases_and_results(
                implementations=just(impls),
                seqs=seqs.filter(lambda x: x not in used["seq"]),
                test_cases=test_cases().filter(
                    lambda x: x.uniq() not in used["case"],
                ),
            ),
        )

        combined = tuple(x + y for x, y in zip(in_common, extra))

        old = data.draw(
            reports(
                implementations=just(impls),
                cases_and_results=just(in_common),
            ),
        )
        new = data.draw(
            reports(
                dialects=just(old.metadata.dialect),
                implementations=just(impls),
                cases_and_results=just(combined),
            ),
        )

        expected = data.draw(
            reports(
                dialects=just(old.metadata.dialect),
                implementations=just(impls),
                cases_and_results=just(extra),
                fail_fast=just(old.did_fail_fast),
            ),
        )
        assert diff(new, old) == Diff(report=expected)

    @given(data())
    def test_missing_test_cases(self, data):
        """
        Diffing against a report containing a strict superset of test cases
        produces a diff with just the extra test cases.
        """
        impls = data.draw(implementations())

        in_common = data.draw(cases_and_results(implementations=just(impls)))
        used = {sc.seq for sc in in_common[0]}

        missing = data.draw(
            cases_and_results(
                implementations=just(impls),
                seqs=seqs.filter(lambda x: x not in used),
            ),
        )

        combined = tuple(x + y for x, y in zip(in_common, missing))

        old = data.draw(
            reports(
                implementations=just(impls),
                cases_and_results=just(combined),
            ),
        )
        new = data.draw(
            reports(
                dialects=just(old.metadata.dialect),
                implementations=just(impls),
                cases_and_results=just(in_common),
            ),
        )

        expected = data.draw(
            reports(
                dialects=just(old.metadata.dialect),
                implementations=just(impls),
                cases_and_results=just(missing),
                fail_fast=just(old.did_fail_fast),
            ),
        )
        assert diff(new, old) == Diff(report=expected)

    def test_extra_test_cases_missing_results(self):
        pass

    def test_missing_test_cases_missing_results(self):
        pass

    def test_same_test_cases_different_descriptions(self):
        """
        Diffing two reports containing equivalent results but where the test
        cases have differing descriptions produces an empty diff.
        """

    def test_same_test_cases_extra_tests(self):
        pass

    def test_same_test_cases_missing_tests(self):
        pass

    def test_same_test_cases_different_tests(self):
        """
        Diffing two reports containing test cases with different tests produces
        a diff containing all cases.
        """

    def test_same_tests_different_results(self):
        """
        Diffing two reports containing the same cases and tests but different
        results from implementations produces a diff containing the differing
        test results.
        """

    def test_same_test_different_descriptions(self):
        """
        Diffing two reports containing equivalent results but where the
        individual tests have differing descriptions produces an empty diff.
        """

    def test_duplicated_test_cases(self):
        """
        Diffing a report containing multiple "equivalent" test cases does...
        something. TBD.
        """

    def test_extra_implementations(self):
        """
        Diffing against a report with equivalent test cases but which ran
        against a strict subset of implementations produces a diff
        containing the extra implementations.
        """

    def test_missing_implementations(self):
        """
        Diffing against a report with equivalent test cases but which ran
        against a strict superset of implementations produces a diff
        containing the missing implementations.
        """

    def test_differing_implementation_metadata(self):
        """
        Diffing against a report with equivalent implementations but differing
        metadata does... something. Probably ignores the difference.
        """

    def test_diff_across_two_implementations(self):
        """
        Diffing can be done on two implementations (i.e. simply by results).
        """

    def test_diff_across_two_dialects(self):
        """
        Diffing can be done on one implementation across two dialects (i.e. by
        forgetting about the dialect and simply comparing equivalent schemas).

        Probably this should support some form of $schema keyword
        transformation.
        """

    @given(data())
    def test_same_tests_different_seqs(self, data):
        """
        Diffing the same test cases but where the reports used different seqs
        (identifiers) ignores the seq differences and simply compares the cases
        and results.
        """
        impls = data.draw(implementations())

        seq_cases, results = data.draw(
            cases_and_results(implementations=just(impls)),
        )
        used = {sc.seq for sc in seq_cases}

        new_seqs = data.draw(
            sets(
                seqs.filter(lambda x: x not in used),
                min_size=len(seq_cases),
                max_size=len(seq_cases),
            ),
        )
        reseqed = [
            SeqCase(seq=new, case=seq_case.case)
            for new, seq_case in zip(new_seqs, seq_cases)
        ]

        old = data.draw(
            reports(
                implementations=just(impls),
                cases_and_results=just((seq_cases, results)),
            ),
        )
        new = data.draw(
            reports(
                dialects=just(old.metadata.dialect),
                implementations=just(impls),
                cases_and_results=just((reseqed, results)),
            ),
        )

        assert diff(new, old) is None

    def test_both_failed_fast(self):
        """
        Diffing two reports which failed fast produces a diff of the results.
        """

    def test_one_failed_fast(self):
        """
        Diffing two reports only one of which failed fast produces an error.
        """

    @given(reports())
    def test_diff_against_empty_always_equals_report(self, report):
        """
        Any report diffed against the empty report is itself.
        """
        empty = Report.empty(
            implementations=report.metadata.implementations,
            dialect=report.metadata.dialect,
        )
        assert diff(report, empty).report == report

    @given(dialect=dialects())
    def test_irrelevant_version_and_start_time(self, dialect):
        """
        Report metadata is ignored when diffing.
        """
        now = datetime.now(timezone.utc)
        before = now - timedelta(hours=1)

        old = Report.empty(
            bowtie_version="v2000.1.1",
            started=before,
            dialect=dialect,
        )
        new = Report.empty(
            bowtie_version="v2023.12.31",
            started=now,
            dialect=dialect,
        )
        assert diff(new, old) is None

    @given(dialects=sets(dialects(), min_size=2, max_size=2))
    def test_incompatible(self, dialects):
        """
        Comparing reports across dialects (unless specifically intended)
        produces an error.
        """
        one, two = dialects
        report_one = Report.empty(dialect=one)
        report_two = Report.empty(dialect=two)

        with pytest.raises(IncompatibleDiff):
            diff(report_one, report_two)

    @given(reports())
    def test_identical(self, report):
        """
        Diffing any report against itself produces no diff.
        """
        assert diff(report, report) is None

    @given(report_diffs())
    def test_report_diffs_are_never_empty(self, diff):
        """
        If a report diff is empty it shouldn't have been produced.
        """
        assert not diff.report.is_empty
