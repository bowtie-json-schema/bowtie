from bowtie._cli import DRAFT2020
from bowtie._report import Report


def test_empty_is_empty():
    assert Report.empty(dialect=DRAFT2020).is_empty
