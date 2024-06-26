import uuid


def get_benchmark():
    name = "enum"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the enum keyword."
    )

    max_array_size = 1000000
    array_size = 10000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]
        benchmarks.append(dict(
            name=f"Array Size - {array_size}",
            description=(
                f"Validating the `enum` keyword over array of size {array_size}."
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

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )
