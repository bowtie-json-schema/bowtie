"""
Tests for the commands Bowtie exchanges with harnesses.
"""

from bowtie._commands import (
    Annotation,
    AnnotationsTestResult,
    FlagTestResult,
)

TITLE = Annotation(
    keyword="title",
    instanceLocation="",
    keywordLocation="#/title",
    annotation="A string",
)
DESCRIPTION = Annotation(
    keyword="description",
    instanceLocation="",
    keywordLocation="#/description",
    annotation="Words!",
)

ASSERT_TITLE = {
    "instanceLocation": "",
    "keyword": "title",
    "expected": {"#/title": "A string"},
}
ASSERT_NO_TITLE = {
    "instanceLocation": "",
    "keyword": "title",
    "expected": {},
}


def test_matches_expected_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert result.matches([ASSERT_TITLE])


def test_matches_ignores_unasserted_annotations():
    result = AnnotationsTestResult(
        valid=True,
        annotations=[TITLE, DESCRIPTION],
    )
    assert result.matches([ASSERT_TITLE])


def test_does_not_match_differing_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert not result.matches(
        [
            {
                "instanceLocation": "",
                "keyword": "title",
                "expected": {"#/title": "A different string"},
            },
        ],
    )


def test_does_not_match_extra_location_for_asserted_keyword():
    another = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/allOf/0/title",
        annotation="Another",
    )
    result = AnnotationsTestResult(valid=True, annotations=[TITLE, another])
    assert not result.matches([ASSERT_TITLE])


def test_matches_multiple_locations_for_asserted_keyword():
    another = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/allOf/0/title",
        annotation="Another",
    )
    result = AnnotationsTestResult(valid=True, annotations=[TITLE, another])
    assert result.matches(
        [
            {
                "instanceLocation": "",
                "keyword": "title",
                "expected": {
                    "#/title": "A string",
                    "#/allOf/0/title": "Another",
                },
            },
        ],
    )


def test_matches_absent_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[DESCRIPTION])
    assert result.matches([ASSERT_NO_TITLE])


def test_does_not_match_absent_annotation_when_produced():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert not result.matches([ASSERT_NO_TITLE])


def test_matches_percent_encoded_locations():
    encoded = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/$defs/a%20b/title",
        annotation="A string",
    )
    result = AnnotationsTestResult(valid=True, annotations=[encoded])
    assert result.matches(
        [
            {
                "instanceLocation": "",
                "keyword": "title",
                "expected": {"#/$defs/a b/title": "A string"},
            },
        ],
    )


def test_annotations_result_matches_valid():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert result.matches(True)
    assert not result.matches(False)


def test_invalid_result_does_not_match_assertions():
    result = AnnotationsTestResult(valid=False, annotations=[TITLE])
    assert not result.matches([ASSERT_TITLE])


def test_invalid_result_does_not_match_absent_annotation():
    result = AnnotationsTestResult(valid=False, annotations=[])
    assert not result.matches([ASSERT_NO_TITLE])


def test_flag_result_does_not_match_annotation_assertions():
    assert not FlagTestResult(valid=True).matches([ASSERT_TITLE])


def test_flag_result_matches_valid():
    assert FlagTestResult(valid=True).matches(True)
    assert not FlagTestResult(valid=True).matches(False)
