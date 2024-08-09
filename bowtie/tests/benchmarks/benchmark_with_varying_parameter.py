from pathlib import Path

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    return BenchmarkGroup(
        name="benchmark",
        description=(
            "This test is to test that when varying parameter is "
            "set then the benchmark output is as expected"
        ),
        benchmarks=[
            Benchmark.from_dict(
                name="benchmark 1",
                schema={
                    "type": "object",
                },
                description="benchmark 1",
                tests=[
                    {
                        "description": "test",
                        "instance": {},
                    },
                ],
            ),
            Benchmark.from_dict(
                name="benchmark 2",
                schema={
                    "type": "object",
                },
                description="benchmark 2",
                tests=[
                    {
                        "description": "test",
                        "instance": {},
                    },
                ],
            ),
        ],
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        benchmark_type="test",
        dialects_supported=list(Dialect.known()),
        varying_parameter="Array Size",
    )
