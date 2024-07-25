from pathlib import Path
import uuid

from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    name = "minProperties"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the minProperties keyword."
    )

    max_num_properties = 100000
    num_properties = 1000

    benchmarks = []
    while num_properties <= max_num_properties:
        valid_object = _create_object_with_num_properties(num_properties)
        invalid_object_with_one_less = _create_object_with_num_properties(
            num_properties - 1,
        )
        invalid_object_with_one_property = _create_object_with_num_properties(
            1,
        )

        tests = [
            dict(
                description="Invalid Object with One",
                instance=invalid_object_with_one_property,
            ),
            dict(
                description="Invalid Object with One Less",
                instance=invalid_object_with_one_less,
            ),
            dict(description="Valid Object", instance=valid_object),
        ] if num_properties == max_num_properties else [
            dict(description="Valid Object", instance=valid_object)
        ]

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Minimum Required Properties - {num_properties}",
                description=(
                    f"Validating the `minProperties` keyword for minProperties - {num_properties}."
                ),
                schema=dict(minProperties=num_properties),
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


def _create_object_with_num_properties(num_properties):
    return {uuid.uuid4().hex: 10 for _ in range(num_properties)}
