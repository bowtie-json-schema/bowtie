from jsonschema.exceptions import ValidationError
from referencing.jsonschema import DRAFT202012, EMPTY_REGISTRY
import pytest

from bowtie._direct_connectable import Direct
from bowtie._registry import UnexpectedlyValid

REGISTRY = [
    DRAFT202012.create_resource({"$id": "urn:everything-valid"}),
    DRAFT202012.create_resource({"$id": "urn:nothing-valid", "not": True}),
] @ EMPTY_REGISTRY
VALIDATORS = Direct.from_id("python-jsonschema").registry(registry=REGISTRY)


def test_validated_valid():
    instance = 37
    returned = VALIDATORS.for_uri("urn:everything-valid").validated(instance)
    assert returned is instance


def test_validated_invalid():
    validator = VALIDATORS.for_uri("urn:nothing-valid")

    with pytest.raises(ValidationError):
        validator.validated(37)


def test_invalidated_invalid():
    instance = 37
    returned = VALIDATORS.for_uri("urn:nothing-valid").invalidated(instance)
    assert returned is instance


def test_invalidated_valid():
    validator = VALIDATORS.for_uri("urn:everything-valid")

    with pytest.raises(UnexpectedlyValid):
        validator.invalidated(37)
