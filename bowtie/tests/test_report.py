from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import sets
import pytest

from bowtie import HOMEPAGE, REPO
from bowtie._commands import (
    CaseErrored,
    CaseResult,
    CaseSkipped,
    SeqCase,
    SeqResult,
    TestResult,
)
from bowtie._core import Dialect, Example, ImplementationInfo, TestCase
from bowtie._report import (
    DuplicateImplementation,
    InconsistentCases,
    InconsistentDialects,
    Report,
    RunMetadata,
)
from bowtie.hypothesis import (
    dialects,
    implementations,
    known_dialects,
    reports,
)

# Make pytest ignore these classes matching Test*
TestCase.__test__ = False
TestResult.__test__ = False


DIALECT_2020, DIALECT_2019 = (
    Dialect.by_alias()["2020"],
    Dialect.by_alias()["2019"],
)
FOO = ImplementationInfo(
    name="foo",
    language="blub",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT_2020]),
)
BAR = ImplementationInfo(
    name="bar",
    language="crust",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT_2020]),
)
BAZ_V1 = ImplementationInfo(
    name="baz",
    language="quux",
    version="1",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT_2020, DIALECT_2019]),
)
BAZ_V2 = ImplementationInfo(
    name="baz",
    language="quux",
    version="2",
    homepage=HOMEPAGE,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset([DIALECT_2020, DIALECT_2019]),
)
FOO_RUN = RunMetadata(dialect=DIALECT_2020, implementations={"foo": FOO})
BAR_RUN = RunMetadata(dialect=DIALECT_2020, implementations={"bar": BAR})
NO_FAIL_FAST = dict(did_fail_fast=False)

CASE1 = TestCase(
    description="case1",
    schema={},
    tests=[Example(description="1", instance=1)],
)
CASE2 = TestCase(
    description="case2",
    schema={"type": "string"},
    tests=[Example(description="2", instance="hello")],
)


def _report_data(
    impl_id,
    impl_info,
    case_results,
    dialect=DIALECT_2020,
    did_fail_fast=False,
    seq_start=1,
):
    """
    Build report data for a single implementation.

    ``case_results`` is a list of ``(case, result)`` pairs.
    """
    metadata = RunMetadata(
        dialect=dialect,
        implementations={impl_id: impl_info},
    )
    data = [metadata.serializable()]
    for i, (case, result) in enumerate(case_results, seq_start):
        data.append(SeqCase(seq=i, case=case).serializable())
        data.append(
            SeqResult(
                seq=i,
                implementation=impl_id,
                expected=[t.expected() for t in case.tests],
                result=result,
            ).serializable(),
        )
    data.append({"did_fail_fast": did_fail_fast})
    return data


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


