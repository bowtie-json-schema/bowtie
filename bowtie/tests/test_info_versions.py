from unittest.mock import Mock, patch

import pytest
from github3.exceptions import GitHubError

from bowtie._core import Implementation, ImplementationInfo


@pytest.mark.asyncio
async def test_get_versions_suppresses_github_error():
    """
    Test that get_versions() catches GitHub API errors (like rate limits)
    and returns the local fallback version instead of crashing.
    """
    info = ImplementationInfo.from_dict(
        name="fake-runner",
        language="python",
        homepage="https://example.com",
        issues="https://example.com/issues",
        source="https://example.com/source",
        dialects=["http://json-schema.org/draft-07/schema#"],
        version="1.2.3",
    )

    impl = Implementation(
        id="python-fake-runner",
        info=info,
        harness=Mock(),
        reporter=Mock(),
    )

    with patch("bowtie._core.github") as mock_github_func:
        mock_gh_client = Mock()
        mock_github_func.return_value = mock_gh_client
        mock_gh_client._iter.side_effect = GitHubError(resp=Mock())
        versions = await impl.get_versions()

    assert versions == ["1.2.3"]