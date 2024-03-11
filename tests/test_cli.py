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
    first, *lines = result.stdout.decode().splitlines()

    # It's fine for the first line to, that's our Usage line, so ignore it.
    assert first.casefold().startswith("usage")

    truncated = [line for line in lines if line.strip().endswith("...")]
    assert not truncated
