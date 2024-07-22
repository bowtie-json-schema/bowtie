import random
import string

from pathlib import Path
from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    name = "minLength"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the minLength keyword."
    )

    max_string_size = 100000
    string_size = 1000
    benchmarks = []

    tests = []
    testing_string_size = 10000
    while testing_string_size <= max_string_size:
        tests.append(
            dict(
                description=f"Testing String Size - {testing_string_size}",
                instance="".join(
                    random.choice(string.ascii_letters)
                    for _ in range(testing_string_size)
                ),
            ),
        )
        testing_string_size *= 10

    while string_size <= max_string_size:
        benchmarks.append(
            Benchmark.from_dict(
                name=f"String Size - {string_size}",
                description=(
                    f"Validating the `minLength` keyword over string of size {string_size}."
                ),
                schema={
                    "type": "string",
                    "minLength": string_size,
                },
                tests=tests,
            )
        )
        string_size *= 10

    return BenchmarkGroup(
        name=name,
        description=description,
        benchmarks=benchmarks,
        path=Path(__file__),
    )
