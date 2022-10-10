#!/usr/bin/env python3
from dataclasses import dataclass
from importlib import metadata
import io
import json
import sys
import traceback

from jsonschema.protocols import Validator
from jsonschema.validators import RefResolver, validator_for


@dataclass
class Runner:

    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout
    _DefaultValidator: Validator | None = None

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
            ready=True,
            version=1,
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
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        self._DefaultValidator = validator_for({"$schema": dialect})
        return dict(ok=True)

    def cmd_run(self, case, seq):
        assert self._started, "Not started!"
        schema = case["schema"]
        try:
            Validator = validator_for(schema, self._DefaultValidator)
            assert (
                Validator is not None
            ), "No dialect sent and schema is missing $schema."

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
