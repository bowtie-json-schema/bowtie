import uuid


def get_benchmark():

    max_array_size = 1000000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]

        invalid_at_first = [1] + array[:-1]
        invalid_at_middle = array[:array_size//2] + [1] + array[array_size//2:-1]
        invalid_at_last = array[:-1] + [1]
        valid = array

        benchmarks.append(dict(
            name=f"items_{array_size}",
            description=(
                "A benchmark for validation of the `items` keyword."
            ),
            schema={
                "type": "array",
                "items": {"type": "string"}
            },
            tests=[
                dict(description="Invalid at First", instance=invalid_at_first),
                dict(description="Invalid at Middle", instance=invalid_at_middle),
                dict(description="Invalid at Last", instance=invalid_at_last),
                dict(description="Valid", instance=valid),
            ],
        ))
        array_size *= 10

    return benchmarks
