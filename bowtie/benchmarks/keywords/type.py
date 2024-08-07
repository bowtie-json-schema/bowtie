from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "type"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the type keyword."
    )
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks = []
    while array_length <= max_array_length:
        array = [uuid.uuid4().hex for _ in range(array_length)]
        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array length - {array_length}",
                description=(
                    f"Validating the `type` keyword over array of length {array_length}."
                ),
                schema={
                    "type": "array",
                },
                tests=[
                    dict(description="Valid Array", instance=array),
                ],
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
