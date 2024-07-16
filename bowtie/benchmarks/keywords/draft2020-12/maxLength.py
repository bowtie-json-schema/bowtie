import random
import string


def get_benchmark():
    name = "maxLength"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the maxLength keyword."
    )

    max_string_size = 100000
    string_size = 1000
    benchmarks = []

    tests = []
    testing_string_size = 10000
    while testing_string_size <= max_string_size:
        tests.append(
            dict(
                description=f"Testing String Size - {testing_string_size}",
                instance="".join(
                    random.choice(string.ascii_letters)
                    for _ in range(testing_string_size)
                ),
            ),
        )
        testing_string_size *= 10

    while string_size <= max_string_size:
        benchmarks.append(
            dict(
                name=f"String Size - {string_size}",
                description=(
                    f"Validating the `maxLength` keyword over string of size {string_size}."
                ),
                schema={
                    "type": "string",
                    "maxLength": string_size,
                },
                tests=tests,
            )
        )
        string_size *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )
