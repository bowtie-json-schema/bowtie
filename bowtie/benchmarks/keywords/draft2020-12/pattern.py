from pathlib import Path
import random
import string

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    name = "pattern"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the pattern keyword."
    )

    max_string_size = 100000
    string_size = 1000

    benchmarks = []
    while string_size <= max_string_size:
        letters = string.ascii_letters
        random_letter_string = "".join(
            random.choice(letters) for _ in range(string_size)
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
                        random_letter_string[: string_size // 2]
                        + "1"
                        + random_letter_string[string_size // 2 :]
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
            if string_size == max_string_size
            else [
                dict(
                    description="Valid String",
                    instance=random_letter_string,
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"String Size - {string_size}",
                description=(
                    f"Validating the `pattern` keyword over string of size {string_size}."
                ),
                schema=dict(type="string", pattern="^[a-zA-Z]+$"),
                tests=tests,
            ),
        )
        string_size *= 10

    return BenchmarkGroup(
        name=name,
        description=description,
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )
