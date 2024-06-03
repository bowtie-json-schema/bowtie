"""
Direct connectables do not really connect anywhere and just operate in-memory.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from importlib import metadata
from typing import TYPE_CHECKING, Any, Generic
import platform

from attrs import asdict, field, frozen, mutable
from referencing.jsonschema import EMPTY_REGISTRY
from url import URL

from bowtie._commands import CaseResult, Started, StartedDialect, TestResult
from bowtie._core import Connection, Dialect, ImplementationInfo
from bowtie._registry import E_co, SchemaCompiler

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Callable, Iterable

    from jsonschema import ValidationError
    from jsonschema.protocols import Validator
    from referencing.jsonschema import Schema, SchemaRegistry

    from bowtie._commands import Message
    from bowtie._connectables import ConnectableId


class NoDirectConnection(Exception):
    @classmethod
    def check(cls, _: Any, __: Any, id: ConnectableId):
        if id not in IMPLEMENTATIONS:
            raise cls(id)

    def __str__(self):
        return f"No direct connection can be made to {self.args[0]!r}."


def not_yet_connected(schema: Schema, registry: SchemaRegistry):
    def _not_yet_connected(instance: Any):
        raise RuntimeError("Not yet connected!")

    return _not_yet_connected


@mutable
class Unconnection(Generic[E_co]):

    _info: ImplementationInfo = field(
        repr=lambda value: f"{value.language}-{value.name}",
        alias="info",
    )
    _compile: Callable[[Dialect], SchemaCompiler[E_co]] = field(
        repr=False,
        alias="compile",
    )
    _for_current_dialect: SchemaCompiler[E_co] = not_yet_connected

    async def request(self, message: Message) -> Message:
        """
        Unpack the request and call our implementation.

        Call us, we always respond (so we never return ``None``).
        """
        match message:  # FIXME: Should request take Commands?
            case {"cmd": "start", "version": 1}:
                started = Started(
                    implementation=self._info.serializable(),  # FIXME
                    version=1,
                )
                return asdict(started)
            case {"cmd": "dialect", "dialect": uri}:
                dialect = Dialect.by_uri()[URL.parse(uri)]
                self._for_current_dialect = self._compile(dialect)
                return asdict(StartedDialect.OK)
            case {"cmd": "run", "seq": seq, "case": case}:
                errors_for = self._for_current_dialect(
                    case["schema"],
                    case.get("registry", EMPTY_REGISTRY),
                )
                results = [
                    TestResult(
                        valid=(
                            next(iter(errors_for(test["instance"])), None)
                            is None
                        ),
                    )
                    for test in case["tests"]
                ]
                return {  # FIXME: Bleh this is not SeqResult
                    "seq": seq,
                    **CaseResult(results=results).serializable(),
                }
            case {"cmd": "stop"}:
                return {}
            case _:
                raise RuntimeError(f"Unknown message: {message!r}")

    async def poison(self, message: Message) -> None:
        """
        Do nothing.
        """


def jsonschema() -> Unconnection[ValidationError]:
    """
    An (un)connection to the python-jsonschema implementation.
    """
    dialects = Dialect.by_alias()

    from jsonschema.validators import (
        validator_for,  # type: ignore[reportUnknownVariableType]
    )

    def compile(dialect: Dialect) -> SchemaCompiler[ValidationError]:
        def _compile(
            schema: Schema,
            registry: SchemaRegistry,
        ) -> Callable[[Any], Iterable[ValidationError]]:
            DialectValidator: type[Validator] = validator_for(  # type: ignore[reportUnknownVariableType]
                schema,
                default=validator_for({"$schema": str(dialect.uri)}),
            )
            validator: Validator = DialectValidator(schema, registry=registry)  # type: ignore[reportUnknownVariableType]
            return validator.iter_errors  # type: ignore[reportUnknownMemberType]

        return _compile

    return Unconnection(
        info=ImplementationInfo(
            language="python",
            name="jsonschema",
            version=metadata.version("jsonschema"),
            homepage=URL.parse(
                "https://python-jsonschema.readthedocs.io/",
            ),
            documentation=URL.parse(
                "https://python-jsonschema.readthedocs.io/",
            ),
            issues=URL.parse(
                "https://github.com/python-jsonschema/jsonschema/issues",
            ),
            source=URL.parse(
                "https://github.com/python-jsonschema/jsonschema",
            ),
            dialects=frozenset(
                [
                    dialects["2020"],
                    dialects["2019"],
                    dialects["7"],
                    dialects["6"],
                    dialects["4"],
                    dialects["3"],
                ],
            ),
            os=platform.system(),
            os_version=platform.release(),
            language_version=platform.python_version(),
        ),
        compile=compile,
    )


IMPLEMENTATIONS = {
    "python-jsonschema": jsonschema,
}


@frozen
class Direct:
    """
    A direct connectable connects by simply importing some Python object.

    This is generally going to be suitable only to implementations written in
    Python or to a language where a wrapper (PyO3, CFFI, ...) can expose
    libraries written in the language directly to Python.

    This object represents only the lazy import.
    Connecting will lookup and call the object from the identified location.
    The return value should then be an object which makes use of a specific
    target implementation.
    """

    _id: ConnectableId = field(alias="id", validator=NoDirectConnection.check)

    connector = "direct"

    @asynccontextmanager
    async def connect(self, **kwargs: Any) -> AsyncIterator[Connection]:
        yield IMPLEMENTATIONS[self._id]()
