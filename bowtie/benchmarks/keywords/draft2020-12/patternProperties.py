from pathlib import Path
import random
import string

from bowtie._benchmarks import Benchmark, BenchmarkGroup

max_num = 100000


def get_benchmark():
    name = "patternProperties"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the patternProperties keyword."
    )
    max_num_properties = 100000
    benchmarks = []

    num_properties = 1000

    while num_properties <= max_num_properties:
        property_value_pairs = [
            (_random_string(), random.randint(0, max_num))
            for _ in range(num_properties)
        ]

        invalid_at_first = [
            (_random_string(), "string"),
        ] + property_value_pairs[1:]
        invalid_at_middle = (
            property_value_pairs[: num_properties // 2]
            + [(_random_string(), "string")]
            + property_value_pairs[num_properties // 2 : -1]
        )
        invalid_at_last = property_value_pairs[1:] + [
            (_random_string(), "string"),
        ]
        valid = property_value_pairs

        tests = (
            [
                dict(
                    description="Invalid Property at first",
                    instance=_get_instance_object(invalid_at_first),
                ),
                dict(
                    description="Invalid Property at middle",
                    instance=_get_instance_object(invalid_at_middle),
                ),
                dict(
                    description="Invalid Property at last",
                    instance=_get_instance_object(invalid_at_last),
                ),
                dict(
                    description="Valid",
                    instance=_get_instance_object(valid),
                ),
            ]
            if num_properties == max_num_properties
            else [
                dict(
                    description="Valid",
                    instance=_get_instance_object(valid),
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"No. of Properties - {num_properties}",
                description=(
                    "Validating the `patternProperties` keyword with "
                    f"no. of properties {num_properties}."
                ),
                schema=dict(
                    type="object",
                    patternProperties={
                        "^[a-z]+$": {"type": "integer"},
                    },
                ),
                tests=tests,
            ),
        )

        num_properties *= 10

    return BenchmarkGroup(
        name=name,
        description=description,
        benchmarks=benchmarks,
        path=Path(__file__),
    )


def _get_instance_object(property_value_pairs):
    return dict(property_value_pairs)


def _random_string():
    string_size = 100
    return "".join(
        random.choice(string.ascii_lowercase) for _ in range(string_size)
    )
