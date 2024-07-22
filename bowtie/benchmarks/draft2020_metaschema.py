from jsonschema_specifications import REGISTRY as SPECIFICATIONS
from pathlib import Path
from bowtie._benchmarks import Benchmark, BenchmarkGroup


DRAFT202012_DIALECT_URI = "https://json-schema.org/draft/2020-12/schema"


def get_benchmark():
    return BenchmarkGroup(
        name="Draft2020-12_MetaSchema",
        description=(
            "A benchmark for validation of the 2020-12 dialect's metaschema"
        ),
        benchmarks=[
            Benchmark.from_dict(
                name="Draft2020-12_MetaSchema",
                description="",
                schema=SPECIFICATIONS.contents(DRAFT202012_DIALECT_URI),
                tests=[
                    dict(
                        description=f"Validating metaschema against metaschema",
                        instance=SPECIFICATIONS.contents(
                            DRAFT202012_DIALECT_URI),
                    )
                ],
            )
        ],
        path=Path(__file__),
    )
