from pathlib import Path

from url.url import URL

from bowtie._benchmarks import BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    array_size = 100000
    beginning = [37] + [0] * (array_size - 1)
    middle = [0] * (array_size // 2) + [37] + [0] * (array_size // 2)
    end = [0] * (array_size - 1) + [37]
    invalid = [0] * array_size

    return BenchmarkGroup.from_dict(
        data=dict(
            name="contains",
            benchmark_type="default",
            dialects_supported=[
                Dialect.from_str(
                    "https://json-schema.org/draft/2020-12/schema",
                ),
                Dialect.from_str(
                    "https://json-schema.org/draft/2019-09/schema",
                ),
                Dialect.from_str("http://json-schema.org/draft-07/schema#"),
                Dialect.from_str("http://json-schema.org/draft-06/schema#"),
            ],
            description="A benchmark for validation of the `contains` keyword.",
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
        ),
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )
