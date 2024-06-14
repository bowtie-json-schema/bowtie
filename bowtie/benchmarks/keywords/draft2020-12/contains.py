def get_benchmark():

    max_array_size = 1000000
    array_size = 1000

    benchmarks = []
    while array_size <= max_array_size:

        start = [37] + [0] * (array_size - 1)
        middle = [0] * (array_size // 2) + [37] + [0] * (array_size // 2)
        end = [0] * (array_size - 1) + [37]
        invalid = [0] * array_size

        benchmarks.append(dict(
            name=f"contains_{array_size}",
            description=(
                "A benchmark for validation of the `contains` keyword."
            ),
            schema={
                "type": "array",
                "contains": {"const": 37},
            },
            tests=[
                dict(description="Beginning of array", instance=start),
                dict(description="Middle of array", instance=middle),
                dict(description="End of array", instance=end),
                dict(description="Invalid array", instance=invalid),
            ],
        ))
        array_size *= 10

    return benchmarks
