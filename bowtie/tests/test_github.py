"""
Tests for extracting information out of GitHub URLs.
"""

from datetime import UTC, datetime, timedelta

import pytest

from bowtie._suite import hour_start, path_and_ref_from_gh_path


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
        (
            "tree/main/annotations/tests/",
            ("annotations/tests", "main"),
        ),
        (
            "tree/main/annotations/tests/format.json",
            ("annotations/tests/format.json", "main"),
        ),
        (
            "tree/feature/tests/tests/draft2020-12/",
            ("tests/draft2020-12", "feature/tests"),
        ),
    ],
)
def test_path_and_ref(path, expected):
    assert path_and_ref_from_gh_path(path.split("/")) == expected


def test_hour_start():
    now = datetime.now(tz=UTC)
    start = hour_start()

    assert (start.minute, start.second, start.microsecond) == (0, 0, 0)
    assert start.tzinfo == UTC
    # The most recent hour boundary: at or before now, less than an hour ago.
    assert start <= now
    assert now - start < timedelta(hours=1)
