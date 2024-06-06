"""
Validator registries, likely for eventual upstreaming into referencing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from attrs import evolve, field, frozen
from referencing.jsonschema import EMPTY_REGISTRY, Schema, SchemaRegistry

if TYPE_CHECKING:
    from referencing.jsonschema import SchemaResource
    from url import URL


E_co = TypeVar("E_co", bound=Exception, covariant=True)
ErrorsFor = Callable[[Any], Iterable[E_co]]
SchemaCompiler = Callable[[Schema, SchemaRegistry], ErrorsFor[E_co]]


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
    _registry: ValidatorRegistry[E_co] = field(alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> Validator[E_co]:
        return evolve(self, registry=resources @ self._registry)

    def is_valid(self, instance: Any):
        return next(iter(self.errors_for(instance)), None) is None

    def validated(self, instance: Any):
        exception = next(iter(self.errors_for(instance)), None)
        if exception is not None:
            raise exception
        return instance

    def invalidated(self, instance: Any):
        exception = next(iter(self.errors_for(instance)), None)
        if exception is None:
            raise UnexpectedlyValid(instance)
        return instance


@frozen
class ValidatorRegistry(Generic[E_co]):

    _compile: SchemaCompiler[E_co] = field(alias="compile")
    _registry: SchemaRegistry = field(default=EMPTY_REGISTRY, alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> ValidatorRegistry[E_co]:
        return evolve(self, registry=resources @ self._registry)

    def schema(self, uri: URL) -> Schema:
        """
        Return the schema identified by the given URI.
        """
        return self._registry.resolver().lookup(str(uri)).contents

    def for_uri(self, uri: URL) -> Validator[E_co]:
        """
        Return a `Validator` using the schema at the given URI.
        """
        return self.for_schema(self.schema(uri))

    def for_schema(self, schema: Schema) -> Validator[E_co]:
        """
        Return a `Validator` using the given schema.
        """
        errors_for: ErrorsFor[E_co] = self._compile(schema, self._registry)
        return Validator(errors_for=errors_for, registry=self)
