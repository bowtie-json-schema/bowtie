from pathlib import Path

from url.url import URL

from bowtie._benchmarks import BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    num_useless_keywords = 300000

    return BenchmarkGroup.from_dict(
        data=dict(
            name="useless_keywords",
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
            description=(
                "A benchmark for validation of schemas containing "
                "lots of useless keywords. "
                "Checks we filter them out once, ahead of time."
            ),
            schema=dict(
                [
                    ("not", {"const": 42}),
                    *((str(i), i) for i in range(num_useless_keywords // 2)),
                    ("type", "integer"),
                    *(
                        (str(i), i)
                        for i in range(
                            num_useless_keywords // 2,
                            num_useless_keywords,
                        )
                    ),
                    ("minimum", 37),
                ],
            ),
            tests=[
                dict(description="Beginning of schema", instance=42),
                dict(description="Middle of schema", instance="foo"),
                dict(description="End of schema", instance=12),
                dict(description="Valid", instance=3737),
            ],
        ),
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )
