#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
from itertools import zip_longest
from typing import TYPE_CHECKING
import json
import platform
import sys
import traceback

from jsonschema.validators import validator_for

jsonschema_version = metadata.version("jsonschema")


def compare_versions(v1: str, v2: str) -> int:
    for p1, p2 in zip_longest(
        v1.split("."),
        v2.split("."),
        fillvalue="0",
    ):
        if p1.isdigit() and p2.isdigit():
            # compare integers
            p1, p2 = int(p1), int(p2)
            if p1 > p2:
                return 1
            elif p1 < p2:
                return -1
        # compare lexicographically
        elif p1 > p2:
            return 1
        elif p1 < p2:
            return -1
    # versions are equal
    return 0


use_referencing_library = compare_versions(jsonschema_version, "4.18.0") >= 0

if use_referencing_library:
    import referencing.jsonschema
else:
    from jsonschema.validators import RefResolver

if TYPE_CHECKING:
    import io

    from jsonschema.protocols import Validator


@dataclass
class Runner:
    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout
    _DefaultValidator: Validator | None = None
    _default_spec = None

    def run(self, stdin=sys.stdin):
        for line in stdin:
            each = json.loads(line)
            cmd = each.pop("cmd")
            response = getattr(self, f"cmd_{cmd}")(**each)
            self._stdout.write(f"{json.dumps(response)}\n")
            self._stdout.flush()

    def cmd_start(self, version):
        assert version == 1
        self._started = True
        return dict(
            version=1,
            implementation=dict(
                language="python",
                name="jsonschema",
                version=jsonschema_version,
                homepage="https://python-jsonschema.readthedocs.io/",
                documentation="https://python-jsonschema.readthedocs.io/",
                issues=(
                    "https://github.com/python-jsonschema/jsonschema/issues"
                ),
                source="https://github.com/python-jsonschema/jsonschema",
                dialects=[
                    "https://json-schema.org/draft/2020-12/schema",
                    "https://json-schema.org/draft/2019-09/schema",
                    "http://json-schema.org/draft-07/schema#",
                    "http://json-schema.org/draft-06/schema#",
                    "http://json-schema.org/draft-04/schema#",
                    "http://json-schema.org/draft-03/schema#",
                ],
                os=platform.system(),
                os_version=platform.release(),
                language_version=platform.python_version(),
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        self._DefaultValidator = validator_for({"$schema": dialect})
        if use_referencing_library:
            self._default_spec = referencing.jsonschema.specification_with(
                dialect,
            )
        return dict(ok=True)

    def cmd_run(self, case, seq):
        assert self._started, "Not started!"
        schema = case["schema"]
        try:
            Validator = validator_for(schema, self._DefaultValidator)
            assert (
                Validator is not None
            ), "No dialect sent and schema is missing $schema."

            if use_referencing_library:
                registry = referencing.Registry().with_contents(
                    case.get("registry", {}).items(),
                    default_specification=self._default_spec,
                )
                validator = Validator(schema, registry=registry)
            else:
                registry = case.get("registry", {})
                resolver = RefResolver.from_schema(schema, store=registry)
                validator = Validator(schema, resolver=resolver)

            results = [
                {"valid": validator.is_valid(test["instance"])}
                for test in case["tests"]
            ]
            return dict(seq=seq, results=results)
        except Exception:
            return dict(
                errored=True,
                seq=seq,
                context={"traceback": traceback.format_exc()},
            )

    def cmd_stop(self):
        assert self._started, "Not started!"
        sys.exit(0)


Runner().run()
