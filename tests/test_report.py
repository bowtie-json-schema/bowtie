from hypothesis import given
from hypothesis.strategies import sets

from bowtie._report import Report
from bowtie.hypothesis import dialects


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
