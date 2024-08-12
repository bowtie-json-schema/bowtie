from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "maxContains"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the maxContains keyword."
    )
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks = []
    while array_length <= max_array_length:
        array = [uuid.uuid4().hex for _ in range(array_length)]

        all_at_first = [1, 1, 1] + array[:-3]
        all_at_middle = (
            array[2 : array_length // 2]
            + [1, 1, 1]
            + array[array_length // 2 : -1]
        )
        all_at_last = array[:-3] + [1, 1, 1]
        valid = array[:-1] + [1]

        tests = (
            [
                dict(description="All at First", instance=all_at_first),
                dict(description="All at Middle", instance=all_at_middle),
                dict(description="All at Last", instance=all_at_last),
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
                    f"Validating the `maxContains` keyword over array of length {array_length}."
                ),
                schema={
                    "type": "array",
                    "contains": {
                        "type": "integer",
                    },
                    "maxContains": 2,
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
