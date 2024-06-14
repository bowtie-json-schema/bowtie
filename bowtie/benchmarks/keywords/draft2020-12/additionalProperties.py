import uuid
import random

max_num = 100000


def get_benchmark():
    max_array_size = 1000000
    benchmarks = []

    array_size = 1000

    while array_size <= max_array_size:
        allowed_properties = [uuid.uuid4().hex for _ in range(max_array_size-1)]

        middle_index = len(allowed_properties) // 2
        invalid_at_first = [uuid.uuid4().hex] + allowed_properties
        invalid_at_middle = allowed_properties[:middle_index] + [uuid.uuid4().hex] + allowed_properties[middle_index:]
        invalid_at_last = allowed_properties + [uuid.uuid4().hex]
        valid = allowed_properties

        benchmarks.append(dict(
            name=f"additionalProperties_{array_size}",
            description=(
                "A benchmark for measuring performance of the "
                "implementation for the additionalProperties keyword."
            ),
            schema=dict(
                properties={
                    key: {} for key in allowed_properties
                },
                additionalProperties=False,
            ),
            tests=[
                dict(description="Invalid at first", instance=_format_properties_as_instance(invalid_at_first)),
                dict(description="Invalid at middle", instance=_format_properties_as_instance(invalid_at_middle)),
                dict(description="Invalid at last", instance=_format_properties_as_instance(invalid_at_last)),
                dict(description="Valid", instance=_format_properties_as_instance(valid)),
            ],
        ))

        array_size *= 10

    return benchmarks


def _format_properties_as_instance(properties):
    return {
        key: random.randint(0, max_num) for key in properties
    }
