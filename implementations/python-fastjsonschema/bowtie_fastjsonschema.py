#!/usr/bin/env python3
from dataclasses import dataclass
from importlib import metadata
import io
import json
import platform
import sys
import traceback

import fastjsonschema


@dataclass
class Runner:
    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout

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
                name="fastjsonschema",
                version=metadata.version("fastjsonschema"),
                homepage="https://horejsek.github.io/python-fastjsonschema/",
                documentation=(
                    "https://horejsek.github.io/python-fastjsonschema/"
                ),
                issues=(
                    "https://github.com/horejsek/python-fastjsonschema/issues"
                ),
                source="https://github.com/horejsek/python-fastjsonschema",
                dialects=[
                    "http://json-schema.org/draft-07/schema#",
                    "http://json-schema.org/draft-06/schema#",
                    "http://json-schema.org/draft-04/schema#",
                ],
                os=platform.system(),
                os_version=platform.release(),
                language_version=platform.python_version(),
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        return dict(ok=False)

    def cmd_run(self, case, seq):
        assert self._started, "Not started!"
        schema = case["schema"]
        try:
            # The registry parameter isn't used here when building cases.
            # Unless I'm missing it, it doesn't seem there's a way to register
            # schemas with fastjsonschema. It seems to use RefResolver-like
            # objects, but they're not exposed to end-user APIs like compile.

            validate = fastjsonschema.compile(schema)

            results = []

            for test in case["tests"]:
                try:
                    validate(test["instance"])
                except fastjsonschema.JsonSchemaException:
                    results.append({"valid": False})
                else:
                    results.append({"valid": True})

            return dict(seq=seq, results=results)
        except:  # noqa: E722  fastjsonschema can raise e.g. IndentationError
            return dict(
                errored=True,
                seq=seq,
                context={"traceback": traceback.format_exc()},
            )

    def cmd_stop(self):
        assert self._started, "Not started!"
        sys.exit(0)


Runner().run()
