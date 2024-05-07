from jsonschema.exceptions import ValidationError
from referencing.jsonschema import DRAFT202012, EMPTY_REGISTRY
import pytest

from bowtie._registry import ValidatorRegistry

REGISTRY = [
    DRAFT202012.create_resource({"$id": "urn:everything-valid"}),
    DRAFT202012.create_resource({"$id": "urn:nothing-valid", "not": True}),
] @ EMPTY_REGISTRY
VALIDATORS = ValidatorRegistry.jsonschema(registry=REGISTRY)


def test_validate_valid():
    VALIDATORS.for_uri("urn:everything-valid").validate(37)


def test_validate_invalid():
    validator = VALIDATORS.for_uri("urn:nothing-valid")

    with pytest.raises(ValidationError):
        validator.validate(37)
