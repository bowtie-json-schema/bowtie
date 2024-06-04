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


class TestImplicit:
    def test_with_repository(self):
        id = "example.com/bar"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar"),
        )

    def test_no_repository(self):
        id = "bar"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )

    def test_with_repository_and_tag(self):
        id = "example.com/bar:latest"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar:latest"),
        )

    def test_known_direct(self):
        name = "python-jsonschema"
        direct = f"direct:{name}"
        validator.validate(name)
        validator.validate(direct)
        assert Connectable.from_str(name) == Connectable.from_str(direct)

    def test_unknown_direct(self):
        name = "asdf"
        image = f"image:{name}"
        validator.validate(name)
        validator.validate(image)
        assert Connectable.from_str(name) == Connectable.from_str(image)


class TestImage:
    def test_with_repository(self):
        id = "image:foo/bar"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar"),
        )

    def test_with_repository_and_tag(self):
        id = "image:foo/bar:latest"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar:latest"),
        )

    def test_no_repository(self):
        id = "image:bar"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )


class TestContainer:
    def test_uuid(self):
        id = "container:c7895a98f49d"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableContainer(id="c7895a98f49d"),
        )


class TestDirect:
    def test_named_python_jsonschema(self):
        id = "direct:python-jsonschema"
        validator.validate(id)
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct.from_id(id="python-jsonschema"),
        )

    def test_named_unknown(self):
        id = "direct:foobar"
        validator.validate(id)
        # TODO: Probably this should be NoSuchImplementation
        with pytest.raises(NoDirectConnection, match="'foobar'"):
            Connectable.from_str(id)

    def test_import(self):
        id = "direct:bowtie._direct_connectable:jsonschema"
        validator.validate(id)

        from bowtie._direct_connectable import jsonschema

        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct(connect=jsonschema),
        )


class TestExplicitHappy:
    def test_explicit_known_direct(self):
        name = "python-jsonschema"
        happy, direct = f"happy:{name}", f"direct:{name}"
        validator.validate(happy)
        validator.validate(direct)
        assert Connectable.from_str(happy) == Connectable.from_str(direct)

    def test_explicit_unknown_direct(self):
        name = "asdf"
        happy, image = f"happy:{name}", f"image:{name}"
        validator.validate(happy)
        validator.validate(image)
        assert Connectable.from_str(happy) == Connectable.from_str(image)


def test_unknown_connector():
    id = "asdf:foo"
    validator.invalidate(id)
    with pytest.raises(UnknownConnector):
        Connectable.from_str(id)


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
