from datetime import date

import pytest

from bowtie._core import Dialect


def test_known_latest():
    assert Dialect.latest() in Dialect.known()


def test_latest():
    assert Dialect.latest().pretty_name == "Draft 2020-12"


def test_top():
    validator = Dialect.latest().top()
    assert validator.is_valid(37)


def test_bottom():
    validator = Dialect.latest().bottom()
    assert not validator.is_valid(37)


def test_top_draft3():
    validator = Dialect.by_short_name()["draft3"].top()
    assert validator.is_valid(37)


def test_bottom_draft3():
    validator = Dialect.by_short_name()["draft3"].bottom()
    assert not validator.is_valid(37)


def test_no_top():
    no_top = Dialect(
        pretty_name="No top!",
        short_name="NoTop",
        uri="urn:example:no-top",
        first_publication_date=date.today(),
        top_schema=None,
    )
    with pytest.raises(ValueError, match="has no top"):
        no_top.top()


def test_no_bottom():
    no_bottom = Dialect(
        pretty_name="No bottom!",
        short_name="NoBottom",
        uri="urn:example:no-bottom",
        first_publication_date=date.today(),
        bottom_schema=None,
    )
    with pytest.raises(ValueError, match="has no bottom"):
        no_bottom.bottom()
