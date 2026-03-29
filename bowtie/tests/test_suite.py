import json

from bowtie._core import Dialect
from bowtie._suite import cases_from, dialect_supports_compatibility


def test_compatibility_filtering():
    draft7 = Dialect.by_short_name()["draft7"]
    draft2020 = Dialect.by_short_name()["draft2020-12"]

    assert dialect_supports_compatibility("7", draft7)
    assert dialect_supports_compatibility("<=2019", draft7)
    assert not dialect_supports_compatibility("=2020", draft7)
    assert dialect_supports_compatibility("=2020", draft2020)


def test_cases_from_v1_filters_and_rewrites(tmp_path):
    suite = tmp_path / "tests" / "v1" / "type.json"
    remotes = tmp_path / "remotes" / "v1"
    remotes.mkdir(parents=True)
    suite.parent.mkdir(parents=True)
    suite.write_text(
        json.dumps(
            [
                {
                    "description": "draft 7 and up",
                    "compatibility": "7",
                    "schema": {
                        "$schema": "https://json-schema.org/v1",
                        "type": "integer",
                    },
                    "tests": [
                        {
                            "description": "integer is valid",
                            "data": 1,
                            "valid": True,
                        },
                    ],
                },
                {
                    "description": "2020 only",
                    "compatibility": "=2020",
                    "schema": {
                        "$schema": "https://json-schema.org/v1",
                        "type": "string",
                    },
                    "tests": [
                        {
                            "description": "string is valid",
                            "data": "x",
                            "valid": True,
                        },
                    ],
                },
            ],
        ),
    )

    cases = list(
        cases_from(
            paths=[suite],
            remotes=remotes,
            dialect=Dialect.by_short_name()["draft7"],
            suite_version="v1",
        ),
    )

    assert [case.description for case in cases] == ["draft 7 and up"]
    assert cases[0].schema["$schema"] == str(
        Dialect.by_short_name()["draft7"].uri
    )
    assert cases[0].tests[0].instance == 1
