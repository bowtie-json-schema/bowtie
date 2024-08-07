from pathlib import Path

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "contains"
    benchmark_type = "keyword"
    description = "A benchmark for validation of the `contains` keyword."
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks = []
    while array_length <= max_array_length:

        start = [37] + [0] * (array_length - 1)
        middle = [0] * (array_length // 2) + [37] + [0] * (array_length // 2)
        end = [0] * (array_length - 1) + [37]
        invalid = [0] * array_length

        tests = (
            [
                dict(description="Empty array", instance=[]),
                dict(description="Beginning of array", instance=start),
                dict(description="Middle of array", instance=middle),
                dict(description="End of array", instance=end),
                dict(description="Invalid array", instance=invalid),
            ]
            if array_length == max_array_length
            else [
                dict(description="Middle of array", instance=middle),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array length - {array_length}",
                description=(
                    "Validating contains keyword over an array "
                    f"of length {array_length}"
                ),
                schema={
                    "type": "array",
                    "contains": {"const": 37},
                },
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
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )
