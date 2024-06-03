import pytest

from bowtie._connectables import Connectable, UnknownConnector
from bowtie._containers import (
    IMAGE_REPOSITORY,
    ConnectableContainer,
    ConnectableImage,
)
from bowtie._core import validator_registry
from bowtie._direct_connectable import Direct, NoDirectConnection

validator = validator_registry().for_uri("tag:bowtie.report,2024:connectables")


def test_explicit_image_with_repository():
    id = "image:foo/bar"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar"),
    )


def test_explicit_image_no_repository():
    id = "image:bar"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
    )


def test_implicit_image_with_repository():
    id = "foo/bar"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar"),
    )


def test_implicit_image_no_repository():
    id = "bar"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
    )


def test_explicit_image_with_repository_and_tag():
    id = "image:foo/bar:latest"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar:latest"),
    )


def test_implicit_image_with_repository_and_tag():
    id = "foo/bar:latest"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar:latest"),
    )


def test_unknown_connector():
    id = "asdf:foo"
    validator.invalidate(id)
    with pytest.raises(UnknownConnector):
        Connectable.from_str(id)


def test_container_connectable():
    id = "container:c7895a98f49d"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=ConnectableContainer(id="c7895a98f49d"),
    )


def test_direct_connectable_python_jsonschema():
    id = "direct:python-jsonschema"
    validator.validate(id)
    assert Connectable.from_str(id) == Connectable(
        id=id,
        connector=Direct(id="python-jsonschema"),
    )


def test_direct_connectable_unknown():
    id = "direct:foobar"
    validator.validate(id)
    with pytest.raises(NoDirectConnection, match="'foobar'"):
        Connectable.from_str(id)


def test_implicit_happy_connectable_known_direct():
    name = "python-jsonschema"
    happy, direct = name, f"direct:{name}"
    validator.validate(name)
    validator.validate(direct)
    assert Connectable.from_str(happy) == Connectable.from_str(direct)


def test_happy_connectable_known_direct():
    name = "python-jsonschema"
    happy, direct = f"happy:{name}", f"direct:{name}"
    validator.validate(happy)
    validator.validate(direct)
    assert Connectable.from_str(happy) == Connectable.from_str(direct)


def test_happy_connectable_unknown_direct():
    name = "asdf"
    happy, image = f"happy:{name}", f"image:{name}"
    validator.validate(happy)
    validator.validate(image)
    assert Connectable.from_str(happy) == Connectable.from_str(image)


class TestToTerse:
    def test_explicit_image_with_repository(self):
        id = "image:foo/bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_explicit_image_bowtie_repository(self):
        id = "image:ghcr.io/bowtie-json-schema/bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_explicit_image_no_repository(self):
        id = "image:bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_with_repository(self):
        id = "foo/bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_implicit_image_bowtie_repository(self):
        id = "ghcr.io/bowtie-json-schema/bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_no_repository(self):
        id = "bar"
        validator.validate(id)
        assert Connectable.from_str(id).to_terse() == "bar"
