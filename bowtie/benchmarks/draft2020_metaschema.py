
from jsonschema_specifications import REGISTRY as SPECIFICATIONS

from bowtie._benchmarks import Benchmark

DRAFT202012_DIALECT_URI = "https://json-schema.org/draft/2020-12/schema"


def get_benchmark():
    return Benchmark.from_dict(
        name="Draft2020-12_MetaSchema",
        description=(
            "A benchmark for validation of the Draft2020-12 MetaSchema."
        ),
        schema=SPECIFICATIONS.contents(DRAFT202012_DIALECT_URI),
        tests=[
            dict(
                description="Validating metaschema against metaschema",
                instance=SPECIFICATIONS.contents(
                    DRAFT202012_DIALECT_URI,
                ),
            ),
        ],
    )
