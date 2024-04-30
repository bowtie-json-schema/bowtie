from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import sets
import pytest

from bowtie import HOMEPAGE, REPO
from bowtie._commands import CaseResult, SeqCase, SeqResult, TestResult
from bowtie._core import Dialect, Example, ImplementationInfo, TestCase
from bowtie._report import Report, RunMetadata
from bowtie.hypothesis import dialects, implementations, known_dialects

TestCase.__test__ = False  # frigging py.test


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
