"""
Direct connectables do not really connect anywhere and just operate in-memory.
"""

from __future__ import annotations

from contextlib import nullcontext
from importlib import metadata
from typing import TYPE_CHECKING, Any, Generic
import pkgutil
import platform

from attrs import asdict, field, frozen, mutable
from referencing.jsonschema import EMPTY_REGISTRY
from url import URL

from bowtie import DOCS, HOMEPAGE, REPO
from bowtie._commands import CaseResult, Started, StartedDialect, TestResult
from bowtie._core import Dialect, ImplementationInfo, registry
from bowtie._registry import E_co, Invalid, SchemaCompiler, ValidatorRegistry

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from jsonschema import ValidationError
    from jsonschema.protocols import Validator
    from referencing.jsonschema import Schema, SchemaRegistry

    from bowtie._commands import Message
    from bowtie._connectables import ConnectableId


class NoDirectConnection(Exception):
    def __str__(self):
        return f"No direct connection can be made to {self.args[0]!r}."


def not_yet_connected(schema: Schema, registry: SchemaRegistry):
    def _not_yet_connected(instance: Any):
        raise RuntimeError("Not yet connected!")

    return _not_yet_connected


@mutable
class Unconnection(Generic[E_co]):

    _info: ImplementationInfo = field(repr=lambda i: i.id, alias="info")
    compiler_for: Callable[[Dialect], SchemaCompiler[E_co]] = field(
        repr=False,
        alias="compiler_for",
    )
    _implicit_dialect_response: StartedDialect = field(
        default=StartedDialect.OK,
        repr=False,
        alias="implicit_dialect_response",
    )

    _current_dialect: Dialect = Dialect.latest()
    _compile: SchemaCompiler[E_co] = not_yet_connected

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
                self._current_dialect = Dialect.by_uri()[URL.parse(uri)]
                self._compile = self.compiler_for(self._current_dialect)
                return asdict(self._implicit_dialect_response)
            case {"cmd": "run", "seq": seq, "case": case}:
                schema = case["schema"]
                registry = EMPTY_REGISTRY.with_contents(
                    case.get("registry", {}).items(),
                    default_specification=self._current_dialect.specification(),
                )
                validate = self._compile(schema, registry)
                results = [
                    TestResult(valid=validate(test["instance"]) is None)
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


def direct_implementation(
    implicit_dialect_response: StartedDialect = StartedDialect.OK,
    **kwargs: Any,
) -> Callable[
    [Callable[[Dialect], SchemaCompiler[E_co]]],
    Callable[[], Unconnection[E_co]],
]:
    def connect(
        fn: Callable[[Dialect], SchemaCompiler[E_co]],
    ) -> Callable[[], Unconnection[E_co]]:
        name = kwargs.pop("name", fn.__name__)
        if "version" not in kwargs:
            kwargs["version"] = metadata.version(name)
        info = ImplementationInfo(
            name=name,
            os=platform.system(),
            os_version=platform.release(),
            language_version=platform.python_version(),
            **kwargs,
        )
        return lambda: Unconnection(
            compiler_for=fn,
            info=info,
            implicit_dialect_response=implicit_dialect_response,
        )

    return connect


@direct_implementation(
    language="python",
    homepage=URL.parse("https://python-jsonschema.readthedocs.io/"),
    documentation=URL.parse("https://python-jsonschema.readthedocs.io/"),
    issues=URL.parse("https://github.com/python-jsonschema/jsonschema/issues"),
    source=URL.parse("https://github.com/python-jsonschema/jsonschema"),
    dialects=frozenset(
        [
            Dialect.by_short_name()["draft2020-12"],
            Dialect.by_short_name()["draft2019-09"],
            Dialect.by_short_name()["draft7"],
            Dialect.by_short_name()["draft6"],
            Dialect.by_short_name()["draft4"],
            Dialect.by_short_name()["draft3"],
        ],
    ),
)
def jsonschema(dialect: Dialect) -> SchemaCompiler[ValidationError]:
    from jsonschema.validators import (
        validator_for,  # type: ignore[reportUnknownVariableType]
    )

    # FIXME: python-jsonschema/jsonschema#1011
    def to_group(error: ValidationError) -> ValidationError | Invalid[Any]:
        """
        Upconvert a validation error to an exception group.
        """
        if error.context:  # FIXME: Throws away all the other attributes...
            return Invalid(
                error.message,
                [to_group(each) for each in error.context],
            )
        elif error.cause:
            return Invalid(error.message, [error.cause])
        return error

    def compile(
        schema: Schema,
        registry: SchemaRegistry,
    ) -> Callable[[Any], Invalid[ValidationError] | None]:
        DialectValidator: type[Validator] = validator_for(  # type: ignore[reportUnknownVariableType]
            schema,
            default=validator_for({"$schema": str(dialect.uri)}),
        )
        validator: Validator = DialectValidator(schema, registry=registry)  # type: ignore[reportUnknownVariableType]

        def validate(instance: Any) -> Invalid[Any] | None:
            errors = validator.iter_errors(instance)  # type: ignore[reportUnknownMemberType]
            exceptions: list[Exception] = [to_group(each) for each in errors]  # type: ignore[reportUnknownArgumentType]
            if exceptions:
                return Invalid("Not valid.", exceptions)

        return validate

    return compile


@direct_implementation(
    language="python",
    version=metadata.version("bowtie-json-schema"),
    homepage=HOMEPAGE,
    documentation=DOCS,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset(Dialect.known()),
)
def null(dialect: Dialect) -> SchemaCompiler[ValidationError]:
    return lambda _, __: lambda _: None


IMPLEMENTATIONS = {
    "python-jsonschema": jsonschema,
}


@frozen
class Direct(Generic[E_co]):
    """
    A direct connectable connects by simply importing some Python object.

    This is generally going to be suitable only to implementations written in
    Python or to a language where a wrapper (PyO3, CFFI, ...) can expose
    libraries written in the language directly to Python.

    This object represents only the lazy import.
    Connecting will lookup and call the object from the identified location.
    The return value should then be an object which makes use of a specific
    target implementation.

    Note that unlike when running implementations via containers, here we do
    *not* (cannot) restrict network access. Implementations making use of this
    functionaly should still ensure no networking takes place.
    """

    _connect: Callable[[], Unconnection[E_co]] = field(alias="connect")

    kind = "direct"

    @classmethod
    def from_id(cls, id: ConnectableId) -> Direct[Any]:
        if "." in id and ":" in id:
            connect = pkgutil.resolve_name(id)
        elif id == "null":
            return cls.null()
        else:
            connect = IMPLEMENTATIONS.get(id)
            if connect is None:
                raise NoDirectConnection(id)
        return cls(connect=connect)

    @classmethod
    def null(cls):
        """
        The null direct connectable considers all instances always valid.

        It can be useful e.g. for simply testing whether something is valid
        JSON, or for disabling validation where it otherwise would happen.
        """
        return cls(connect=null)

    def connect(
        self,
        **kwargs: Any,
    ) -> AbstractAsyncContextManager[Unconnection[E_co]]:
        return nullcontext(self._connect())

    def registry(self, **kwargs: Any) -> ValidatorRegistry[E_co]:
        if "registry" not in kwargs:
            kwargs["registry"] = registry()
        return ValidatorRegistry(
            compile=self._connect().compiler_for(Dialect.latest()),  # XXX
            **kwargs,
        )
