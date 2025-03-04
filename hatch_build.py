"""
Bowtie's Hatchling plugin, used for pregenerating implementation data.
"""

from __future__ import annotations

import os
import requests
from pathlib import Path
from typing import Any
import json

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

    @staticmethod
    def _known_implementations_from_packages_api(known_local: list[str]) -> list[str]:
        """
        Collects available implementation using GitHub packages API.
        """
        gh_token_env_var = "GITHUB_TOKEN"
        gh_token = os.getenv(gh_token_env_var)

        if not gh_token:
            print(f"WARN: {gh_token_env_var} env variable was not provided. "
                  f"It will be REQUIRED in the future to collect known implementations")
            return known_local

        try:
            packages = BowtieDataIncluder._collect_packages(gh_token)
        except requests.HTTPError as e:
            print(f"ERROR: fallback to using local implementations: {e.response.text}")
            return known_local

        packages_set = set(packages)
        local_set = set(known_local)
        if not packages_set.issuperset(local_set):
            print(f"WARN: local implementations contain additional implementations: {local_set.difference(packages_set)}")
            # return local implementation until fully migrated to packages API
            # https://github.com/bowtie-json-schema/bowtie/issues/1849
            return known_local

        return packages

    @staticmethod
    def _collect_packages(gh_token):
        packages = []
        page = 1
        while True:
            # https://docs.github.com/en/rest/packages/packages?apiVersion=2022-11-28#list-packages-for-an-organization
            response = requests.get(
                url="https://api.github.com/orgs/bowtie-json-schema/packages",
                params={
                    "package_type": "container",
                    "page": page,
                },
                headers={
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "Authorization": f"Bearer {gh_token}"
                }
            )

            with response:
                response.raise_for_status()
                payload = response.json()

            packages.extend(p["name"] for p in payload)
            page += 1
            if not payload:
                break
        return packages
