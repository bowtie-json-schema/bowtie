from pathlib import Path

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


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
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        benchmark_type="test",
        dialects_supported=list(Dialect.known()),
    )
