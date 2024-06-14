def get_benchmark():
    max_array_size = 1000000
    array_size = 1000

    benchmarks = []

    tests = []
    testing_array_size = 10000
    while testing_array_size <= max_array_size:
        tests.append(
            dict(
                description=f"Array Size {testing_array_size}",
                instance=["random" for _ in range(testing_array_size)]
            )
        )
        testing_array_size *= 10

    while array_size <= max_array_size:
        benchmarks.append(dict(
            name=f"maxItems_{array_size}",
            description=(
                "A benchmark for validation of the `maxItems` keyword."
            ),
            schema={
                "maxItems": array_size,
            },
            tests=tests,
        ))
        array_size *= 10

    return benchmarks
