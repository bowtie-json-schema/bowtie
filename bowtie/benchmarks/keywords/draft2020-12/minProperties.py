import uuid


def get_benchmark():
    name = "minProperties"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the minProperties keyword."
    )

    max_num_properties = 1000000
    num_properties = 10000

    benchmarks = []
    while num_properties <= max_num_properties:
        valid_object = _create_object_with_num_properties(num_properties)
        invalid_object_with_one_less = _create_object_with_num_properties(
            num_properties-1
        )
        invalid_object_with_one_property = _create_object_with_num_properties(
            1
        )
        benchmarks.append(dict(
            name=f"Minimum Required Properties - {num_properties}",
            description=(
                f"Validating the `minProperties` keyword for minProperties - {num_properties}."
            ),
            schema=dict(minProperties=num_properties),
            tests=[
                dict(description="Invalid Object with One", instance=invalid_object_with_one_property),
                dict(description="Invalid Object with One Less", instance=invalid_object_with_one_less),
                dict(description="Valid Object", instance=valid_object),
            ],
        ))
        num_properties *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )


def _create_object_with_num_properties(num_properties):
    return {
        uuid.uuid4().hex: 10 for _ in range(num_properties)
    }
