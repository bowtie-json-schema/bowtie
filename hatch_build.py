"""
Bowtie's Hatchling plugin, used for pregenerating implementation data.
"""

from __future__ import annotations

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
