"""
A collection of small mini-fake implementations with deterministic behavior.

Useful for testing Bowtie's own internal behavior.
"""

from url import URL

from bowtie import HOMEPAGE, REPO
from bowtie._commands import StartedDialect
from bowtie._core import Dialect, Link
from bowtie._direct_connectable import direct_implementation

ARBITRARILY_INVALID = ExceptionGroup("Not valid!", [ZeroDivisionError()])


def fake(**kwargs):
    return direct_implementation(
        **{
            "language": "python",
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


@fake(dialects=frozenset([Dialect.by_short_name()["draft3"]]))
def only_draft3(dialect: Dialect):
    """
    Claims to only support Draft 3.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: None


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
    return lambda schema, registry: lambda instance: (  # naively...
        None if "not" not in schema else ARBITRARILY_INVALID
    )


@fake(implicit_dialect_response=StartedDialect(ok=False))
def no_implicit_dialect_support(dialect: Dialect):
    """
    An implementation which crudely passes `bowtie smoke`.

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

@fake(name="versioned", version="1.0")
def version_1(dialect: Dialect):
    """
    An implementation which claims to be in version 1.0.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: []

@fake(name="versioned", version="2.0")
def version_2(dialect: Dialect):
    """
    An implementation which claims to be in version 2.0.

    The validity result of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: []
