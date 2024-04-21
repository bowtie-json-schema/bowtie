import subprocess
import sys


def test_help_is_not_truncated():
    """
    Click will truncate short help messages if they are too long.

    That should never happen.
    """

    result = subprocess.run(
        [sys.executable, "-m", "bowtie", "--help"],
        capture_output=True,
        check=True,
    )
    truncated = [
        line  # [1:]: ignore the Usage: line
        for line in result.stdout.decode().strip().splitlines()[1:]
        if "..." in line
    ]
    assert not truncated
