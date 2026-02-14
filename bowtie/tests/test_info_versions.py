import os
import subprocess
import sys


def test_info_versions_survives_no_credentials():
    """
    Integration test: Ensure 'bowtie info --versions' does not crash
    when the environment lacks GitHub credentials.
    """
    clean_env = os.environ.copy()
    clean_env.pop("GITHUB_TOKEN", None)
    clean_env.pop("GH_TOKEN", None)

    cmd = [
        sys.executable,
        "-m",
        "bowtie",
        "info",
        "-i",
        "ghcr.io/bowtie-json-schema/python-jsonschema",
        "--versions",
    ]

    result = subprocess.run(
        cmd,
        env=clean_env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, f"Command failed. Stderr: {result.stderr}"

    assert "Traceback (most recent call last)" not in result.stderr
