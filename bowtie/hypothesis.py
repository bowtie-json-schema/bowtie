# type: ignore[reportMissingParameterType]
"""
Hypothesis strategies and support for Bowtie.

Note that this module depends on you having installed Hypothesis.
"""

from string import printable

from hypothesis.strategies import (
    booleans,
    builds,
    composite,
    dictionaries,
    floats,
    integers,
    just,
    lists,
    none,
    recursive,
    register_type_strategy,
    sampled_from,
    sets,
    text,
    tuples,
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

seq = integers(min_value=1)
implementations = text(printable, min_size=1)


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


test_results = sampled_from(
    [
        _commands.TestResult.VALID,
        _commands.TestResult.INVALID,
    ],
)


@composite
def case_results(
    draw,
    implementations=implementations,
    seq=seq,
    test_results=test_results,
    expected=booleans() | none(),
    min_tests=1,
    max_tests=20,
):
    """
    A result for an individual test case.

    Note that the `Seq` for this result will be arbitrary, so don't use this to
    generate results in isolation without controlling for these IDs being what
    they need to be (i.e. report-wide unique).
    """
    size = draw(integers(min_value=min_tests, max_value=max_tests))
    # FIXME: only successful here
    return _commands.CaseResult(
        implementation=draw(implementations),
        seq=draw(seq),
        results=draw(lists(test_results, min_size=size, max_size=size)),
        expected=draw(lists(expected, min_size=size, max_size=size)),
    )


@composite
def cases_and_results(
    draw,
    implementations=sets(implementations, min_size=1),
    test_cases=test_cases(),
    min_cases=1,
    max_cases=10,
):
    """
    A set of test cases along with their results for generated implementations.
    """
    impls = draw(implementations)

    strategy = lists(
        tuples(seq, test_cases),
        min_size=min_cases,
        max_size=max_cases,
        unique_by=lambda each: each[0],
    )
    seq_cases = draw(strategy)

    return seq_cases, [
        draw(case_results(seq=just(seq), implementations=just(implementation)))
        for implementation in impls
        for (seq, _) in seq_cases
    ]


# FIXME: These don't seem to do anything (in that builds() still fails?)
#        I also don't really understand why the builtin attrs support doesn't
#        autodetect more than it seems to be.
register_type_strategy(_commands.CaseResult, case_results())
register_type_strategy(_commands.Seq, seq)
register_type_strategy(_commands.Test, tests())
register_type_strategy(_commands.TestCase, test_cases())
register_type_strategy(_commands.TestResult, test_results)
