import uuid


def get_benchmark():

    max_array_size = 1000000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]

        all_at_first = [1, 1, 1] + array[:-3]
        all_at_middle = array[2:array_size//2] + [1, 1, 1] + array[array_size//2:-1]
        all_at_last = array[:-3] + [1, 1, 1]
        valid = array[:-1] + [1]

        benchmarks.append(dict(
            name=f"maxContains_{array_size}",
            description=(
                "A benchmark for validation of the `maxContains` keyword."
            ),
            schema={
                "type": "array",
                "contains": {
                    "type": "integer"
                },
                "maxContains": 2
            },
            tests=[
                dict(description="All at First", instance=all_at_first),
                dict(description="All at Middle", instance=all_at_middle),
                dict(description="All at Last", instance=all_at_last),
                dict(description="Valid", instance=valid),
            ],
        ))
        array_size *= 10

    return benchmarks
