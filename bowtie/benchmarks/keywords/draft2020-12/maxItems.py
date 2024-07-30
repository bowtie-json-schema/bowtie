from pathlib import Path

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    name = "maxItems"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the maxItems keyword."
    )

    max_array_size = 100000
    array_size = 1000
    benchmarks = []
    tests = []
    testing_array_size = 10000

    while testing_array_size <= max_array_size:
        tests.append(
            dict(
                description=f"Testing Array Size - {testing_array_size}",
                instance=["random" for _ in range(testing_array_size)],
            ),
        )
        testing_array_size *= 10

    while array_size <= max_array_size:
        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array Size - {array_size}",
                description=(
                    f"Validating the `maxItems` keyword over array of size {array_size}."
                ),
                schema={
                    "maxItems": array_size,
                },
                tests=tests,
            ),
        )
        array_size *= 10

    return BenchmarkGroup(
        name=name,
        description=description,
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )
