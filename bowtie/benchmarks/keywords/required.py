from pathlib import Path
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "required"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the required keyword."
    )
    max_array_length = 100000
    varying_parameter = "Array length"

    array_length = 1000
    benchmarks = []
    while array_length * 2 <= max_array_length:
        num_required_properties = array_length // 2
        required_properties = [
            uuid.uuid4().hex for _ in range(num_required_properties)
        ]

        object_keys = [uuid.uuid4().hex for _ in range(array_length)]
        all_at_beginning = required_properties + object_keys
        all_at_middle = (
            object_keys[: array_length // 2]
            + required_properties
            + object_keys[array_length // 2 :]
        )
        all_at_last = object_keys + required_properties
        none_present = object_keys + object_keys

        tests = (
            [
                dict(
                    description="All required properties at beginning",
                    instance=_generate_object_with_keys(all_at_beginning),
                ),
                dict(
                    description="All required properties at middle",
                    instance=_generate_object_with_keys(all_at_middle),
                ),
                dict(
                    description="All required properties at last",
                    instance=_generate_object_with_keys(all_at_last),
                ),
                dict(
                    description="None of the required properties present",
                    instance=_generate_object_with_keys(none_present),
                ),
            ]
            if array_length == max_array_length
            else [
                dict(
                    description="None of the required properties present",
                    instance=_generate_object_with_keys(none_present),
                ),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Array length - {array_length}",
                description=(
                    f"Validating the `required` keyword over array of length {array_length}."
                ),
                schema={
                    "type": "object",
                    "required": required_properties,
                },
                tests=tests,
            ),
        )
        array_length *= 10

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
            Dialect.from_str("http://json-schema.org/draft-03/schema#"),
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )


def _generate_object_with_keys(keys):
    return {key: uuid.uuid4().hex for key in keys}
