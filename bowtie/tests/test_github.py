"""
Tests for extracting information out of GitHub URLs.
"""

import pytest

from bowtie._suite import path_and_ref_from_gh_path


@pytest.mark.parametrize(
    "path, expected",
    [
        (
            "tree/main/tests/draft2020-12",
            ("tests/draft2020-12", "main"),
        ),
        (
            "tree/main/tests/draft2020-12/",
            ("tests/draft2020-12", "main"),
        ),
        (
            "blob/main/tests/draft2020-12/contains.json",
            ("tests/draft2020-12/contains.json", "main"),
        ),
        (
            "blob/branch/with/slashes/tests/draft2020-12/contains.json",
            ("tests/draft2020-12/contains.json", "branch/with/slashes"),
        ),
        (
            "blob/CASESENSITIVEBRANCH/tests/draft2020-12/contains.json",
            ("tests/draft2020-12/contains.json", "CASESENSITIVEBRANCH"),
        ),
        # this URL isn't real, in that you get tree/ not blob/,
        # but we can easily support it anyhow in case someone manually
        # edits the URL
        (
            "blob/main/tests/draft2020-12/",
            ("tests/draft2020-12", "main"),
        ),
    ],
)
def test_path_and_ref(path, expected):
    assert path_and_ref_from_gh_path(path.split("/")) == expected