def test_eq_combine_versioned_reports():
    BAZ_V1_2020_RUN = RunMetadata(
        dialect=DIALECT_2020,
        implementations={"baz_v1": BAZ_V1},
    )
    BAZ_V1_2019_RUN = RunMetadata(
        dialect=DIALECT_2019,
        implementations={"baz_v1": BAZ_V1},
    )
    data_baz_v1_2020 = [
        BAZ_V1_2020_RUN.serializable(),
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
            implementation="baz_v1",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    data_baz_v1_2019 = [
        BAZ_V1_2019_RUN.serializable(),
        SeqCase(
            seq=1,
            case=TestCase(
                description="bar",
                schema={},
                tests=[Example(description="1", instance="bar")],
            ),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="baz_v1",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    BAZ_V2_2020_RUN = RunMetadata(
        dialect=DIALECT_2020,
        implementations={"baz_v2": BAZ_V2},
    )
    data_baz_v2_2020 = [
        BAZ_V2_2020_RUN.serializable(),
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
            implementation="baz_v2",
            expected=[None],
            result=CaseResult(results=[TestResult.INVALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    combined = [
        RunMetadata(
            dialect=DIALECT_2020,
            implementations={
                "baz_v1": BAZ_V1,
                "baz_v2": BAZ_V2,
            },
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
            implementation="baz_v1",
            expected=[None],
            result=CaseResult(results=[TestResult.VALID]),
        ).serializable(),
        SeqResult(
            seq=1,
            implementation="baz_v2",
            expected=[None],
            result=CaseResult(results=[TestResult.INVALID]),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    assert Report.combine_versioned_reports_for(
        [
            Report.from_input(data_baz_v1_2020),
            Report.from_input(data_baz_v1_2019),
            Report.from_input(data_baz_v2_2020),
        ],
        dialect=DIALECT_2020,
    ) == Report.from_input(combined)


@given(dialect=known_dialects)
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_ne_different_implementations(dialect):
    foo = RunMetadata(
        dialect=dialect,
        implementations={"foo": FOO},
    )
    foo_and_bar = RunMetadata(
        dialect=dialect,
        implementations={"foo": FOO, "x/baz": BAR},
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


class TestSerialized:
    """Tests for Report.serialized()."""

    def test_round_trip_single_case(self):
        data = _report_data(
            "foo",
            FOO,
            [(CASE1, CaseResult(results=[TestResult.VALID]))],
        )
        report = Report.from_input(data)
        assert Report.from_serialized(report.serialized()) == report

    def test_round_trip_multiple_cases(self):
        data = _report_data(
            "foo",
            FOO,
            [
                (CASE1, CaseResult(results=[TestResult.VALID])),
                (CASE2, CaseResult(results=[TestResult.INVALID])),
            ],
        )
        report = Report.from_input(data)
        assert Report.from_serialized(report.serialized()) == report

    def test_round_trip_multiple_implementations(self):
        combined = Report.combine(
            Report.from_input(
                _report_data(
                    "foo",
                    FOO,
                    [(CASE1, CaseResult(results=[TestResult.VALID]))],
                ),
            ),
            Report.from_input(
                _report_data(
                    "bar",
                    BAR,
                    [(CASE1, CaseResult(results=[TestResult.INVALID]))],
                ),
            ),
        )
        assert Report.from_serialized(combined.serialized()) == combined

    def test_round_trip_errored_case(self):
        data = _report_data(
            "foo",
            FOO,
            [(CASE1, CaseErrored(context={"message": "boom"}, caught=True))],
        )
        report = Report.from_input(data)
        assert Report.from_serialized(report.serialized()) == report

    def test_round_trip_skipped_case(self):
        data = _report_data(
            "foo",
            FOO,
            [(CASE1, CaseSkipped(message="not supported"))],
        )
        report = Report.from_input(data)
        assert Report.from_serialized(report.serialized()) == report

    def test_round_trip_did_fail_fast(self):
        data = _report_data(
            "foo",
            FOO,
            [(CASE1, CaseResult(results=[TestResult.VALID]))],
            did_fail_fast=True,
        )
        report = Report.from_input(data)
        result = Report.from_serialized(report.serialized())
        assert result == report
        assert result.did_fail_fast

    @given(report=reports())
    @settings(suppress_health_check=[HealthCheck.too_slow])
    def test_round_trip_any_report(self, report):
        result = Report.from_serialized(report.serialized())
        assert result == report


class TestCombine:
    """Tests for Report.combine()."""

    def test_combine_two_single_implementation_reports(self):
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, CaseResult(results=[TestResult.INVALID]))],
            ),
        )
        combined = Report.combine(foo_report, bar_report)
        assert set(combined.implementations) == {"foo", "bar"}
        assert combined.total_tests == 1
        assert combined.unsuccessful("foo").total == 0
        assert combined.unsuccessful("bar").total == 0  # no expected result

    def test_combine_different_seqs_same_cases(self):
        """Reports with different seq numbers but identical cases combine."""
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, CaseResult(results=[TestResult.INVALID]))],
                seq_start=99,
            ),
        )
        combined = Report.combine(foo_report, bar_report)
        assert set(combined.implementations) == {"foo", "bar"}
        assert combined.total_tests == 1

    def test_combine_multiple_cases(self):
        valid = CaseResult(results=[TestResult.VALID])
        invalid = CaseResult(results=[TestResult.INVALID])
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, valid), (CASE2, valid)],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, invalid), (CASE2, invalid)],
            ),
        )
        combined = Report.combine(foo_report, bar_report)
        assert set(combined.implementations) == {"foo", "bar"}
        assert combined.total_tests == len(CASE1.tests) + len(CASE2.tests)

    def test_combine_fail_fast_is_ored(self):
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
                did_fail_fast=True,
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        combined = Report.combine(foo_report, bar_report)
        assert combined.did_fail_fast

    def test_combine_errors_on_mismatched_dialects(self):
        bar_2019 = ImplementationInfo(
            name="bar",
            language="crust",
            homepage=HOMEPAGE,
            issues=REPO / "issues",
            source=REPO,
            dialects=frozenset([DIALECT_2019]),
        )
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                bar_2019,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
                dialect=DIALECT_2019,
            ),
        )
        with pytest.raises(InconsistentDialects):
            Report.combine(foo_report, bar_report)

    def test_combine_errors_on_duplicate_implementation(self):
        report1 = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        report2 = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.INVALID]))],
            ),
        )
        with pytest.raises(DuplicateImplementation):
            Report.combine(report1, report2)

    def test_combine_three_reports(self):
        baz = ImplementationInfo(
            name="baz",
            language="quux",
            homepage=HOMEPAGE,
            issues=REPO / "issues",
            source=REPO,
            dialects=frozenset([DIALECT_2020]),
        )
        valid = CaseResult(results=[TestResult.VALID])
        combined = Report.combine(
            Report.from_input(_report_data("foo", FOO, [(CASE1, valid)])),
            Report.from_input(_report_data("bar", BAR, [(CASE1, valid)])),
            Report.from_input(_report_data("baz", baz, [(CASE1, valid)])),
        )
        assert set(combined.implementations) == {"foo", "bar", "baz"}
        assert combined.total_tests == 1

    def test_combine_errors_on_different_cases(self):
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE2, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        with pytest.raises(InconsistentCases):
            Report.combine(foo_report, bar_report)

    def test_combine_errors_on_extra_cases_in_first(self):
        valid = CaseResult(results=[TestResult.VALID])
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, valid), (CASE2, valid)],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, valid)],
            ),
        )
        with pytest.raises(InconsistentCases):
            Report.combine(foo_report, bar_report)

    def test_combine_errors_on_extra_cases_in_rest(self):
        valid = CaseResult(results=[TestResult.VALID])
        foo_report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, valid)],
            ),
        )
        bar_report = Report.from_input(
            _report_data(
                "bar",
                BAR,
                [(CASE1, valid), (CASE2, valid)],
            ),
        )
        with pytest.raises(InconsistentCases):
            Report.combine(foo_report, bar_report)

    def test_combine_single_report_is_identity(self):
        report = Report.from_input(
            _report_data(
                "foo",
                FOO,
                [(CASE1, CaseResult(results=[TestResult.VALID]))],
            ),
        )
        assert Report.combine(report) == report

    def test_combine_then_serialize_round_trips(self):
        combined = Report.combine(
            Report.from_input(
                _report_data(
                    "foo",
                    FOO,
                    [(CASE1, CaseResult(results=[TestResult.VALID]))],
                ),
            ),
            Report.from_input(
                _report_data(
                    "bar",
                    BAR,
                    [(CASE1, CaseResult(results=[TestResult.INVALID]))],
                ),
            ),
        )
        assert Report.from_serialized(combined.serialized()) == combined


