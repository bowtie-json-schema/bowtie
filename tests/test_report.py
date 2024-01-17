from hypothesis import given
from hypothesis.strategies import sets
import pytest

from bowtie import _commands
from bowtie._report import Report, RunMetadata
from bowtie.hypothesis import dialects

FOO_RUN = RunMetadata(
    dialect="urn:example",
    implementations={"foo": {"image": "foo"}},
)
NO_FAIL_FAST = dict(did_fail_fast=False)


def test_eq():
    data = (
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    )
    assert Report.from_input(data) == Report.from_input(data)


def test_eq_different_seqs():
    data = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    reseqed = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=200,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(reseqed)


def test_eq_different_order():
    data = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    reordered = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(reordered)


@pytest.mark.xfail(reason="We should use some other structure for results.")
def test_eq_different_seqs_different_order():
    data = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    different_seqs = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=200,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        _commands.SeqCase(
            seq=100,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=100,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        NO_FAIL_FAST,
    ]
    assert Report.from_input(data) == Report.from_input(different_seqs)


def test_ne_different_results():
    data = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]
    different_result = [
        FOO_RUN.serializable(),
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": False}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    assert Report.from_input(data) != Report.from_input(different_result)


def test_ne_different_implementations():
    foo = RunMetadata(
        dialect="urn:example",
        implementations={"foo": {"image": "foo"}},
    )
    foo_and_bar = RunMetadata(
        dialect="urn:example",
        implementations={"foo": {"image": "foo"}, "bar": {"image": "bar"}},
    )
    data = [
        _commands.SeqCase(
            seq=1,
            case=_commands.TestCase(
                description="foo",
                schema={},
                tests=[_commands.Test(description="1", instance=1)],
            ),
        ).serializable(),
        _commands.CaseResult(
            seq=1,
            implementation="foo",
            results=[{"valid": True}],
            expected=[None],
        ).serializable(),
        _commands.SeqCase(
            seq=2,
            case=_commands.TestCase(
                description="bar",
                schema={},
                tests=[_commands.Test(description="1", instance="bar")],
            ),
        ).serializable(),
        NO_FAIL_FAST,
    ]

    foo_report = Report.from_input([foo.serializable(), *data])
    assert Report.from_input([foo_and_bar.serializable(), *data]) != foo_report


@given(dialect=dialects)
def test_eq_different_bowtie_version(dialect):
    one = Report.empty(dialect=dialect, bowtie_version="1970-1-1")
    two = Report.empty(dialect=dialect, bowtie_version="2000-12-31")
    assert one == two


@given(dialects=sets(dialects, min_size=2, max_size=2))
def test_ne_different_dialect(dialects):
    one, two = dialects
    assert Report.empty(dialect=one) != Report.empty(dialect=two)


@given(dialect=dialects)
def test_eq_empty(dialect):
    assert Report.empty(dialect=dialect) == Report.empty(dialect=dialect)


@given(dialect=dialects)
def test_empty_is_empty(dialect):
    assert Report.empty(dialect=dialect).is_empty
