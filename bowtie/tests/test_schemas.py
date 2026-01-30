"""
Test Bowtie's schemas for proper functionality.
"""

import pytest

from bowtie._direct_connectable import Direct

TEST = {
    "description": "a test",
    "instance": 37,
}
ANOTHER_TEST = {
    "description": "another test",
    "instance": "foo",
}


@pytest.mark.parametrize(
    "valid, instance",
    [
        (
            True,
            {
                "description": "test group with schema",
                "schema": {},
                "children": [TEST],
            },
        ),
        (
            True,
            {
                "description": "test group with schema and registry",
                "schema": {},
                "registry": {"urn:example": {}},
                "children": [TEST],
            },
        ),
        (
            True,
            {
                "description": "outer test group",
                "children": [
                    {
                        "description": "inner test group",
                        "schema": {},
                        "children": [TEST],
                    },
                ],
            },
        ),
        (
            True,
            {
                "description": "level 3",
                "children": [
                    {
                        "description": "level 2",
                        "children": [
                            {
                                "description": "level 1",
                                "schema": {},
                                "children": [TEST],
                            },
                        ],
                    },
                ],
            },
        ),
        (
            False,
            {
                "description": "test group missing schema everywhere",
                "children": [
                    {
                        "description": "a test",
                        "instance": 37,
                    },
                ],
            },
        ),
        (
            False,
            {
                "description": "duplicated schema",
                "schema": {},
                "children": [
                    {
                        "description": "inner test group",
                        "schema": {},
                        "children": [TEST],
                    },
                ],
            },
        ),
        (
            False,
            {
                "description": "duplicated registry",
                "schema": {},
                "registry": {},
                "children": [
                    {
                        "description": "inner test group",
                        "registry": {"urn:example": {}},
                        "children": [TEST],
                    },
                ],
            },
        ),
        (
            False,
            {
                "description": "nonhomogeneous test group",
                "children": [
                    TEST,
                    {
                        "description": "test group, not test",
                        "children": [ANOTHER_TEST],
                    },
                ],
            },
        ),
        (
            False,
            {
                "description": "test group with invalid registry",
                "schema": {},
                "registry": 37,
                "children": [TEST],
            },
        ),
        (
            False,
            {
                "description": "test group with empty children",
                "schema": {},
                "children": [],
            },
        ),
    ],
)
def test_group(valid, instance):
    registry = Direct.from_id("python-jsonschema").registry()
    validator = registry.for_uri("tag:bowtie.report,2023:models:group")
    assert validator.is_valid(instance) == valid, validator.validate(instance)


def test_root_schema():
    registry = Direct.from_id("python-jsonschema").registry()
    canonical_url = "tag:bowtie.report,2023:ihop"
    schema = registry.schema(canonical_url)
    assert schema["$id"] == canonical_url


@pytest.mark.parametrize(
    "valid, instance",
    [
        (
            True,
            {
                "name": "TestImpl",
                "language": "python",
                "dialects": ["https://json-schema.org/draft/2020-12/schema"],
                "homepage": "https://example.com",
                "issues": "https://example.com/issues",
                "source": "https://example.com/source",
                "version": "1.0.0",
            },
        ),
        (
            True,
            {
                "name": "TestImpl",
                "language": "python",
                "dialects": ["https://json-schema.org/draft/2020-12/schema"],
                "homepage": "https://example.com",
                "issues": "https://example.com/issues",
                "source": "https://example.com/source",
                "version": "remaster-edition",  # master is part of another word
            },
        ),
        (
            False,
            {
                "name": "TestImpl",
                "language": "python",
                "dialects": ["https://json-schema.org/draft/2020-12/schema"],
                "homepage": "https://example.com",
                "issues": "https://example.com/issues",
                "source": "https://example.com/source",
                "version": "master",
            },
        ),
        (
            False,
            {
                "name": "TestImpl",
                "language": "python",
                "dialects": ["https://json-schema.org/draft/2020-12/schema"],
                "homepage": "https://example.com",
                "issues": "https://example.com/issues",
                "source": "https://example.com/source",
                "version": "trunk-latest",
            },
        ),
    ],
)
def test_implementation_version_disallows_branch_names(valid, instance):
    registry = Direct.from_id("python-jsonschema").registry()
    validator = registry.for_uri(
        "tag:bowtie.report,2024:models:implementation"
    )
    assert validator.is_valid(instance) == valid, validator.validate(instance)
