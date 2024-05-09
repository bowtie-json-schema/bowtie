import pytest

from bowtie._connectables import Connectable, UnknownConnector
from bowtie._containers import IMAGE_REPOSITORY, ConnectableImage
from bowtie._core import validator_registry

validator = validator_registry().for_uri(
    "tag:bowtie.report,2024:connectables",
)


def test_explicit_image_with_repository():
    id = "image:foo/bar"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar"),
    )


def test_explicit_image_no_repository():
    id = "image:bar"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
    )


def test_implicit_image_with_repository():
    id = "foo/bar"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar"),
    )


def test_implicit_image_no_repository():
    id = "bar"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id=f"{IMAGE_REPOSITORY}/bar"),
    )


def test_explicit_image_with_repository_and_tag():
    id = "image:foo/bar:latest"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar:latest"),
    )


def test_implicit_image_with_repository_and_tag():
    id = "foo/bar:latest"
    validator.validate(id)
    connectable = Connectable.from_str(id)
    assert connectable == Connectable(
        id=id,
        connector=ConnectableImage(id="foo/bar:latest"),
    )


def test_unknown_connector():
    id = "asdf:foo"
    validator.invalidate(id)
    with pytest.raises(UnknownConnector):
        Connectable.from_str(id)


def test_terse_explicit_image_with_repository():
    id = "image:foo/bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "foo/bar"


def test_terse_explicit_image_bowtie_repository():
    id = "image:ghcr.io/bowtie-json-schema/bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "bar"


def test_terse_explicit_image_no_repository():
    id = "image:bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "bar"


def test_terse_implicit_image_with_repository():
    id = "foo/bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "foo/bar"


def test_terse_implicit_image_bowtie_repository():
    id = "ghcr.io/bowtie-json-schema/bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "bar"


def test_terse_implicit_image_no_repository():
    id = "bar"
    validator.validate(id)
    assert Connectable.from_str(id).to_terse() == "bar"
