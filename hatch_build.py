"""
Bowtie's Hatchling plugin, used for pregenerating implementation data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os

from github3.exceptions import GitHubException
from github3.session import GitHubSession
from github3.structs import GitHubIterator
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

        known = self._known_implementations_from_packages_api(known)

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

    def _known_implementations_from_packages_api(
        self,
        known_local: list[str],
    ) -> list[str]:
        """
        Collects available implementation using GitHub packages API.
        """
        gh_token = os.getenv("GITHUB_TOKEN")

        if not gh_token:
            self.app.display_warning(
                "GITHUB_TOKEN env variable was not provided. "
                "It will be REQUIRED in the future "
                "to collect known implementations",
            )
            return known_local

        try:
            packages = self._collect_packages(gh_token)
        except GitHubException as e:
            self.app.display_error(
                f"fallback to using local implementations: {e}",
            )
            return known_local

        self.app.display_debug(
            f"Collected {len(packages)} package(s): {packages}",
        )

        packages_set = set(packages)
        local_set = set(known_local)
        if not packages_set.issuperset(local_set):
            self.app.display_warning(
                f"local implementations contain additional implementations: "
                f"{local_set.difference(packages_set)}",
            )
            # return local implementation until fully migrated to packages API
            # https://github.com/bowtie-json-schema/bowtie/issues/1849
            return known_local

        return packages

    @staticmethod
    def _collect_packages(gh_token) -> list[str]:
        session = GitHubSession()
        session.token_auth(gh_token)
        packages_iter = GitHubIterator(
            count=-1,
            url="https://api.github.com/orgs/bowtie-json-schema/packages",
            cls=dict,
            session=session,
            params={
                "package_type": "container",
            },
        )
        return [p["name"] for p in packages_iter]
