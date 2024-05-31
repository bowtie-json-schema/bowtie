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
    stdout = result.stdout.decode().strip()
    truncated = [
        line  # [1:]: ignore the Usage: line
        for line in stdout.splitlines()[1:]
        if "..." in line
    ]
    assert not truncated, stdout


def test_commands_are_sorted_into_bins():
    """
    We want rich-click to be used to help users figure out which commands are
    relevant to them.

    Ideally it (or we) should have an API to *ensure* every subcommand we
    create goes in a bin, but until then let's assert against the "catch-all"
    bin appearing.
    """

    result = subprocess.run(
        [sys.executable, "-m", "bowtie", "--help"],
        capture_output=True,
        check=True,
    )
    stdout = result.stdout.decode().strip()
    assert not any("─ Commands ─" in i for i in stdout.splitlines()), stdout
