"""
A collection of small mini-fake implementations with deterministic behavior.

Useful for testing Bowtie's own internal behavior.
"""

from url import URL

from bowtie import HOMEPAGE, REPO
from bowtie._commands import StartedDialect
from bowtie._core import Dialect, Link
from bowtie._direct_connectable import DirectImplementation, null

ARBITRARILY_INVALID = ExceptionGroup("Not valid!", [ZeroDivisionError()])


def fake(**kwargs):
    return DirectImplementation.from_callable(
        **{
            "homepage": HOMEPAGE,
            "source": REPO,
            "issues": REPO / "issues",
            "version": "v1.0.0",
            "dialects": frozenset(Dialect.known()),
            **kwargs,
        },
    )


@fake()
def always_invalid(dialect: Dialect):
    """
    Always considers any instance invalid.

    For the inverse, see `Direct.null`.
    """
    return lambda schema, registry: lambda instance: ARBITRARILY_INVALID


@fake()
def always_wrong(dialect: Dialect):
    """
    Tries (naively) to always get the absolute wrong answer.
    """
    return lambda schema, registry: lambda instance: (
        naively_incorrect(schema, registry, instance)
    )


def only_supports(dialect: str):
    """
    Claims to only support the dialect provided in its (sole) parameter.

    Use this by passing a connectable parameter, e.g. via
    ``direct:miniatures:only_supports,dialect=draft4``.

    The validity result of instances should not be relied on.
    """
    return fake(
        name="only_supports",
        dialects=frozenset([Dialect.by_short_name()[dialect]]),
    )(null)()


@fake()
def incorrectly_claims_draft7(dialect: Dialect):
    """
    Claims to support Draft 7 but returns all wrong results for it.

    Otherwise attempts to crudely pass the smoke test.
    """
    if dialect == dialect.by_short_name()["draft7"]:
        return lambda schema, registry: lambda instance: (
            naively_correct(schema, registry)(instance)
            if registry
            else naively_incorrect(schema, registry, instance)
        )
    return naively_correct


@fake(language="javascript")
def fake_javascript(dialect: Dialect):
    """
    Claims to be written in Javascript.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: None


@fake()
def passes_smoke(dialect: Dialect):
    """
    An implementation which crudely passes `bowtie smoke`.
    """
    return naively_correct


@fake()
def no_registry_support(dialect: Dialect):
    """
    An implementation which tries really hard but fails at referecing.
    """
    return lambda schema, registry: (
        naively_correct(schema, registry)
        if not registry
        else lambda instance: None
    )


@fake(implicit_dialect_response=StartedDialect(ok=False))
def no_implicit_dialect_support(dialect: Dialect):
    """
    An implementation which does not support implicit dialects in schemas.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: None


@fake(
    homepage=URL.parse("urn:example"),
    issues=URL.parse("urn:example"),
    source=URL.parse("urn:example"),
    dialects=frozenset([Dialect.by_short_name()["draft7"]]),
    links=[
        Link(description="foo", url=URL.parse("urn:example:foo")),
        Link(description="bar", url=URL.parse("urn:example:bar")),
    ],
)
def links(dialect: Dialect):
    """
    An implementation which declares some additional links.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: None


def foo_v1(dialect: Dialect):
    """
    Claims to be in version 1.0 and changes its behaviour based on the dialect.

    The validity result of instances should not be relied on.
    """
    if dialect == Dialect.by_short_name()["draft2020-12"]:
        return lambda schema, registry: lambda instance: ARBITRARILY_INVALID
    elif dialect == Dialect.by_short_name()["draft2019-09"]:
        return lambda schema, registry: lambda instance: None

    return lambda schema, registry: lambda instance: None


def foo_v2(dialect: Dialect):
    """
    Claims to be in version 2.0 and changes its behaviour based on the dialect.

    The validity result of instances should not be relied on.
    """
    if dialect == Dialect.by_short_name()["draft2020-12"]:
        return lambda schema, registry: lambda instance: None
    elif dialect == Dialect.by_short_name()["draft2019-09"]:
        return lambda schema, registry: lambda instance: ARBITRARILY_INVALID

    return lambda schema, registry: lambda instance: None


def by_version_and_dialect(version: str, dialect: str):
    """
    An implementation whose behaviour changes based on its version and dialect.

    Use this by passing a connectable parameter, e.g. via
    ``direct:miniatures:by_version_and_dialect,version=1.0,dialect=draft2020-12``.

    The validity result of instances should not be relied on.
    """
    if version == "1.0":
        return fake(
            name="foo",
            version=version,
            dialects=frozenset([Dialect.by_short_name()[dialect]]),
        )(foo_v1)()
    elif version == "2.0":
        return fake(
            name="foo",
            version=version,
            dialects=frozenset([Dialect.by_short_name()[dialect]]),
        )(foo_v2)()


def naively_correct(schema, registry):
    """
    The naivest implementation which tries to pass a smoke test.
    """
    ref = schema.get("$ref")
    if ref is not None:
        schema = registry.contents(ref)

    def validate(instance):
        if "not" in schema or "disallow" in schema:
            return ARBITRARILY_INVALID

        pytype = dict(string=str).get(schema.get("type"))
        if pytype is not None and not isinstance(instance, pytype):
            return ARBITRARILY_INVALID

    return validate


def naively_incorrect(schema, registry, instance):
    """
    Naively returns the wrong answer.
    """
    result = naively_correct(schema, registry)(instance)
    return ARBITRARILY_INVALID if result is None else None
