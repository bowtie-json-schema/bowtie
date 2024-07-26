from bowtie._benchmarks import Benchmark


def get_benchmark():
    return Benchmark.from_dict(
        name="benchmark",
        schema={
            "type": "object",
        },
        description="benchmark",
        tests=[
            {
                "description": "test",
                "instance": {
                    "a": "b",
                },
            },
        ],
    )
