import string
import uuid
import random


def get_benchmark():
    name = "propertyNames"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the propertyNames keyword."
    )

    max_object_size = 100000
    object_size = 1000

    benchmarks = []
    while object_size <= max_object_size:
        object = {uuid.uuid4().hex: 10 for _ in range(object_size)}
        invalid_property = "".join(random.choice(string.ascii_letters) for _ in range(7))

        invalid_at_first = {invalid_property: 10}
        invalid_at_first.update(object)

        invalid_at_middle = {
            uuid.uuid4().hex: 10
            for _ in range(object_size//2)
        }
        invalid_at_middle.update(
            {invalid_property: 10}
        )
        invalid_at_middle.update({
            uuid.uuid4().hex: 10
            for _ in range(object_size // 2)
        })

        invalid_at_last = object.copy()
        invalid_at_last.update({invalid_property: 10})

        valid = {
            "".join(random.choice(string.ascii_letters) for _ in range(1)): 10
            for _ in range(object_size)
        }

        benchmarks.append(dict(
            name=f"Num of Properties - {object_size}",
            description=(
                f"Validating the `propertyNames` keyword over object of size {object_size}."
            ),
            schema={
                "propertyNames": {"maxLength": 5}
            },
            tests=[
                dict(description="Invalid at First", instance=invalid_at_first),
                dict(description="Invalid at Middle", instance=invalid_at_middle),
                dict(description="Invalid at Last", instance=invalid_at_last),
                dict(description="Valid", instance=valid),
            ],
        ))
        object_size *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )
