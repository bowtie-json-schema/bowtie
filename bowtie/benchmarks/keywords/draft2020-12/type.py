import uuid


def get_benchmark():
    name = "type"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the type keyword."
    )
    max_array_size = 1000000
    array_size = 10000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]
        benchmarks.append(dict(
            name=f"Array Size - {array_size}",
            description=(
                f"Validating the `type` keyword over array of size {array_size}."
            ),
            schema={
                "type": "array",
            },
            tests=[
                dict(description="Valid Array", instance=array),
                dict(description="Invalid String", instance="string"),
            ],
        ))
        array_size *= 10

    return dict(
        name=name,
        description=description,
        benchmarks=benchmarks,
    )
