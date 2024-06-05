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
        id = validator.validated("example.com/bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar"),
        )

    def test_no_repository(self):
        id = validator.validated("bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )

    def test_with_repository_and_tag(self):
        id = validator.validated("example.com/bar:latest")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar:latest"),
        )

    def test_known_direct(self):
        name = validator.validated("python-jsonschema")
        direct = validator.validated(f"direct:{name}")
        assert Connectable.from_str(name) == Connectable.from_str(direct)

    def test_unknown_direct(self):
        name = validator.validated("asdf")
        image = validator.validated(f"image:{name}")
        assert Connectable.from_str(name) == Connectable.from_str(image)


class TestImage:
    def test_with_repository(self):
        id = validator.validated("image:foo/bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar"),
        )

    def test_with_repository_and_tag(self):
        id = validator.validated("image:foo/bar:latest")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar:latest"),
        )

    def test_no_repository(self):
        id = validator.validated("image:bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )


class TestContainer:
    def test_uuid(self):
        id = validator.validated("container:c7895a98f49d")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableContainer(id="c7895a98f49d"),
        )


class TestDirect:
    def test_named_python_jsonschema(self):
        id = validator.validated("direct:python-jsonschema")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct.from_id(id="python-jsonschema"),
        )

    def test_named_unknown(self):
        id = validator.validated("direct:foobar")
        # TODO: Probably this should be NoSuchImplementation
        with pytest.raises(NoDirectConnection, match="'foobar'"):
            Connectable.from_str(id)

    def test_import(self):
        id = validator.validated(
            "direct:bowtie._direct_connectable:jsonschema",
        )

        from bowtie._direct_connectable import jsonschema

        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct(connect=jsonschema),
        )


class TestExplicitHappy:
    def test_explicit_known_direct(self):
        name = "python-jsonschema"
        happy = validator.validated(f"happy:{name}")
        direct = validator.validated(f"direct:{name}")
        assert Connectable.from_str(happy) == Connectable.from_str(direct)

    def test_explicit_unknown_direct(self):
        name = "asdf"
        happy = validator.validated(f"happy:{name}")
        image = validator.validated(f"image:{name}")
        assert Connectable.from_str(happy) == Connectable.from_str(image)


def test_unknown_connector():
    id = validator.invalidated("asdf:foo")
    with pytest.raises(UnknownConnector):
        Connectable.from_str(id)


class TestToTerse:
    def test_explicit_image_with_repository(self):
        id = validator.validated("image:foo/bar")
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_explicit_image_bowtie_repository(self):
        id = validator.validated("image:ghcr.io/bowtie-json-schema/bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_explicit_image_no_repository(self):
        id = validator.validated("image:bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_with_repository(self):
        id = validator.validated("foo/bar")
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_implicit_image_bowtie_repository(self):
        id = validator.validated("ghcr.io/bowtie-json-schema/bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_no_repository(self):
        id = validator.validated("bar")
        assert Connectable.from_str(id).to_terse() == "bar"
