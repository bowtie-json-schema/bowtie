"""
Bowtie's Hatchling plugin, used for pregenerating implementation data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os

from github3 import GitHub, login
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class BowtieDataIncluder(BuildHookInterface):
    """
    Include Bowtie implementation data when building a distribution.
    """

    def known_implementations(self):
        """
        Our temporary file location.
        """
        return Path(self.directory) / "known_implementations.json"

    def initialize(
        self,
        version: str,
        build_data: dict[str, Any],
    ) -> None:
        """
        Tell Hatchling to store data we'll need at runtime within the package.

        Known implementations are calculated by listing the ``implementations``
        sibling directory (present at build time, but won't be present at
        install time).
        """
        path = Path(__file__).parent.joinpath("implementations")
        known = [d.name for d in path.iterdir() if not d.name.startswith(".")]

        known = self._known_implementations_from_github(known)

        self.app.display_info(f"{len(known)} known implementation(s)")
        self.app.display_debug(f"Known implementations: {known}")

        target_path = "bowtie/data/known_implementations.json"

        out = self.known_implementations()
        out.write_text(json.dumps(known))
        build_data["force_include"][str(out)] = target_path

    def finalize(
        self,
        version: str,
        build_data: dict[str, Any],
        artifact_path: str,
    ) -> None:
        """
        Clean up any generated temporary files.
        """
        self.known_implementations().unlink()

    def _known_implementations_from_github(
        self,
        known_local: list[str],
    ) -> list[str]:
        """
        Collects available implementation using GitHub repositories API.

        The method uses GitHub repositories API to filter our repositories
        marked with 'bowtie-harness' topic.
        """
        gh_token = os.getenv(
            "BUILD_GITHUB_TOKEN",
            default=os.getenv("GITHUB_TOKEN"),
        )

        if not gh_token:
            self.app.display_warning(
                "neither BUILD_GITHUB_TOKEN nor GITHUB_TOKEN are provided. "
                "You can reach the GitHub rate limit",
            )

        # once all harnesses are moved we should report an error
        # if collected list is empty
        harnesses = self._collect_harnesses(gh_token)

        self.app.display_debug(
            f"Collected {len(harnesses)} harness(es): {harnesses}",
        )

        harnesses_set = set(harnesses)
        local_set = set(known_local)
        if harnesses_set.issubset(local_set):
            known_local.sort()
            return known_local

        # join with local implementation until fully migrated to packages API
        # https://github.com/bowtie-json-schema/bowtie/issues/1849
        # sorting is done just to simplify debugging
        # if some harnesses are missed for some reason
        return sorted(local_set | harnesses_set)

    @staticmethod
    def _collect_harnesses(gh_token) -> list[str]:
        gh = login(token=gh_token) if gh_token else GitHub()
        org = gh.organization("bowtie-json-schema")
        repositories = org.repositories()

        def is_harness(repo) -> bool:
            return "bowtie-harness" in repo.topics().names

        return [repo.name for repo in repositories if is_harness(repo)]
