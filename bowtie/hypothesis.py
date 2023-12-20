# type: ignore[reportMissingParameterType]
"""
Hypothesis strategies and support for Bowtie.

Note that this module depends on you having installed Hypothesis.
"""

from string import printable

from hypothesis.strategies import (
    booleans,
    builds,
    dictionaries,
    floats,
    integers,
    lists,
    none,
    recursive,
    register_type_strategy,
    text,
)

from bowtie import _commands

# FIXME: probably via hypothesis-jsonschema
schemas = booleans() | dictionaries(
    keys=text(),
    values=recursive(
        none() | booleans() | floats() | text(printable),
        lambda children: lists(children)
        | dictionaries(text(printable), children),
    ),
)


def tests(
    description=text(),
    instance=integers(),  # FIXME: probably via hypothesis-jsonschema
    valid=booleans() | none(),
    comment=text() | none(),
):
    r"""
    Generate `_commands.Test`\ s.
    """
    return builds(
        _commands.Test,
        description=description,
        instance=instance,
        valid=valid,
        comment=comment,
    )


def test_cases(
    description=text(),
    schema=schemas,
    tests=lists(tests(), min_size=1),
):
    r"""
    Generate `_commands.TestCase`\ s.
    """
    return builds(
        _commands.TestCase,
        description=description,
        schema=schema,
        tests=tests,
    )


# FIXME: These don't seem to do anything (in that builds() still fails?)
#        I also don't really understand why the builtin attrs support doesn't
#        autodetect more than it seems to be.
register_type_strategy(_commands.Test, tests())
register_type_strategy(_commands.TestCase, test_cases())
