from pathlib import Path
from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    array_size = 100000
    beginning = [37] + [0] * (array_size - 1)
    middle = [0] * (array_size // 2) + [37] + [0] * (array_size // 2)
    end = [0] * (array_size - 1) + [37]
    invalid = [0] * array_size

    return BenchmarkGroup(
        name="contains",
        description="A benchmark for validation of the `contains` keyword.",
        benchmarks=[
            Benchmark.from_dict(
                name="contains",
                description="",
                schema={
                    "type": "array",
                    "contains": {"const": 37},
                },
                tests=[
                    dict(description="Empty array", instance=[]),
                    dict(description="Beginning of array", instance=beginning),
                    dict(description="Middle of array", instance=middle),
                    dict(description="End of array", instance=end),
                    dict(description="Invalid array", instance=invalid),
                ],
            )
        ],
        path=Path(__file__),
    )
