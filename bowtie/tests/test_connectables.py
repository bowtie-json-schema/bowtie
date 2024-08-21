import pytest

from bowtie._connectables import Connectable, UnknownConnector
from bowtie._containers import (
    IMAGE_REPOSITORY,
    ConnectableContainer,
    ConnectableImage,
)
from bowtie._direct_connectable import Direct
from bowtie.exceptions import CannotConnect

validators = Direct.from_id("python-jsonschema").registry()
validator = validators.for_uri("tag:bowtie.report,2024:connectables")
validated, invalidated = validator.validated, validator.invalidated


class TestImplicit:
    def test_with_repository(self):
        id = validated("example.com/bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar"),
        )

    def test_no_repository(self):
        id = validated("bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )

    def test_with_repository_and_tag(self):
        id = validated("example.com/bar:latest")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="example.com/bar:latest"),
        )

    def test_known_direct(self):
        name = validated("python-jsonschema")
        direct = validated(f"direct:{name}")
        assert Connectable.from_str(name) == Connectable.from_str(direct)

    def test_unknown_direct(self):
        name = validated("asdf")
        image = validated(f"image:{name}")
        assert Connectable.from_str(name) == Connectable.from_str(image)


class TestImage:
    def test_with_repository(self):
        id = validated("image:foo/bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar"),
        )

    def test_with_repository_and_tag(self):
        id = validated("image:foo/bar:latest")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id="foo/bar:latest"),
        )

    def test_no_repository(self):
        id = validated("image:bar")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
        )

    def test_read_timeout_sec(self):
        id = validated("image:bar:read_timeout_sec=5")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(
                id=f"{IMAGE_REPOSITORY}/bar",
                read_timeout_sec=5,
            ),
        )

    def test_no_timeout(self):
        id = validated("image:bar:read_timeout_sec=0")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableImage(
                id=f"{IMAGE_REPOSITORY}/bar",
                read_timeout_sec=None,
            ),
        )


class TestContainer:
    def test_uuid(self):
        id = validated("container:c7895a98f49d")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableContainer(id="c7895a98f49d"),
        )

    def test_read_timeout_sec(self):
        id = validated("container:c7895a98f49d:read_timeout_sec=5")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableContainer(
                id="c7895a98f49d",
                read_timeout_sec=5,
            ),
        )

    def test_no_timeout(self):
        id = validated("container:c7895a98f49d:read_timeout_sec=0")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=ConnectableContainer(
                id="c7895a98f49d",
                read_timeout_sec=None,
            ),
        )


class TestDirect:
    def test_named_python_jsonschema(self):
        id = validated("direct:python-jsonschema")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct.from_id(id="python-jsonschema"),
        )

    def test_null(self):
        id = validated("direct:null")
        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct.null(),
        )

    def test_null_considers_everything_valid(self):
        assert Direct.null().registry().for_schema(False).is_valid(37)

    def test_named_unknown(self):
        id = validated("direct:foobar")
        with pytest.raises(CannotConnect, match="'foobar'"):
            Connectable.from_str(id)

    def test_import(self):
        id = validated("direct:bowtie._direct_connectable:jsonschema")

        from bowtie._direct_connectable import jsonschema

        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct(wraps=jsonschema()),
        )

    def test_import_parameters(self):
        id = validated(
            "direct:bowtie.tests.miniatures:only_supports,dialect=draft7",
        )

        from bowtie.tests.miniatures import only_supports

        assert Connectable.from_str(id) == Connectable(
            id=id,
            connector=Direct(
                wraps=only_supports(dialect="draft7"),
            ),
        )

    def test_import_missing_parameter(self):
        """
        The basic import syntax is direct:foo.bar:baz, not foo.bar.baz.
        """
        prefix, suffix = "direct:bowtie.tests.miniatures", "always_invalid"

        Connectable.from_str(validated(f"{prefix}:{suffix}"))  # succeeds

        with pytest.raises(CannotConnect, match=":always_invalid'"):
            Connectable.from_str(invalidated(f"{prefix}.{suffix}"))


class TestExplicitHappy:
    def test_known_direct(self):
        name = "python-jsonschema"
        happy = validated(f"happy:{name}")
        direct = validated(f"direct:{name}")
        assert Connectable.from_str(happy) == Connectable.from_str(direct)

    def test_unknown_direct_becomes_image(self):
        name = "asdf"
        happy = validated(f"happy:{name}")
        image = validated(f"image:{name}")
        assert Connectable.from_str(happy) == Connectable.from_str(image)

    def test_image_parameters(self):
        name = "asdf:read_timeout_sec=5"
        happy = validated(f"happy:{name}")
        image = validated(f"image:{name}")
        assert Connectable.from_str(happy) == Connectable.from_str(image)


def test_unknown_connector():
    id = invalidated("asdf:foo")
    with pytest.raises(UnknownConnector):
        Connectable.from_str(id)


class TestToTerse:
    def test_explicit_image_with_repository(self):
        id = validated("image:foo/bar")
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_explicit_image_bowtie_repository(self):
        id = validated("image:ghcr.io/bowtie-json-schema/bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_explicit_image_no_repository(self):
        id = validated("image:bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_with_repository(self):
        id = validated("foo/bar")
        assert Connectable.from_str(id).to_terse() == "foo/bar"

    def test_implicit_image_bowtie_repository(self):
        id = validated("ghcr.io/bowtie-json-schema/bar")
        assert Connectable.from_str(id).to_terse() == "bar"

    def test_implicit_image_no_repository(self):
        id = validated("bar")
        assert Connectable.from_str(id).to_terse() == "bar"
