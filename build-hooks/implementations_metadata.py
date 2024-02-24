from hatchling.builders.hooks.plugin.interface import BuildHookInterface
import os

class ImplementationsMetadataHook(BuildHookInterface): # type: ignore[reportMissingTypeArgument]
    def initialize(
        self, 
        version: str, 
        build_data # type: ignore[reportMissingParameterType]
    ) -> None:
        """
        Reads the JSON file path from environment variable and adds it to shared data.
        """
        json_file_path = os.environ.get("IMPLEMENTATIONS_METADATA_FILE_PATH")

        if not json_file_path or not os.path.exists(json_file_path):
            raise RuntimeError(
                "Generated JSON file not found"
            )

        # Add file to shared data
        build_data["shared-data"] = {
            json_file_path: "bowtie/data/implementations.json"
        }
