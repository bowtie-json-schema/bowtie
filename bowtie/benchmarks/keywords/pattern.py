from pathlib import Path
import random
import string

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "pattern"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the pattern keyword."
    )
    max_string_length = 100000
    varying_parameter = "String length"

    string_length = 1000
    benchmarks = []
    while string_length <= max_string_length:
        letters = string.ascii_letters
        random_letter_string = "".join(
            random.choice(letters) for _ in range(string_length)
        )

        tests = (
            [
                dict(description="Empty String", instance=""),
                dict(
                    description="Invalid Char at First",
                    instance="1" + random_letter_string,
                ),
                dict(
                    description="Invalid Char at Middle",
                    instance=(
                        random_letter_string[: string_length // 2]
                        + "1"
                        + random_letter_string[string_length // 2 :]
                    ),
                ),
                dict(
                    description="Invalid Char at Last",
                    instance=random_letter_string + "1",
                ),
                dict(
                    description="Valid String",
                    instance=random_letter_string,
                ),
            ]
            if string_length == max_string_length
            else [
                dict(
                    description="Valid String",
                    instance=random_letter_string,
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"String length - {string_length}",
                description=(
                    f"Validating the `pattern` keyword over string of length {string_length}."
                ),
                schema=dict(type="string", pattern="^[a-zA-Z]+$"),
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
