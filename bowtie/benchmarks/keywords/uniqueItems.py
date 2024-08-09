from pathlib import Path

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "uniqueItems"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the uniqueItems keyword."
    )
    max_array_length = 200000
    varying_parameter = "Array length"

    array_length = 2000
    benchmarks = []
    while array_length <= max_array_length:
        first_two_duplicate = [1, 1, *list(range(2, array_length - 2))]
        middle_two_duplicate = [
            *list(range(array_length // 2)),
            -1,
            -1,
            *list(range(array_length // 2, array_length)),
        ]
        last_two_duplicate = [*list(range(2, array_length - 2)), 1, 1]
        valid = list(range(array_length))

        tests = (
            [
                dict(
                    description="First Two Duplicate",
                    instance=first_two_duplicate,
                ),
                dict(
                    description="Middle Two Duplicate",
                    instance=middle_two_duplicate,
                ),
                dict(
                    description="Last Two Duplicate",
                    instance=last_two_duplicate,
                ),
                dict(description="Valid", instance=valid),
            ]
            if array_length == max_array_length
            else [
                dict(description="Valid", instance=valid),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array length - {array_length}",
                description=(
                    f"Validating the `uniqueItems` keyword over array of length {array_length}."
                ),
                schema=dict(
                    uniqueItems=True,
                ),
                tests=tests,
            ),
        )

        array_length *= 10

    return BenchmarkGroup(
        name=name,
        benchmark_type=benchmark_type,
        description=description,
        dialects_supported=[
            Dialect.from_str("https://json-schema.org/draft/2020-12/schema"),
            Dialect.from_str("https://json-schema.org/draft/2019-09/schema"),
            Dialect.from_str("http://json-schema.org/draft-07/schema#"),
            Dialect.from_str("http://json-schema.org/draft-06/schema#"),
            Dialect.from_str("http://json-schema.org/draft-04/schema#"),
            Dialect.from_str("http://json-schema.org/draft-03/schema#"),
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )
