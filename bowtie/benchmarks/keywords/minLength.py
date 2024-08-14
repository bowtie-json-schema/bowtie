from pathlib import Path
import random
import string

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "minLength"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the minLength keyword."
    )
    max_string_length = 100000
    varying_parameter = "String length"

    string_length = 1000
    benchmarks = []
    tests = []
    testing_string_length = 10000

    while testing_string_length <= max_string_length:
        tests.append(
            dict(
                description=f"Testing String length - {testing_string_length}",
                instance="".join(
                    random.choice(string.ascii_letters)
                    for _ in range(testing_string_length)
                ),
            ),
        )
        testing_string_length *= 10

    while string_length <= max_string_length:
        benchmarks.append(
            Benchmark.from_dict(
                name=f"String length - {string_length}",
                description=(
                    f"Validating the `minLength` keyword over string of length {string_length}."
                ),
                schema={
                    "type": "string",
                    "minLength": string_length,
                },
                tests=tests,
            ),
        )
        string_length *= 10

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