class TestSplitOnCases:
    """Tests for Report.split_on_cases()."""

    def test_all_agree(self):
        valid = CaseResult(results=[TestResult.VALID])
        foo = Report.from_input(_report_data("foo", FOO, [(CASE1, valid)]))
        bar = Report.from_input(_report_data("bar", BAR, [(CASE1, valid)]))
        kept, rest = Report.split_on_cases([foo, bar])
        assert (kept, rest) == ([foo, bar], [])

    def test_the_odd_one_out_is_left_out(self):
        baz_info = ImplementationInfo(
            name="baz",
            language="quux",
            homepage=HOMEPAGE,
            issues=REPO / "issues",
            source=REPO,
            dialects=frozenset([DIALECT_2020]),
        )
        valid = CaseResult(results=[TestResult.VALID])
        foo = Report.from_input(_report_data("foo", FOO, [(CASE1, valid)]))
        stale = Report.from_input(_report_data("bar", BAR, [(CASE2, valid)]))
        baz = Report.from_input(
            _report_data("baz", baz_info, [(CASE1, valid)]),
        )
        kept, rest = Report.split_on_cases([foo, stale, baz])
        assert (kept, rest) == ([foo, baz], [stale])
        assert set(Report.combine(*kept).implementations) == {"foo", "baz"}

    def test_a_tie_goes_to_the_newer_report(self):
        valid = CaseResult(results=[TestResult.VALID])
        older = _report_data("foo", FOO, [(CASE1, valid)])
        older[0]["started"] = "2026-01-01T00:00:00+00:00"
        newer = _report_data("bar", BAR, [(CASE2, valid)])
        newer[0]["started"] = "2026-02-01T00:00:00+00:00"
        foo, bar = Report.from_input(older), Report.from_input(newer)
        assert Report.split_on_cases([foo, bar]) == ([bar], [foo])
        assert Report.split_on_cases([bar, foo]) == ([bar], [foo])
