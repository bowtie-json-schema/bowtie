import uuid


def get_benchmark():

    max_array_size = 1000000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]
        benchmarks.append(dict(
            name=f"enum_{array_size}",
            description=(
                "A benchmark for validation of the `enum` keyword."
            ),
            schema=dict(enum=array),
            tests=[
                dict(description="Valid First", instance=array[0]),
                dict(description="Valid Middle", instance=array[array_size//2]),
                dict(description="Valid Last", instance=array[-1]),
                dict(description="Invalid", instance=uuid.uuid4().hex),
            ],
        ))
        array_size *= 10

    return benchmarks
