#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from importlib import metadata
import io
import json
import platform
import sys
import traceback

from jsonschema.exceptions import SchemaError
from jsonschema.protocols import Validator
from jsonschema.validators import validator_for
import referencing.jsonschema


@dataclass
class Runner:
    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout
    _DefaultValidator: Validator | None = None
    _default_spec: referencing.Specification | None = None

    def run(self, stdin=sys.stdin):
        for line in stdin:
            each = json.loads(line)
            cmd = each.pop("cmd")
            response = getattr(self, f"cmd_{cmd.replace('-', '_')}")(**each)
            self._stdout.write(f"{json.dumps(response)}\n")
            self._stdout.flush()

    def cmd_start(self, version):
        assert version == 2
        self._started = True
        return dict(
            ready=True,
            version=2,
            implementation=dict(
                language="python",
                name="jsonschema",
                version=metadata.version("jsonschema"),
                homepage="https://python-jsonschema.readthedocs.io/",
                issues=(
                    "https://github.com/python-jsonschema/jsonschema/issues"
                ),
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
        self._default_spec = referencing.jsonschema.specification_with(dialect)
        return dict(ok=True)

    def cmd_validate(self, case, seq):
        assert self._started, "Not started!"
        schema = case["schema"]
        try:
            Validator = validator_for(schema, default=self._DefaultValidator)
            assert (
                Validator is not None
            ), "No dialect sent and schema is missing $schema."

            registry = referencing.Registry().with_contents(
                case.get("registry", {}).items(),
                default_specification=self._default_spec,
            )
            validator = Validator(schema, registry=registry)

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

    def cmd_validate_schema(self, case, seq):
        results = []
        for test in case["tests"]:
            schema = test["instance"]
            Validator = validator_for(schema, default=self._DefaultValidator)
            try:
                Validator.check_schema(schema)
            except SchemaError:
                results.append(dict(valid=False))
            else:
                results.append(dict(valid=True))
        return dict(seq=seq, results=results)

    def cmd_stop(self):
        assert self._started, "Not started!"
        sys.exit(0)


Runner().run()
