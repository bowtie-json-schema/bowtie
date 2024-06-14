import uuid


def get_benchmark():

    max_array_size = 1000000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:
        array = [uuid.uuid4().hex for _ in range(array_size)]
        benchmarks.append(dict(
            name=f"type_{array_size}",
            description=(
                "A benchmark for validation of the `type` keyword."
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

    return benchmarks
