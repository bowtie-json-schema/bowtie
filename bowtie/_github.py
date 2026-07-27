"""
Bowtie's runtime interactions with the GitHub API.

All of Bowtie's runtime GitHub access -- discovering an implementation's
published versions, fetching the test suite, reading commit metadata -- goes
through here, so that ``github3.py`` (which ships no type stubs, and whose
public API didn't cover listing container versions without a private method)
stays confined to a single module behind a small, typed interface.

The build-time hook (``hatch_build.py``) deliberately talks to GitHub on its
own: it must not import the package it is building.
"""

from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Any
import os

from bowtie import ORG_NAME

if TYPE_CHECKING:
    from datetime import datetime

#: The git tag prefix each harness repository uses to mark a released version.
HARNESS_RELEASE_TAG = "harness-release-"


def _client() -> Any:
    """
    A GitHub client, authenticated from ``$GITHUB_TOKEN`` when one is set.

    Authenticating (even with the automatic token in CI) lifts the API rate
    limit well above the anonymous one, which matters when a single run touches
    many repositories.
    """
    from github3 import (  # type: ignore[reportMissingTypeStubs]  # noqa: PLC0415
        GitHub,
    )

    return GitHub(token=os.environ.get("GITHUB_TOKEN", ""))


def versions_of(name: str, organization: str = ORG_NAME) -> list[str]:
    """
    The published versions of an implementation.

    Read from the ``harness-release-*`` tags of the implementation's harness
    repository (a sibling, in the Bowtie organization, of its published image).

    Best-effort: an empty list is returned when the harness has no such
    repository or tags, or when GitHub can't be reached -- callers then fall
    back to just the current image, so version discovery is never fatal.
    """
    try:
        repository = _client().repository(organization, name)
        if repository is None:
            return []
        tags = list(repository.tags())
    except Exception:  # noqa: BLE001
        return []
    return [
        tag.name.removeprefix(HARNESS_RELEASE_TAG)
        for tag in tags
        if tag.name.startswith(HARNESS_RELEASE_TAG)
    ]


def latest_commit_before(
    owner: str,
    name: str,
    branch: str,
    when: datetime,
) -> str | None:
    """
    The newest commit on ``branch`` of ``owner/name`` at or before ``when``.

    Returns ``None`` when there is no such commit.
    """
    commits = (
        _client()
        .repository(owner, name)
        .commits(
            sha=branch,
            until=when,
            number=1,
        )
    )
    commit = next(iter(commits), None)
    return None if commit is None else commit.sha


def download_tree(
    owner: str,
    name: str,
    ref: str,
) -> tuple[BytesIO, dict[str, Any]] | None:
    """
    Download ``owner/name`` at ``ref`` as a zipball, with run metadata.

    Returns the zipball (seeked to its start) alongside metadata recording the
    exact commit the ref resolved to, or ``None`` if the archive could not be
    fetched.
    """
    repository = _client().repository(owner, name)

    data = BytesIO()
    data.name = ""
    if not repository.archive(format="zipball", path=data, ref=ref):
        return None
    data.seek(0)
    return data, _commit_metadata(repository, ref)


def _commit_metadata(repository: Any, ref: str) -> dict[str, Any]:
    """Run metadata recording the exact commit a suite ``ref`` resolves to."""
    from github3.exceptions import (  # type: ignore[reportMissingTypeStubs]  # noqa: PLC0415
        NotFoundError,
    )

    try:
        commit = repository.commit(ref)
    except NotFoundError:
        info: Any = ref
    else:
        # TODO: Make this the tree URL maybe, but tree(...) doesn't come with
        #       an html_url.
        info = {"text": commit.sha[:7], "href": commit.html_url}
    return {"Commit": info}
