from hypothesis import given

from bowtie._report import Report
from bowtie.hypothesis import dialects


@given(dialect=dialects)
def test_empty_is_empty(dialect):
    assert Report.empty(dialect=dialect).is_empty
