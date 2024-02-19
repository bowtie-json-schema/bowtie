"""
In-process 'clients' for the implementations we can talk to directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import traceback

from attrs import asdict, field, frozen
from referencing.jsonschema import SchemaRegistry
from url import URL

from bowtie._commands import (
    CaseErrored,
    CaseResult,
    Started,
    StartedDialect,
    TestResult,
)
from bowtie._core import Dialect, ImplementationInfo

if TYPE_CHECKING:
    from bowtie._commands import Message


@frozen
class Unconnection:
    """
    The non-connection connection to an imported implementation.
    """

    info: ImplementationInfo
    validate: ImplementationInfo

    _dialect: Dialect = field(init=False)

    @classmethod
    def jsonschema(cls):
        """
        An unconnection the `jsonschema` package.
        """
        from jsonschema.validators import validator_for

        info = ImplementationInfo(
            image=None,
            name="jsonschema",
            language="python",
            homepage=URL.parse(
                "https://github.com/python-jsonschema/jsonschema",
            ),
            source=URL.parse(
                "https://github.com/python-jsonschema/jsonschema",
            ),
            issues=URL.parse(
                "https://github.com/python-jsonschema/jsonschema/issues",
            ),
            dialects=Dialect.known(),
        )

        def validate(dialect, schema, instances, registry):
            DefaultValidator = validator_for({"$schema": str(dialect.uri)})
            Validator = validator_for(schema, DefaultValidator)
            validator = Validator(schema, registry=registry)
            return [validator.is_valid(instance) for instance in instances]

        return cls(info=info, validate=validate)

    async def request(self, message: Message) -> Message | None:
        match message:
            case {"cmd": "start", "version": 1}:
                response = asdict(
                    Started(
                        version=1,
                        implementation=self.info.serializable(),
                    ),
                )
            case {"cmd": "dialect", "dialect": uri}:
                object.__setattr__(self, "_dialect", Dialect.from_str(uri))
                response = asdict(StartedDialect.OK)
            case {
                "cmd": "run",
                "seq": seq,
                "case": {
                    "schema": schema,
                    "tests": tests,
                    **kwargs,
                },
            }:
                registry = SchemaRegistry().with_contents(
                    kwargs.get("registry", {}).items(),
                    default_specification=self._dialect.specification(),
                )

                try:
                    result = CaseResult(
                        results=[
                            TestResult(valid=valid)
                            for valid in self.validate(
                                dialect=self._dialect,
                                schema=schema,
                                instances=[test["instance"] for test in tests],
                                registry=registry,
                            )
                        ],
                    )
                except Exception:  # noqa: BLE001
                    result = CaseErrored(
                        context=dict(traceback=traceback.format_exc()),
                    )
                response = dict(seq=seq, **asdict(result))
            case _:
                raise RuntimeError(f"Unknown command {message}")

        return response

    async def poison(self, message: Message):
        pass
