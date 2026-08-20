"""
Tests for the commands Bowtie exchanges with harnesses.
"""

from bowtie._commands import (
    Annotation,
    AnnotationsTestResult,
    Assertion,
    ExpectedAnnotations,
    ExpectedValidity,
    FlagTestResult,
    expectation_from_serialized,
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

EXPECT_TITLE = ExpectedAnnotations(
    assertions=[
        Assertion(
            instanceLocation="",
            keyword="title",
            expected={"#/title": "A string"},
        ),
    ],
)
EXPECT_NO_TITLE = ExpectedAnnotations(
    assertions=[
        Assertion(instanceLocation="", keyword="title", expected={}),
    ],
)


def test_matches_expected_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert EXPECT_TITLE.matches(result)


def test_matches_ignores_unasserted_annotations():
    result = AnnotationsTestResult(
        valid=True,
        annotations=[TITLE, DESCRIPTION],
    )
    assert EXPECT_TITLE.matches(result)


def test_does_not_match_differing_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    expecting = ExpectedAnnotations(
        assertions=[
            Assertion(
                instanceLocation="",
                keyword="title",
                expected={"#/title": "A different string"},
            ),
        ],
    )
    assert not expecting.matches(result)


def test_does_not_match_extra_location_for_asserted_keyword():
    another = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/allOf/0/title",
        annotation="Another",
    )
    result = AnnotationsTestResult(valid=True, annotations=[TITLE, another])
    assert not EXPECT_TITLE.matches(result)


def test_matches_multiple_locations_for_asserted_keyword():
    another = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/allOf/0/title",
        annotation="Another",
    )
    result = AnnotationsTestResult(valid=True, annotations=[TITLE, another])
    expecting = ExpectedAnnotations(
        assertions=[
            Assertion(
                instanceLocation="",
                keyword="title",
                expected={
                    "#/title": "A string",
                    "#/allOf/0/title": "Another",
                },
            ),
        ],
    )
    assert expecting.matches(result)


def test_matches_repeated_assertions_for_one_keyword():
    """
    Repeated assertions for one pair are their union, as displayed.
    """
    another = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/allOf/0/title",
        annotation="Another",
    )
    result = AnnotationsTestResult(valid=True, annotations=[TITLE, another])
    expecting = ExpectedAnnotations(
        assertions=[
            Assertion(
                instanceLocation="",
                keyword="title",
                expected={"#/title": "A string"},
            ),
            Assertion(
                instanceLocation="",
                keyword="title",
                expected={"#/allOf/0/title": "Another"},
            ),
        ],
    )
    assert expecting.matches(result)


def test_matches_absent_annotation():
    result = AnnotationsTestResult(valid=True, annotations=[DESCRIPTION])
    assert EXPECT_NO_TITLE.matches(result)


def test_does_not_match_absent_annotation_when_produced():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert not EXPECT_NO_TITLE.matches(result)


def test_matches_percent_encoded_locations():
    encoded = Annotation(
        keyword="title",
        instanceLocation="",
        keywordLocation="#/$defs/a%20b/title",
        annotation="A string",
    )
    result = AnnotationsTestResult(valid=True, annotations=[encoded])
    expecting = ExpectedAnnotations(
        assertions=[
            Assertion(
                instanceLocation="",
                keyword="title",
                expected={"#/$defs/a b/title": "A string"},
            ),
        ],
    )
    assert expecting.matches(result)


def test_expected_validity_matches_annotated_results():
    result = AnnotationsTestResult(valid=True, annotations=[TITLE])
    assert ExpectedValidity(valid=True).matches(result)
    assert not ExpectedValidity(valid=False).matches(result)


def test_expected_validity_matches_flag_results():
    assert ExpectedValidity(valid=True).matches(FlagTestResult(valid=True))
    assert not ExpectedValidity(valid=False).matches(
        FlagTestResult(valid=True),
    )


def test_flag_result_does_not_match_annotation_assertions():
    assert not EXPECT_TITLE.matches(FlagTestResult(valid=True))


def test_invalid_result_does_not_match_assertions():
    result = AnnotationsTestResult(valid=False, annotations=[TITLE])
    assert not EXPECT_TITLE.matches(result)


def test_invalid_result_does_not_match_absent_annotation():
    result = AnnotationsTestResult(valid=False, annotations=[])
    assert not EXPECT_NO_TITLE.matches(result)


def test_expectations_from_serialized():
    assert expectation_from_serialized(None) is None
    assert expectation_from_serialized(True) == ExpectedValidity(valid=True)
    assert expectation_from_serialized(False) == ExpectedValidity(valid=False)
    assert (
        expectation_from_serialized(
            [
                {
                    "instanceLocation": "",
                    "keyword": "title",
                    "expected": {"#/title": "A string"},
                },
            ],
        )
        == EXPECT_TITLE
    )


def test_expectations_roundtrip():
    for expectation in [
        ExpectedValidity(valid=True),
        ExpectedValidity(valid=False),
        EXPECT_TITLE,
        EXPECT_NO_TITLE,
    ]:
        serialized = expectation.serializable()
        assert expectation_from_serialized(serialized) == expectation
