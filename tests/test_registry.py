from referencing.jsonschema import DRAFT202012, EMPTY_REGISTRY
from url import URL
import pytest

from bowtie._direct_connectable import Direct
from bowtie._registry import Invalid, UnexpectedlyValid

ALL_VALID = URL.parse("urn:example:everything-valid")
ALL_INVALID = URL.parse("urn:example:nothing-valid")

REGISTRY = [
    DRAFT202012.create_resource({"$id": str(ALL_VALID)}),
    DRAFT202012.create_resource({"$id": str(ALL_INVALID), "not": True}),
] @ EMPTY_REGISTRY
VALIDATORS = Direct.from_id("python-jsonschema").registry(registry=REGISTRY)


def test_validated_valid():
    instance = 37
    returned = VALIDATORS.for_uri(ALL_VALID).validated(instance)
    assert returned is instance


def test_validated_invalid():
    validator = VALIDATORS.for_uri(ALL_INVALID)

    with pytest.raises(Invalid):
        validator.validated(37)


def test_invalidated_invalid():
    instance = 37
    returned = VALIDATORS.for_uri(ALL_INVALID).invalidated(instance)
    assert returned is instance


def test_invalidated_valid():
    validator = VALIDATORS.for_uri(ALL_VALID)

    with pytest.raises(UnexpectedlyValid):
        validator.invalidated(37)


def test_is_valid():
    assert VALIDATORS.for_uri(ALL_VALID).is_valid(37)


def test_is_not_valid():
    assert not VALIDATORS.for_uri(ALL_INVALID).is_valid(37)
