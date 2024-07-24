from pathlib import Path

from bowtie._benchmarks import Benchmark, BenchmarkGroup


def get_benchmark():
    return BenchmarkGroup(
        name="benchmark",
        description="benchmark",
        benchmarks=[
            Benchmark.from_dict(
                name="benchmark",
                schema={
                    "type": "object",
                },
                description="benchmark",
                tests=[
                    {
                        "description": "test",
                        "instance": {},
                    },
                    {
                        "description": "test",
                        "instance": {},
                    },
                ],
            ),
        ],
        path=Path(__file__),
    )
