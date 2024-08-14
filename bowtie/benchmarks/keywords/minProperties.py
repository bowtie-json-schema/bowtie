from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "minProperties"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the implementation "
        "for the minProperties keyword."
    )
    max_num_properties = 100000
    varying_parameter = "No. of minProperties Needed"

    num_properties = 1000
    benchmarks = []
    while num_properties <= max_num_properties:
        valid_object = _create_object_with_num_properties(num_properties)
        invalid_object_with_one_less = _create_object_with_num_properties(
            num_properties - 1,
        )
        invalid_object_with_one_property = _create_object_with_num_properties(
            1,
        )

        tests = (
            [
                dict(
                    description="Invalid Object with One",
                    instance=invalid_object_with_one_property,
                ),
                dict(
                    description="Invalid Object with One Less",
                    instance=invalid_object_with_one_less,
                ),
                dict(description="Valid Object", instance=valid_object),
            ]
            if num_properties == max_num_properties
            else [
                dict(description="Valid Object", instance=valid_object),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Minimum Required Properties - {num_properties}",
                description=(
                    f"Validating the `minProperties` keyword for minProperties - {num_properties}."
                ),
                schema=dict(minProperties=num_properties),
                tests=tests,
            ),
        )
        num_properties *= 10

    return BenchmarkGroup(
        name=name,
        benchmark_type=benchmark_type,
        description=description,
        dialects_supported=[
            Dialect.from_str("https://json-schema.org/draft/2020-12/schema"),
            Dialect.from_str("https://json-schema.org/draft/2019-09/schema"),
            Dialect.from_str("http://json-schema.org/draft-07/schema#"),
            Dialect.from_str("http://json-schema.org/draft-06/schema#"),
            Dialect.from_str("http://json-schema.org/draft-04/schema#"),
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )


def _create_object_with_num_properties(num_properties):
    return {uuid.uuid4().hex: 10 for _ in range(num_properties)}
