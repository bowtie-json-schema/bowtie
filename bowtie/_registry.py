"""
Validator registries, likely for eventual upstreaming into referencing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

from attrs import evolve, field, frozen
from referencing.jsonschema import EMPTY_REGISTRY, Schema, SchemaRegistry

if TYPE_CHECKING:
    from referencing.jsonschema import SchemaResource
    from url import URL


type Validate[E: Exception] = Callable[[Any], ExceptionGroup[E] | None]
type SchemaCompiler[E: Exception] = Callable[
    [Schema, SchemaRegistry],
    Validate[E],
]


class Invalid[E: Exception](ExceptionGroup[E]):
    """
    An instance is not valid under a schema.
    """

    # TODO: Don't require a message? Or what should the general message be?
    #       What about lazy error production? Can we delay asking for all
    #           errors here?


class UnexpectedlyValid(Exception):
    """
    An instance which was expected to be invalid just isn't.
    """


@frozen
class Validator[E: Exception]:
    """
    A compiled schema, ready to validate instances.
    """

    validate: Validate[E]
    _registry: ValidatorRegistry[E] = field(alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> Validator[E]:
        return evolve(self, registry=resources @ self._registry)

    def is_valid(self, instance: Any):
        return self.validate(instance) is None

    def validated(self, instance: Any):
        exception = self.validate(instance)
        if exception is not None:
            raise exception
        return instance

    def invalidated(self, instance: Any):
        if self.is_valid(instance):
            raise UnexpectedlyValid(instance)
        return instance


@frozen
class ValidatorRegistry[E: Exception]:

    _compile: SchemaCompiler[E] = field(alias="compile")
    _registry: SchemaRegistry = field(default=EMPTY_REGISTRY, alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> ValidatorRegistry[E]:
        return evolve(self, registry=resources @ self._registry)

    def schema(self, uri: URL) -> Schema:
        """
        Return the schema identified by the given URI.
        """
        return self._registry.resolver().lookup(str(uri)).contents

    def for_uri(self, uri: URL) -> Validator[E]:
        """
        Return a `Validator` using the schema at the given URI.
        """
        return self.for_schema(self.schema(uri))

    def for_schema(self, schema: Schema) -> Validator[E]:
        """
        Return a `Validator` using the given schema.
        """
        validate: Validate[E] = self._compile(schema, self._registry)
        return Validator(validate=validate, registry=self)
