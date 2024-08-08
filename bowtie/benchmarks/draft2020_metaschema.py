from pathlib import Path

from jsonschema_specifications import REGISTRY as SPECIFICATIONS
from url.url import URL

from bowtie._benchmarks import BenchmarkGroup
from bowtie._core import Dialect

DRAFT202012_DIALECT_URI = "https://json-schema.org/draft/2020-12/schema"


def get_benchmark():
    return BenchmarkGroup.from_dict(
        data=dict(
            name="Draft2020-12_MetaSchema",
            benchmark_type="default",
            dialects_supported=[
                Dialect.from_str(
                    "https://json-schema.org/draft/2020-12/schema",
                ),
            ],
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
        ),
        uri=URL.parse(Path(__file__).absolute().as_uri()),
    )
