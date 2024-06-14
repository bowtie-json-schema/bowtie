import string
import random


def get_benchmark():

    max_string_size = 1000000
    string_size = 1000

    benchmarks = []

    tests = []
    testing_string_size = 10000
    while testing_string_size <= max_string_size:
        tests.append(
            dict(
                description=f"String Size {testing_string_size}",
                instance=''.join(random.choice(string.ascii_letters) for _ in range(testing_string_size))
            )
        )
        testing_string_size *= 10

    while string_size <= max_string_size:
        benchmarks.append(dict(
            name=f"minLength_{string_size}",
            description=(
                "A benchmark for validation of the `minLength` keyword."
            ),
            schema={
                "type": "string",
                "minLength": string_size,
            },
            tests=tests,
        ))
        string_size *= 10

    return benchmarks
