"""
Tests for loading test cases from the official test suite.
"""

import json

import pytest

from bowtie._core import Dialect
from bowtie._suite import ClickParam, _is_compatible, annotation_cases_from

DRAFT7 = Dialect.by_alias()["7"]
DRAFT2019 = Dialect.by_alias()["2019"]
DRAFT2020 = Dialect.by_alias()["2020"]


@pytest.mark.parametrize(
    ("dialect", "compatibility", "compatible"),
    [
        (DRAFT2020, None, True),
        (DRAFT2020, "7", True),
        (DRAFT7, "7", True),
        (DRAFT7, "2019", False),
        (DRAFT2020, "=2020", True),
        (DRAFT2019, "=2020", False),
        (DRAFT7, "<=2019", True),
        (DRAFT2020, "<=2019", False),
        (DRAFT2020, ">=2019", True),
        (DRAFT7, ">=2019", False),
        (DRAFT2019, "7, <=2019", True),
        (DRAFT2020, "7, <=2019", False),
        # Bowtie has no drafts 1 or 2, but they're valid lower bounds.
        (DRAFT2020, "1", True),
        (DRAFT7, "2", True),
        (DRAFT2020, "=1", False),
        (DRAFT2020, "<=2", False),
        # The suite marks tests for drafts which don't yet exist with a
        # placeholder version, which no current dialect reaches.
        (DRAFT2020, "9999", False),
        (DRAFT2020, "=9999", False),
        (DRAFT2020, "<=9999", True),
        # Unknown version tokens are never satisfied.
        (DRAFT2020, "bananas", False),
    ],
)
def test_is_compatible(dialect, compatibility, compatible):
    assert _is_compatible(dialect, compatibility) is compatible


def test_convert_local_path(tmp_path):
    tests = tmp_path / "tests" / "draft7"
    tests.mkdir(parents=True)
    tmp_path.joinpath("remotes").mkdir()
    tests.joinpath("type.json").write_text(
        json.dumps(
            [
                {
                    "description": "string type",
                    "schema": {"type": "string"},
                    "tests": [
                        {
                            "description": "a string",
                            "data": "foo",
                            "valid": True,
                        },
                    ],
                },
            ],
        ),
    )

    cases, dialect, metadata = ClickParam().convert(str(tests), None, None)

    assert dialect == DRAFT7
    assert len(list(cases)) == 1
    assert metadata == {}


def test_annotation_cases_from(tmp_path):
    path = tmp_path / "meta-data.json"
    path.write_text(
        json.dumps(
            {
                "suite": [
                    {
                        "description": "title",
                        "schema": {
                            "title": "Foo",
                            "allOf": [{"title": "Bar"}],
                        },
                        "tests": [
                            {
                                "instance": 37,
                                "assertions": [
                                    {
                                        "location": "",
                                        "keyword": "title",
                                        "expected": {
                                            "#": "Foo",
                                            "#/allOf/0": "Bar",
                                        },
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ),
    )

    (case,) = annotation_cases_from(paths=[path], dialect=DRAFT2020)
    (test,) = case.tests

    assert test.assertions == [
        {
            "instanceLocation": "",
            "keyword": "title",
            "expected": {
                "#/title": "Foo",
                "#/allOf/0/title": "Bar",
            },
        },
    ]


def test_annotation_cases_from_absence_assertion(tmp_path):
    path = tmp_path / "unknown.json"
    path.write_text(
        json.dumps(
            {
                "suite": [
                    {
                        "description": "unknown keywords produce nothing",
                        "schema": {"eierlegendeWollmilchsau": True},
                        "tests": [
                            {
                                "instance": 37,
                                "assertions": [
                                    {
                                        "location": "",
                                        "keyword": "eierlegendeWollmilchsau",
                                        "expected": {},
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ),
    )

    (case,) = annotation_cases_from(paths=[path], dialect=DRAFT2020)
    (test,) = case.tests

    assert test.assertions == [
        {
            "instanceLocation": "",
            "keyword": "eierlegendeWollmilchsau",
            "expected": {},
        },
    ]


def test_annotation_cases_from_external_schemas(tmp_path):
    path = tmp_path / "refs.json"
    path.write_text(
        json.dumps(
            {
                "suite": [
                    {
                        "description": "a case with external schemas",
                        "schema": {"$ref": "urn:example:string"},
                        "externalSchemas": {
                            "urn:example:string": {"title": "External!"},
                        },
                        "tests": [
                            {
                                "instance": 37,
                                "assertions": [
                                    {
                                        "location": "",
                                        "keyword": "title",
                                        "expected": {"#": "External!"},
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
        ),
    )

    (case,) = annotation_cases_from(paths=[path], dialect=DRAFT2020)

    assert case.registry["urn:example:string"].contents == {
        "title": "External!",
    }


def test_annotation_cases_from_incompatible_dialect(tmp_path):
    path = tmp_path / "future.json"
    path.write_text(
        json.dumps(
            {
                "suite": [
                    {
                        "description": "needs a draft which does not exist",
                        "compatibility": "9999",
                        "schema": {},
                        "tests": [
                            {
                                "instance": 37,
                                "assertions": [],
                            },
                        ],
                    },
                ],
            },
        ),
    )

    assert list(annotation_cases_from(paths=[path], dialect=DRAFT2020)) == []
