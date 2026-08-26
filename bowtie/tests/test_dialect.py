from datetime import date
from importlib.resources import files
from pathlib import Path
import json

from referencing.jsonschema import specification_with
from url import URL
import pytest

from bowtie._core import Dialect
from bowtie._direct_connectable import Direct


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


def test_ordering():
    draft7 = Dialect.by_short_name()["draft7"]
    draft2019 = Dialect.by_short_name()["draft2019-09"]

    assert draft7 < draft2019
    assert draft7 <= draft2019
    assert draft2019 > draft7
    assert draft2019 >= draft7
    assert draft7 <= draft7  # noqa: PLR0124
    assert draft7 >= draft7  # noqa: PLR0124
    assert not draft7 < draft7  # noqa: PLR0124


def test_latest_ignores_unpublished_dialects():
    """
    A dialect still being written is known, but it is not the latest one.

    Defaulting to one would send schemas to harnesses which have not said
    they support the dialect.
    """
    unpublished = [each for each in Dialect.known() if not each.is_published]
    assert unpublished, "this test is only meaningful with one of these"
    assert Dialect.latest() not in unpublished


def test_unpublished_dialects_sort_newest():
    v1 = Dialect.by_short_name()["v1"]

    assert max(Dialect.known()) == v1
    assert v1 > Dialect.latest()
    assert Dialect.latest() < v1


def test_unpublished_dialect_has_no_publication_date():
    v1 = Dialect.by_short_name()["v1"]

    assert v1.first_publication_date is None
    assert not v1.is_published


def test_v1():
    v1 = Dialect.by_short_name()["v1"]

    assert v1.uri == URL.parse("https://json-schema.org/v1")
    assert Dialect.from_str("https://json-schema.org/v1") == v1
    for alias in ("draft-next",):
        assert Dialect.by_alias()[alias] == v1


def test_v1_specification():
    """
    `referencing` does not know v1 yet, so Bowtie says what it looks like.

    Without this, loading a single v1 test case raises `UnknownDialect`.
    """
    v1 = Dialect.by_short_name()["v1"]

    assert v1.specification() == specification_with(
        "https://json-schema.org/draft/2020-12/schema",
    )


def test_every_dialect_has_a_specification():
    for each in Dialect.known():
        each.specification()


def test_dialects_json_matches_its_own_schema():
    registry = Direct.from_id("python-jsonschema").registry()
    validator = registry.for_uri("tag:bowtie.report,2024:models:dialect")

    data = files("bowtie") / "data"
    if not data.is_dir():
        data = Path(__file__).parent.parent.parent / "data"

    for each in json.loads(data.joinpath("dialects.json").read_text()):
        # $schema here identifies the model the entry follows, so it is
        # metadata about the entry rather than part of what is described
        validator.validate({k: v for k, v in each.items() if k != "$schema"})


def test_two_unpublished_dialects_still_have_a_total_order():
    """
    Two dialects being written at once must not compare as incomparable.

    `Dialect.known()` is a set, so without a tie-break the sort order would
    also differ between runs.
    """
    one = Dialect(
        pretty_name="One",
        short_name="one",
        uri="urn:example:one",
        first_publication_date=None,
    )
    two = Dialect(
        pretty_name="Two",
        short_name="two",
        uri="urn:example:two",
        first_publication_date=None,
    )

    assert one < two
    assert two > one
    assert sorted([two, one]) == [one, two]
    assert sorted([one, two]) == [one, two]


def test_a_dialect_must_say_whether_it_is_published():
    with pytest.raises(TypeError):
        Dialect(  # type: ignore[reportCallIssue]
            pretty_name="Undated",
            short_name="undated",
            uri="urn:example:undated",
        )
