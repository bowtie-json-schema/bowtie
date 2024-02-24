"""
Responsible for defining the custom build hook plugin class.
"""

from pathlib import Path
from typing import Any
import os

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """
    A custom build hook plugin class.

    Subclasses the BuildHookInterface to let know hatchling
    about a custom build hook plugin and defines the
    initialize method.
    """

    def initialize(
        self,
        version: str,
        build_data: dict[str, Any],
    ) -> None:
        """
        Includes the json file in the final build.

        Reads the JSON file path from environment variable and
        force includes it in the final build.
        """
        if not os.environ.get("RUNNING_HATCH_SESSION"):
            return
        json_file_path = os.environ.get("IMPLEMENTATIONS_METADATA_FILE_PATH")

        if not json_file_path or not Path(json_file_path).exists():
            raise RuntimeError(
                "Generated JSON file not found",
                "Generated JSON file not found",
            )

        build_data["force_include"]["implementations.json"] = json_file_path
