"""
Validator registries, likely for eventual upstreaming into referencing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from attrs import evolve, field, frozen
from referencing.jsonschema import EMPTY_REGISTRY, Schema, SchemaRegistry

if TYPE_CHECKING:
    from jsonschema.exceptions import ValidationError
    from referencing.jsonschema import SchemaResource


E_co = TypeVar("E_co", bound=Exception, covariant=True)
ErrorsFor = Callable[[Any], Iterable[E_co]]
SchemaCompiler = Callable[
    [Schema, SchemaRegistry],
    Callable[[Any], ErrorsFor[E_co]],
]


class UnexpectedlyValid(Exception):
    """
    An instance which was expected to be invalid just isn't.
    """


@frozen
class Validator(Generic[E_co]):
    """
    A compiled schema, ready to validate instances.
    """

    errors_for: ErrorsFor[E_co]
    _raises: tuple[type[E_co], ...] = field(alias="raises")
    _registry: ValidatorRegistry[E_co] = field(alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> Validator[E_co]:
        return evolve(self, registry=resources @ self._registry)

    def validate(self, instance: Any):
        exception = next(iter(self.errors_for(instance)), None)
        if exception is not None:
            raise exception

    def invalidate(self, instance: Any):
        exception = next(iter(self.errors_for(instance)), None)
        if not isinstance(exception, self._raises):
            raise UnexpectedlyValid(instance)


@frozen
class ValidatorRegistry(Generic[E_co]):

    _compile: Callable[[Schema, SchemaRegistry], ErrorsFor[E_co]] = field(
        alias="compile",
    )
    _raises: tuple[type[E_co], ...] = field(  # type: ignore[reportAssignmentType]  ?!?
        default=(Exception,),
        alias="raises",
    )
    _registry: SchemaRegistry = field(default=EMPTY_REGISTRY, alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> ValidatorRegistry[E_co]:
        return evolve(self, registry=resources @ self._registry)

    @classmethod
    def jsonschema(cls, **kwargs: Any) -> ValidatorRegistry[ValidationError]:
        """
        A registry which uses the `jsonschema` module to do validation.
        """
        from jsonschema.exceptions import ValidationError
        from jsonschema.validators import (
            validator_for,  # type: ignore[reportUnknownVariableType]
        )

        def compile(
            schema: Schema,
            registry: SchemaRegistry,
        ) -> ErrorsFor[ValidationError]:
            _Validator = validator_for(schema)  # type: ignore[reportUnknownVariableType]
            return _Validator(schema, registry=registry).iter_errors  # type: ignore[reportUnknownVariableType]

        return cls(compile=compile, raises=(ValidationError,), **kwargs)  # type: ignore[reportAssignmentType]  ?!?

    def schema(self, uri: str) -> Schema:
        """
        Return the schema identified by the given URI.
        """
        return self._registry.contents(uri)

    def for_uri(self, uri: str) -> Validator[E_co]:
        """
        Return a `Validator` using the schema at the given URI.
        """
        return self.for_schema(self.schema(uri))

    def for_schema(self, schema: Schema) -> Validator[E_co]:
        """
        Return a `Validator` using the given schema.
        """
        errors_for: ErrorsFor[E_co] = self._compile(schema, self._registry)
        return Validator(
            errors_for=errors_for,
            raises=self._raises,
            registry=self,
        )
