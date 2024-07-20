from jsonschema_specifications import REGISTRY as SPECIFICATIONS

DRAFT202012_DIALECT_URI = "https://json-schema.org/draft/2020-12/schema"


def get_benchmark():
    return dict(
        name="Draft2020-12_MetaSchema",
        description=(
            "A benchmark for validation of the 2020-12 dialect's metaschema"
        ),
        schema=SPECIFICATIONS.contents(DRAFT202012_DIALECT_URI),
        tests=[
            dict(
                description=f"Validating metaschema against metaschema",
                instance=SPECIFICATIONS.contents(DRAFT202012_DIALECT_URI),
            )
        ],
    )
