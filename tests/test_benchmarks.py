from pathlib import Path

from bowtie._core import validator_registry
from bowtie._benchmarks import get_default_benchmarks

validator = validator_registry().for_uri(
    "tag:bowtie.report,2024:benchmarks",
)


def test_valid_benchmark_files():
    bowtie_dir = Path(__file__).parent.parent.joinpath("bowtie")
    benchmark_dir = bowtie_dir.joinpath("benchmarks").iterdir()

    desired_extensions = {".json", ".py"}
    other_files = (
        file
        for file in benchmark_dir
        if file.is_file() and file.suffix not in desired_extensions and file.name != "__pycache__"
    )

    assert not any(other_files)


def test_validate_benchmarks():
    default_benchmarks = get_default_benchmarks()
    for benchmark in default_benchmarks:
        validator.validate(benchmark)
