"""
Validator registries, likely for eventual upstreaming into referencing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any

from attrs import evolve, field, frozen
from referencing.jsonschema import EMPTY_REGISTRY

if TYPE_CHECKING:
    from referencing.jsonschema import Schema, SchemaRegistry, SchemaResource


ErrorsFor = Callable[[Any], Iterable[Exception]]


@frozen
class Validator:
    """
    A compiled schema, ready to validate instances.
    """

    errors_for: ErrorsFor
    _registry: ValidatorRegistry = field(alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> Validator:
        return evolve(self, registry=resources @ self._registry)

    def validate(self, instance: Any):
        exception = next(iter(self.errors_for(instance)), None)
        if exception is not None:
            raise exception


@frozen
class ValidatorRegistry:

    _compile: Callable[[Schema, SchemaRegistry], ErrorsFor] = field(
        alias="compile",
    )
    _registry: SchemaRegistry = field(default=EMPTY_REGISTRY, alias="registry")

    def __rmatmul__(
        self,
        resources: SchemaResource | Iterable[SchemaResource],
    ) -> ValidatorRegistry:
        return evolve(self, registry=resources @ self._registry)

    @classmethod
    def jsonschema(cls, **kwargs: Any) -> ValidatorRegistry:
        """
        A registry which uses the `jsonschema` module to do validation.
        """
        from jsonschema.validators import (
            validator_for,  # type: ignore[reportUnknownVariableType]
        )

        def compile(schema: Schema, registry: SchemaRegistry) -> ErrorsFor:
            _Validator = validator_for(schema)  # type: ignore[reportUnknownVariableType]
            return _Validator(schema, registry=registry).iter_errors  # type: ignore[reportUnknownVariableType]

        return cls(compile=compile, **kwargs)

    def schema(self, uri: str) -> Schema:
        """
        Return the schema identified by the given URI.
        """
        return self._registry.contents(uri)

    def for_uri(self, uri: str) -> Validator:
        """
        Return a `Validator` using the schema at the given URI.
        """
        return self.for_schema(self.schema(uri))

    def for_schema(self, schema: Schema) -> Validator:
        """
        Return a `Validator` using the given schema.
        """
        errors_for: ErrorsFor = self._compile(schema, self._registry)
        return Validator(errors_for=errors_for, registry=self)
