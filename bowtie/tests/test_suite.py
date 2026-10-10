"""
Tests for loading test cases from the official test suite.
"""

from io import BytesIO
from types import SimpleNamespace
import json
import zipfile

import pytest

from bowtie import _github, _suite
from bowtie._core import Dialect
from bowtie._suite import (
    ClickParam,
    _is_compatible,
    annotation_cases_from,
    validation_cases_from,
)

DRAFT7 = Dialect.by_alias()["7"]
DRAFT2019 = Dialect.by_alias()["2019"]
DRAFT2020 = Dialect.by_alias()["2020"]
DRAFT4 = Dialect.by_alias()["4"]
DRAFT6 = Dialect.by_alias()["6"]
DRAFT3 = Dialect.by_alias()["3"]
V1 = Dialect.by_short_name()["v1"]

TYPE_CASES = {
    "description": "type validation",
    "tests": [
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
}


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
        # Disjunction-over-ranges behaviour
        (DRAFT4, "<=4,7", True),
        (DRAFT6, "<=4,7", False),
        (DRAFT7, "<=4,7", True),
        (DRAFT2019, "<=4,7", True),
        # Three-segment constraint
        (DRAFT3, "<=3,7,<=2020", True),
        (DRAFT4, "<=3,7,<=2020", False),
        (DRAFT7, "<=3,7,<=2020", True),
        (DRAFT2020, "<=3,7,<=2020", True),
        # The prerelease is tested against features not yet released.
        (V1, "9999", True),
        (V1, "2020", True),
        (V1, "<=2020", False),
        (V1, "=2020", False),
    ],
)
def test_is_compatible(dialect, compatibility, compatible):
    assert _is_compatible(dialect, compatibility) is compatible


def test_convert_local_path_unified_format(tmp_path):
    validation = tmp_path / "validation" / "tests"
    validation.mkdir(parents=True)
    validation.joinpath("type.json").write_text(json.dumps(TYPE_CASES))

    ctx = SimpleNamespace(params={"dialect": DRAFT7})
    cases, dialect, metadata = ClickParam().convert(str(validation), None, ctx)

    assert dialect == DRAFT7
    assert len(list(cases)) == 1
    assert metadata == {}


def _fake_download(monkeypatch):
    """
    Serve a unified-layout suite in place of GitHub, recording requests.
    """
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as zf:
        zf.writestr(
            "suite-abc123/validation/tests/type.json",
            json.dumps(TYPE_CASES),
        )
    requested: list[tuple[str, str, str]] = []

    def download_tree(org, repo, ref):
        requested.append((org, repo, ref))
        buffer.seek(0)
        return buffer, {"commit": "abc123"}

    monkeypatch.setattr(_github, "download_tree", download_tree)
    return requested


def test_convert_shortname_fetches_unified_layout(monkeypatch):
    requested = _fake_download(monkeypatch)

    ctx = SimpleNamespace(params={"dialect": DRAFT2020})
    cases, dialect, metadata = ClickParam().convert("7", None, ctx)

    assert requested == [
        ("json-schema-org", "JSON-Schema-Test-Suite", "unify"),
    ]
    assert dialect == DRAFT7
    assert len(list(cases)) == 1
    assert metadata == {"commit": "abc123"}


def test_convert_url_uses_dialect_option(monkeypatch):
    _fake_download(monkeypatch)

    ctx = SimpleNamespace(params={"dialect": DRAFT6})
    cases, dialect, _ = ClickParam().convert(
        str(_suite.TESTS_DIR_URL),
        None,
        ctx,
    )

    assert dialect == DRAFT6
    assert len(list(cases)) == 1


def test_dialects_in_unified_layout(tmp_path):
    validation = tmp_path / "validation" / "tests"
    validation.mkdir(parents=True)
    validation.joinpath("type.json").write_text(json.dumps(TYPE_CASES))

    assert _suite.dialects_in(tmp_path) == set(Dialect.known())


def test_dialects_in_pre_unified_layout(tmp_path):
    tmp_path.joinpath("tests", "draft7").mkdir(parents=True)
    assert _suite.dialects_in(tmp_path) == set()


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


def test_validation_cases_from_unified_format(tmp_path):
    path = tmp_path / "type.json"
    path.write_text(
        json.dumps(
            {
                "description": "type validation",
                "tests": [
                    {
                        "description": "integer type",
                        "schema": {"type": "integer"},
                        "tests": [
                            {
                                "description": "integer is valid",
                                "data": 1,
                                "valid": True,
                            },
                            {
                                "description": "string is invalid",
                                "data": "1",
                                "valid": False,
                            },
                        ],
                    },
                ],
            },
        ),
    )

    dialect = Dialect.by_short_name()["draft7"]

    cases = list(validation_cases_from([path], dialect))

    assert len(cases) == 1
    assert cases[0].description == "integer type"
    assert cases[0].schema == {"type": "integer"}
    assert [result.valid for result in cases[0].expected_results()] == [
        True,
        False,
    ]
    assert [test.instance for test in cases[0].tests] == [1, "1"]


