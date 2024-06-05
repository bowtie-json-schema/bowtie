"""
A collection of small mini-fake implementations with deterministic behavior.

Useful for testing Bowtie's own internal behavior.
"""

from bowtie import HOMEPAGE, REPO
from bowtie._core import Dialect
from bowtie._direct_connectable import python_implementation


class NotValid(Exception):
    pass


def fake(dialects=frozenset(Dialect.known()), **kwargs):
    return python_implementation(
        homepage=HOMEPAGE,
        issues=REPO / "issues",
        source=REPO,
        version="v1.0.0",
        dialects=dialects,
        **kwargs,
    )


@fake()
def always_valid(dialect: Dialect):
    """
    Always considers any instance valid.
    """
    return lambda schema, registry: lambda instance: []


@fake()
def always_invalid(dialect: Dialect):
    """
    Always considers any instance invalid.
    """
    return lambda schema, registry: lambda instance: [NotValid(instance)]


@fake(dialects=frozenset([Dialect.by_short_name()["draft3"]]))
def only_draft3(dialect: Dialect):
    """
    Claims to only support Draft 3.

    The validity of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: []


@fake(language="javascript")
def fake_javascript(dialect: Dialect):
    """
    Claims to be written in Javascript.

    The validity of instances should not be relied on.
    """
    return lambda schema, registry: lambda instance: []


@fake()
def passes_smoke(dialect: Dialect):
    """
    An implementation which crudely passes `bowtie smoke`.
    """
    return lambda schema, registry: lambda instance: (  # naively...
        [] if "not" not in schema else [NotValid(instance)]
    )
