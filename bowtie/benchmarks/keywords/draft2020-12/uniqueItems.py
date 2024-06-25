def get_benchmark():
    max_array_size = 2000000
    benchmarks = []

    array_size = 2000
    while array_size <= max_array_size:

        first_two_duplicate = [1, 1] + [i for i in range(2, array_size-2)]
        middle_two_duplicate = [i for i in range(0, array_size // 2)] + [-1, -1] + [i for i in range(array_size // 2, array_size)]
        last_two_duplicate = [i for i in range(2, array_size-2)] + [1, 1]
        valid = [i for i in range(array_size)]

        benchmarks.append(dict(
            name=f"uniqueItems_{array_size}",
            description=(
                "A benchmark for measuring performance of the "
                "implementation for the uniqueItems keyword."
            ),
            schema=dict(
                uniqueItems=True,
            ),
            tests=[
                dict(description="First Two Duplicate", instance=first_two_duplicate),
                dict(description="Middle Two Duplicate", instance=middle_two_duplicate),
                dict(description="Last Two Duplicate", instance=last_two_duplicate),
                dict(description="Valid", instance=valid),
            ],
        ))

        array_size *= 10

    return benchmarks