def test_validation_cases_from_keeps_comments(tmp_path):
    path = tmp_path / "type.json"
    path.write_text(
        json.dumps(
            {
                "description": "type validation",
                "tests": [
                    {
                        "description": "integer type",
                        "comment": "a case comment",
                        "schema": {"type": "integer"},
                        "tests": [
                            {
                                "description": "integer is valid",
                                "comment": "a test comment",
                                "data": 1,
                                "valid": True,
                            },
                        ],
                    },
                ],
            },
        ),
    )

    (case,) = validation_cases_from([path], DRAFT7)
    (test,) = case.tests

    assert (case.comment, test.comment) == ("a case comment", "a test comment")


def test_validation_cases_from_respects_compatibility(tmp_path):
    path = tmp_path / "type.json"
    path.write_text(
        json.dumps(
            {
                "description": "type validation",
                "tests": [
                    {
                        "description": "available from draft 6",
                        "compatibility": "6",
                        "schema": {"type": "integer"},
                        "tests": [
                            {
                                "description": "integer",
                                "data": 1,
                                "valid": True,
                            },
                        ],
                    },
                    {
                        "description": "available from draft 7",
                        "compatibility": "7",
                        "schema": {"type": "string"},
                        "tests": [
                            {
                                "description": "integer string",
                                "data": "hello",
                                "valid": True,
                            },
                        ],
                    },
                ],
            },
        ),
    )

    draft6 = Dialect.by_short_name()["draft6"]
    draft7 = Dialect.by_short_name()["draft7"]

    draft6_cases = list(validation_cases_from([path], draft6))
    draft7_cases = list(validation_cases_from([path], draft7))

    assert [case.description for case in draft6_cases] == [
        "available from draft 6",
    ]
    assert [case.description for case in draft7_cases] == [
        "available from draft 6",
        "available from draft 7",
    ]


def test_cases_for_unified_layout(tmp_path):
    validation = tmp_path / "validation" / "tests"
    validation.mkdir(parents=True)
    validation.joinpath("type.json").write_text(
        json.dumps(
            {
                "description": "type validation",
                "tests": [
                    {
                        "description": "integer type",
                        "schema": {"type": "integer"},
                        "tests": [
                            {
                                "description": "an integer is valid",
                                "data": 1,
                                "valid": True,
                            },
                        ],
                    },
                    {
                        "description": "only for draft7+",
                        "compatibility": "7",
                        "schema": {"type": "string"},
                        "tests": [
                            {
                                "description": "a string is valid",
                                "data": "foo",
                                "valid": True,
                            },
                        ],
                    },
                ],
            },
        ),
    )

    draft6 = Dialect.by_short_name()["draft6"]
    draft7 = Dialect.by_short_name()["draft7"]
    draft6_cases = list(_suite.cases_for(tmp_path, draft6))
    draft7_cases = list(_suite.cases_for(tmp_path, draft7))
    assert [case.description for case in draft6_cases] == ["integer type"]
    assert [case.description for case in draft7_cases] == [
        "integer type",
        "only for draft7+",
    ]


def _format_cases():
    return {
        "description": "email format",
        "tests": [
            {
                "description": "untagged",
                "schema": {"format": "email"},
                "tests": [
                    {"description": "a number", "data": 12, "valid": True},
                ],
            },
            {
                "description": "annotation",
                "tags": ["format-annotation"],
                "schema": {"format": "email"},
                "tests": [
                    {"description": "bad", "data": "2962", "valid": True},
                ],
            },
            {
                "description": "assertion",
                "tags": ["format-assertion"],
                "schema": {"format": "email"},
                "tests": [
                    {"description": "bad", "data": "2962", "valid": False},
                ],
            },
            {
                "description": "unknown behavior",
                "tags": ["format-annotation", "eierlegendeWollmilchsau"],
                "schema": {},
                "tests": [{"description": "any", "data": 1, "valid": True}],
            },
        ],
    }


@pytest.mark.parametrize(
    ("dialect", "expected"),
    [
        (DRAFT7, ["untagged", "annotation"]),
        (DRAFT2020, ["untagged", "annotation"]),
        (V1, ["untagged", "assertion"]),
    ],
)
def test_validation_cases_from_respects_tags(tmp_path, dialect, expected):
    path = tmp_path / "format-email.json"
    path.write_text(json.dumps(_format_cases()))

    cases = validation_cases_from([path], dialect)

    assert [case.description for case in cases] == expected
