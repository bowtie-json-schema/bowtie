from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from typing import Any
import os

class CustomBuildHook(BuildHookInterface):
    def initialize(
        self, 
        version: str, 
        build_data: dict[str, Any]
    ) -> None:
        """
        Reads the JSON file path from environment variable and adds it to shared data.
        """
        if not os.environ.get("RUNNING_HATCH_SESSION"):
            return
        print('in here')
        json_file_path = os.environ.get("IMPLEMENTATIONS_METADATA_FILE_PATH")

        if not json_file_path or not os.path.exists(json_file_path):
            raise RuntimeError(
                "Generated JSON file not found"
            )

        build_data['force_include']['implementations.json'] = json_file_path
