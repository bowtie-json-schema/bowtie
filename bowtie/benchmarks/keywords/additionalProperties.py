from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "additionalProperties"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the additionalProperties keyword."
    )
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks: list[Benchmark] = []
    while array_length <= max_array_length:
        allowed_properties = [
            uuid.uuid4().hex for _ in range(max_array_length - 1)
        ]

        middle_index = len(allowed_properties) // 2
        invalid_at_first = [uuid.uuid4().hex, *allowed_properties]
        invalid_at_middle = (
            allowed_properties[:middle_index]
            + [uuid.uuid4().hex]
            + allowed_properties[middle_index:]
        )
        invalid_at_last = [*allowed_properties, uuid.uuid4().hex]
        valid = allowed_properties

        tests = (
            [
                dict(
                    description="Invalid at first",
                    instance=_format_properties_as_instance(
                        invalid_at_first,
                    ),
                ),
                dict(
                    description="Invalid at middle",
                    instance=_format_properties_as_instance(
                        invalid_at_middle,
                    ),
                ),
                dict(
                    description="Invalid at last",
                    instance=_format_properties_as_instance(
                        invalid_at_last,
                    ),
                ),
                dict(
                    description="Valid",
                    instance=_format_properties_as_instance(valid),
                ),
            ]
            if array_length == max_array_length
            else [
                dict(
                    description="Valid",
                    instance=_format_properties_as_instance(valid),
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array length - {array_length}",
                description=(
                    f"Validating additionalProperties keyword over array of length {array_length}"
                ),
                schema=dict(
                    properties={key: {} for key in allowed_properties},
                    additionalProperties=False,
                ),
                tests=tests,
            ),
        )

        array_length *= 10

    return BenchmarkGroup(
        name=name,
        benchmark_type=benchmark_type,
        dialects_supported=[
            Dialect.from_str("https://json-schema.org/draft/2020-12/schema"),
            Dialect.from_str("https://json-schema.org/draft/2019-09/schema"),
            Dialect.from_str("http://json-schema.org/draft-07/schema#"),
            Dialect.from_str("http://json-schema.org/draft-06/schema#"),
            Dialect.from_str("http://json-schema.org/draft-04/schema#"),
            Dialect.from_str("http://json-schema.org/draft-03/schema#"),
        ],
        description=description,
        benchmarks=benchmarks,
        varying_parameter=varying_parameter,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )


def _format_properties_as_instance(properties):
    return dict.fromkeys(properties, 1000)
