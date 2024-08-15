from pathlib import Path
import random
import string
import uuid

from url.url import URL

from bowtie._benchmarks import Benchmark, BenchmarkGroup
from bowtie._core import Dialect


def get_benchmark():
    name = "propertyNames"
    benchmark_type = "keyword"
    description = (
        "A benchmark for measuring performance of the "
        "implementation for the propertyNames keyword."
    )
    max_object_length = 100000
    varying_parameter = "Object length"

    object_length = 1000
    benchmarks = []
    while object_length <= max_object_length:
        object = {uuid.uuid4().hex: 10 for _ in range(object_length)}
        invalid_property = "".join(
            random.choice(string.ascii_letters) for _ in range(7)
        )

        invalid_at_first = {invalid_property: 10}
        invalid_at_first.update(object)

        invalid_at_middle = {
            uuid.uuid4().hex: 10 for _ in range(object_length // 2)
        }
        invalid_at_middle.update({invalid_property: 10})
        invalid_at_middle.update(
            {uuid.uuid4().hex: 10 for _ in range(object_length // 2)},
        )

        invalid_at_last = object.copy()
        invalid_at_last.update({invalid_property: 10})

        valid = {
            "".join(random.choice(string.ascii_letters) for _ in range(1)): 10
            for _ in range(object_length)
        }

        tests = (
            [
                dict(
                    description="Invalid at First",
                    instance=invalid_at_first,
                ),
                dict(
                    description="Invalid at Middle",
                    instance=invalid_at_middle,
                ),
                dict(
                    description="Invalid at Last",
                    instance=invalid_at_last,
                ),
                dict(description="Valid", instance=valid),
            ]
            if object_length == max_object_length
            else [
                dict(description="Valid", instance=valid),
            ]
        )

        benchmarks.append(
            Benchmark.from_dict(
                name=f"Num of Properties - {object_length}",
                description=(
                    f"Validating the `propertyNames` keyword over object of length {object_length}."
                ),
                schema={"propertyNames": {"maxLength": 5}},
                tests=tests,
            ),
        )
        object_length *= 10

    return BenchmarkGroup(
        name=name,
        benchmark_type=benchmark_type,
        description=description,
        dialects_supported=[
            Dialect.from_str("https://json-schema.org/draft/2020-12/schema"),
            Dialect.from_str("https://json-schema.org/draft/2019-09/schema"),
            Dialect.from_str("http://json-schema.org/draft-07/schema#"),
            Dialect.from_str("http://json-schema.org/draft-06/schema#"),
        ],
        benchmarks=benchmarks,
        uri=URL.parse(Path(__file__).absolute().as_uri()),
        varying_parameter=varying_parameter,
    )
