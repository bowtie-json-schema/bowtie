import uuid


def get_benchmark():
    name = "required"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the required keyword."
    )
    max_array_size = 100000

    benchmarks = []
    array_size = 1000

    while array_size*2 <= max_array_size:
        num_required_properties = array_size//2
        required_properties = [uuid.uuid4().hex for _ in range(num_required_properties)]

        object_keys = [uuid.uuid4().hex for _ in range(array_size)]
        all_at_beginning = required_properties + object_keys
        all_at_middle = object_keys[:array_size//2] + required_properties + object_keys[array_size//2:]
        all_at_last = object_keys + required_properties
        none_present = object_keys + object_keys

        benchmarks.append(dict(
            name=f"Array Size - {array_size}",
            description=(
                f"Validating the `required` keyword over array of size {array_size}."
            ),
            schema={
                "type": "object",
                "required": required_properties,
            },
            tests=[
                dict(
                    description="All required properties at beginning",
                    instance=_generate_object_with_keys(all_at_beginning),
                ),
                dict(
                    description="All required properties at middle",
                    instance=_generate_object_with_keys(all_at_middle),
                ),
                dict(
                    description="All required properties at last",
                    instance=_generate_object_with_keys(all_at_last),
                ),
                dict(
                    description="None of the required properties present",
                    instance=_generate_object_with_keys(none_present),
                ),
            ],
        ))
        array_size *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )

def _generate_object_with_keys(keys):
    return {
        key: uuid.uuid4().hex for key in keys
    }
