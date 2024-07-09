import uuid


def get_benchmark():

    name = "minContains"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the minContains keyword."
    )

    max_array_size = 100000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]

        both_at_first = [1, 1] + array[:-2]
        both_at_middle = array[1:array_size//2] + [1, 1] + array[array_size//2:-1]
        both_at_last = array[:-2] + [1, 1]
        invalid = array

        benchmarks.append(dict(
            name=f"minContains_{array_size}",
            description=(
                "A benchmark for validation of the `minContains` keyword."
            ),
            schema={
                "type": "array",
                "contains": {
                    "type": "integer"
                },
                "minContains": 2
            },
            tests=[
                dict(description="Both at First", instance=both_at_first),
                dict(description="Both at Middle", instance=both_at_middle),
                dict(description="Both at Last", instance=both_at_last),
                dict(description="Invalid", instance=invalid),
            ],
        ))
        array_size *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )
