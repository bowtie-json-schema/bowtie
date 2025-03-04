"""
Direct connectables do not really connect anywhere and just operate in-memory.
"""

from __future__ import annotations

from contextlib import nullcontext
from importlib import metadata
from typing import TYPE_CHECKING, Any, Never
import pkgutil
import platform

from attrs import asdict, field, frozen, mutable
from referencing.jsonschema import EMPTY_REGISTRY
from url import URL

from bowtie import DOCS, HOMEPAGE, REPO
from bowtie._commands import CaseResult, Started, StartedDialect, TestResult
from bowtie._core import Dialect, ImplementationInfo, registry
from bowtie._registry import Invalid, SchemaCompiler, ValidatorRegistry
from bowtie.exceptions import CannotConnect

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from jsonschema import ValidationError
    from jsonschema.protocols import Validator
    from referencing.jsonschema import Schema, SchemaRegistry

    from bowtie._commands import Message
    from bowtie._connectables import ConnectableId


def not_yet_connected(schema: Schema, registry: SchemaRegistry):
    def _not_yet_connected(instance: Any):
        raise RuntimeError("Not yet connected!")

    return _not_yet_connected


@mutable
class Unconnection[E: Exception]:

    _info: ImplementationInfo = field(repr=lambda i: i.id, alias="info")
    compiler_for: Callable[[Dialect], SchemaCompiler[E]] = field(
        repr=False,
        alias="compiler_for",
    )
    _implicit_dialect_response: StartedDialect = field(
        default=StartedDialect.OK,
        repr=False,
        alias="implicit_dialect_response",
    )

    _current_dialect: Dialect = Dialect.latest()
    _compile: SchemaCompiler[E] = not_yet_connected

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
                self._current_dialect = Dialect.from_str(uri)
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


@frozen
class DirectImplementation[E: Exception]:

    _compiler_for: Callable[[Dialect], SchemaCompiler[E]]
    _info: ImplementationInfo
    _implicit_dialect_response: StartedDialect

    def __init__(
        self,
        compiler_for: Callable[[Dialect], SchemaCompiler[E]],
        implicit_dialect_response: StartedDialect = StartedDialect.OK,
        **kwargs: Any,
    ):
        object.__setattr__(self, "_compiler_for", compiler_for)
        object.__setattr__(
            self,
            "_implicit_dialect_response",
            implicit_dialect_response,
        )

        name = kwargs.pop("name", compiler_for.__name__)
        if "version" not in kwargs:
            kwargs["version"] = metadata.version(name)

        for key, default in [
            ("language_version", platform.python_version()),
            ("os", platform.system()),
            ("os_version", platform.release()),
        ]:
            kwargs.setdefault(key, default)

        info = ImplementationInfo(name, **kwargs)
        object.__setattr__(self, "_info", info)

    def __call__(self):
        return Unconnection(
            compiler_for=self._compiler_for,
            info=self._info,
            implicit_dialect_response=self._implicit_dialect_response,
        )

    @classmethod
    def from_callable(
        cls,
        language: str = "python",
        **kwargs: Any,
    ):
        def decorator(fn: Callable[[Dialect], SchemaCompiler[E]]):
            return lambda: cls(compiler_for=fn, language=language, **kwargs)

        return decorator


@DirectImplementation.from_callable(
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


# pyright (at least 1.1.372) seems unable to see through this type if we try to
# define it via DirectImplementation.from_callable. But I guess that's fine...
def null(dialect: Dialect) -> SchemaCompiler[Never]:
    return lambda _, __: lambda _: None


NULL = DirectImplementation(
    compiler_for=null,
    language="python",
    version=metadata.version("bowtie-json-schema"),
    homepage=HOMEPAGE,
    documentation=DOCS,
    issues=REPO / "issues",
    source=REPO,
    dialects=frozenset(Dialect.known()),
)


IMPLEMENTATIONS: dict[str, Callable[..., Callable[[], Unconnection[Any]]]] = {
    "python-jsonschema": jsonschema,  # type: ignore[reportAssignmentType]  # pyright seems confused.
}


@frozen(kw_only=True)
class Direct[E: Exception]:
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

    _wraps: Callable[[], Unconnection[E]] = field(alias="wraps")

    kind = "direct"

    @classmethod
    def from_id(cls, id: ConnectableId, **params: Any) -> Direct[Any]:
        if id == "null":
            return cls.null()

        wrapper = IMPLEMENTATIONS.get(id)
        if wrapper is not None:
            return cls(wraps=wrapper(**params))

        try:
            wrapper = pkgutil.resolve_name(id)
        except (ModuleNotFoundError, ValueError) as err:
            raise CannotConnect(kind=cls.kind, id=id) from err
        else:
            # pkgutil.resolve_name supports foo.bar.baz in addition to
            # foo.bar:baz. The latter has minor performance benefits, and in
            # addition, in our case it's easy to accidentally forget
            # *parameters* that foo.bar.baz takes, so here we disallow any
            # import string which does not use the foo.bar:baz syntax even
            # though it has succeeded.
            if ":" not in id:
                corrected = ":".join(id.rsplit(".", 1))
                raise CannotConnect(
                    kind=cls.kind,
                    id=id,
                    hint=(
                        f"{id!r} is not a known 'named' direct connectable "
                        "and instead appears to describe an object to "
                        "import, but it is not well formed. "
                        f"You may mean to use {corrected!r}."
                    ),
                )
        return cls(wraps=wrapper(**params))

    @classmethod
    def null(cls):
        """
        The null direct connectable considers all instances always valid.

        It can be useful e.g. for simply testing whether something is valid
        JSON, or for disabling validation where it otherwise would happen.
        """
        return cls(wraps=NULL)  # type: ignore[reportArgumentType]

    def connect(
        self,
        **kwargs: Any,
    ) -> AbstractAsyncContextManager[Unconnection[E]]:
        return nullcontext(self._wraps())

    def registry(self, **kwargs: Any) -> ValidatorRegistry[E]:
        if "registry" not in kwargs:
            kwargs["registry"] = registry()
        return ValidatorRegistry(
            compile=self._wraps().compiler_for(Dialect.latest()),  # XXX
            **kwargs,
        )
