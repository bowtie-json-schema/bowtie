#!/usr/bin/env python3
from dataclasses import dataclass
from importlib import metadata
import io
import json
import platform
import sys
import traceback

import jschon

SUITE_REMOTES_BASE_URI = jschon.URI("http://localhost:1234/")


class InMemorySource(jschon.catalog.Source):
    # From what I can tell this seems to be the way to get jschon to look up
    # schemas. Just using catalog.add_schema doesn't seem to do it.

    def __init__(self, base_url, registry, **kwargs):
        # It probably doesn't matter here, but it seems super() isn't the right
        # thing to use, as jschon.catalog.Source.__init__ seems to have a
        # different signature than its subclasses from the examples I see.
        jschon.catalog.Source.__init__(self, **kwargs)
        self.base_url = base_url
        self.registry = registry

    def __call__(self, relative_path):
        url = str(jschon.URI(relative_path).resolve(self.base_url))
        return self.registry[url]


VOCABULARIES = {
    jschon.URI("https://json-schema.org/draft/2020-12/schema"): "2020-12",
    jschon.URI("https://json-schema.org/draft/2019-09/schema"): "2019-09",
}


@dataclass
class Runner:
    _started: bool = False
    _stdout: io.TextIOWrapper = sys.stdout

    _metaschema_uri = None

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
                name="jschon",
                version=metadata.version("jschon"),
                homepage="https://jschon.readthedocs.io/",
                documentation="https://jschon.readthedocs.io/",
                issues="https://github.com/marksparkza/jschon/issues",
                source="https://github.com/marksparkza/jschon",
                dialects=[
                    "https://json-schema.org/draft/2020-12/schema",
                    "https://json-schema.org/draft/2019-09/schema",
                ],
                os=platform.system(),
                os_version=platform.release(),
                language_version=platform.python_version(),
            ),
        )

    def cmd_dialect(self, dialect):
        assert self._started, "Not started!"
        self._metaschema_uri = jschon.URI(dialect)
        return dict(ok=self._metaschema_uri in VOCABULARIES)

    def cmd_run(self, case, seq):
        assert self._started, "Not started!"
        try:
            catalog = jschon.create_catalog(
                VOCABULARIES[self._metaschema_uri],
                name=f"catalog-{seq}",
            )
            catalog.add_uri_source(
                SUITE_REMOTES_BASE_URI,
                InMemorySource(
                    base_url=SUITE_REMOTES_BASE_URI,
                    registry=case.get("registry", {}),
                ),
            )

            schema = jschon.JSONSchema(
                case["schema"],
                catalog=catalog,
                metaschema_uri=self._metaschema_uri,
            )

            results = []

            for test in case["tests"]:
                result = schema.evaluate(jschon.JSON(test["instance"]))
                results.append({"valid": result.valid})

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
