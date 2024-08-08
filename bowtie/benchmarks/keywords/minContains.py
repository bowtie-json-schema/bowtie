from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():

    name = "minContains"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the minContains keyword."
    )
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks = []
    while array_length <= max_array_length:
        array = [uuid.uuid4().hex for _ in range(array_length)]

        both_at_first = [1, 1] + array[:-2]
        both_at_middle = (
            array[1 : array_length // 2]
            + [1, 1]
            + array[array_length // 2 : -1]
        )
        both_at_last = array[:-2] + [1, 1]
        invalid = array

        tests = (
            [
                dict(description="Both at First", instance=both_at_first),
                dict(
                    description="Both at Middle",
                    instance=both_at_middle,
                ),
                dict(description="Both at Last", instance=both_at_last),
                dict(description="Invalid", instance=invalid),
            ]
            if array_length == max_array_length
            else [
                dict(
                    description="Both at Middle",
                    instance=both_at_middle,
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"minContains_{array_length}",
                description=(
                    "A benchmark for validation of the `minContains` keyword."
                ),
                schema={
                    "type": "array",
                    "contains": {"type": "integer"},
                    "minContains": 2,
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
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )
