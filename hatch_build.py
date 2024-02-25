"""
Responsible for defining the custom build hook plugin class.
"""

from pathlib import Path
from typing import Any
import os
import shlex
import subprocess

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
        Build the implementations metadata file.

        Runs various commands and build / generates the
        implementations.json file to force include in the
        final built package.
        """
        if not os.environ.get("RUNNING_HATCH_SESSION"):
            return

        pip_path = "pip"
        subprocess.run(
            [pip_path, "install", "-r", "requirements.txt"],
            check=True,
        )

        bowtie_info_cmd = ["bowtie", "info"]
        impls = os.listdir("implementations")
        for impl in impls:
            bowtie_info_cmd.extend(["-i", impl])
        bowtie_info_cmd.extend(["--format", "json"])

        output_file_path = Path("implementations.json").absolute()

        with Path.open(output_file_path, "w") as output_file:
            command = " ".join(shlex.quote(arg) for arg in bowtie_info_cmd)
            subprocess.run(
                command,
                stdout=output_file,
                check=True,
            )

        build_data["force_include"]["implementations.json"] = output_file_path
