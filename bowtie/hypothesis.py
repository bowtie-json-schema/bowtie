# type: ignore[reportMissingParameterType]
"""
Hypothesis strategies and support for Bowtie.

Note that this module depends on you having installed Hypothesis.
"""

from string import printable

from hypothesis.provisional import urls
from hypothesis.strategies import (
    booleans,
    builds,
    composite,
    dates,
    dictionaries,
    fixed_dictionaries,
    floats,
    from_regex,
    frozensets,
    integers,
    just,
    lists,
    none,
    recursive,
    register_type_strategy,
    sampled_from,
    text,
    tuples,
    uuids,
)
from url import URL

from bowtie import _commands
from bowtie._core import (
    Dialect,
    Example,
    ImplementationInfo,
    Test,
    TestCase,
)
from bowtie._direct_connectable import Direct
from bowtie._report import Report, RunMetadata


def pattern_from(uri):
    """
    Return a strategy which matches the pattern in the given schema.
    """
    validators = Direct.from_id("python-jsonschema").registry()
    return from_regex(validators.schema(uri)["pattern"])


# FIXME: probably via hypothesis-jsonschema
object_schemas = dictionaries(
    keys=text(),
    values=recursive(
        none() | booleans() | floats() | text(printable),
        lambda children: lists(children)
        | dictionaries(text(printable), children),
        max_leaves=3,
    ),
    max_size=5,
)
schemas = booleans() | object_schemas

seqs = uuids().map(lambda uuid: uuid.hex)
connectable_ids = text()
implementation_names = pattern_from(
    "tag:bowtie.report,2024:models:implementation:name",
)
languages = pattern_from(
    "tag:bowtie.report,2024:models:implementation:language",
)


def dialects(
    prety_names=text(max_size=15),
    short_names=text(max_size=10),
    uris=urls().map(URL.parse),
    publication_dates=dates(),
    aliases=frozensets(text(), max_size=2),
):
    """
    Generate a dialect.
    """
    return builds(
        Dialect,
        pretty_name=prety_names,
        short_name=prety_names,
        uri=uris,
        first_publication_date=publication_dates,
        aliases=aliases,
    )


#: Only one of our "real" dialects.
known_dialects = sampled_from(sorted(Dialect.known()))


@composite
def implementation_infos(
    draw,
    names=implementation_names,
    dialects=frozensets(known_dialects, min_size=1, max_size=4),
    languages=languages,
):
    """
    Generate an implementation (info).
    """
    name = draw(names)
    language = draw(languages)
    return ImplementationInfo(
        name=name,
        language=language,
        homepage=draw(urls().map(URL.parse)),
        issues=draw(urls().map(URL.parse)),
        source=draw(urls().map(URL.parse)),
        dialects=draw(dialects),
    )


def implementations(
    infos=implementation_infos(),
    min_size=1,
    max_size=5,
):
    """
    Generate (unique) collections of implementations.
    """
    return dictionaries(
        connectable_ids,
        infos,
        min_size=min_size,
        max_size=max_size,
    )


def examples(
    description=text(),
    instance=integers(),  # FIXME: probably via hypothesis-jsonschema
    comment=text() | none(),
):
    r"""
    Generate `Example`\ s.
    """
    return builds(
        Example,
        description=description,
        instance=instance,
        comment=comment,
    )


def tests(
    description=text(),
    instance=integers(),  # FIXME: probably via hypothesis-jsonschema
    valid=booleans(),
    comment=text() | none(),
):
    r"""
    Generate `Test`\ s.
    """
    return builds(
        Test,
        description=description,
        instance=instance,
        valid=valid,
        comment=comment,
    )


def test_cases(
    description=text(),
    schemas=schemas,
    tests=lists(examples() | tests(), min_size=1, max_size=8),
):
    r"""
    Generate `TestCase`\ s.
    """
    return builds(
        TestCase,
        description=description,
        schema=schemas,
        tests=tests,
    )


successful_tests = sampled_from(
    [
        _commands.TestResult.VALID,
        _commands.TestResult.INVALID,
    ],
)
errored_tests = builds(
    _commands.ErroredTest,
    context=fixed_dictionaries(
        {},
        optional=dict(
            message=text(min_size=1, max_size=50),
            traceback=text(min_size=1, max_size=50),
            foo=text(),
        ),
    ),
)
skipped_tests = builds(
    _commands.SkippedTest,
    message=text(min_size=1, max_size=50) | none(),
    issue_url=urls() | none(),
)
test_results = successful_tests | errored_tests | skipped_tests


def case_results(min_tests=1, max_tests=10):
    """
    A successfully executed (though perhaps still failing) test case result.
    """
    return builds(
        _commands.CaseResult,
        results=lists(test_results, min_size=min_tests, max_size=max_tests),
    )


def errored_cases(
    context=dictionaries(keys=text(), values=text() | integers(), max_size=5),
    caught=booleans(),
):
    """
    A test case which errored (caught or otherwise).
    """
    return builds(_commands.CaseErrored, context=context, caught=caught)


def skipped_cases(
    message=text(min_size=1, max_size=50) | none(),
    issue_url=urls() | none(),
):
    """
    A test case which was skipped by an implementation.
    """
    return builds(_commands.CaseSkipped, message=message, issue_url=issue_url)


def any_case_results(min_tests=1, max_tests=10):
    """
    Any kind of case result.
    """
    happy = case_results(min_tests=min_tests, max_tests=max_tests)
    return happy | errored_cases() | skipped_cases()


def seq_results(
    seqs=seqs,
    implementations=implementation_names,
    min_tests=1,
    max_tests=10,
):
    """
    A result with its seq and implementation.
    """
    return integers(min_value=min_tests, max_value=max_tests).flatmap(
        lambda size: builds(
            _commands.SeqResult,
            seq=seqs,
            implementation=implementations,
            expected=lists(booleans() | none(), min_size=size, max_size=size),
            result=any_case_results(min_tests=size, max_tests=size),
        ),
    )


# Evade the s h a d o w
_implementations = implementations
_test_cases = test_cases


@composite
def cases_and_results(
    draw,
    implementations=implementations(),
    responding=None,
    seqs=seqs,
    test_cases=test_cases(),
    min_cases=1,
    max_cases=8,
):
    """
    A set of test cases along with their results for generated implementations.
    """
    impls = draw(implementations)

    if responding is None:

        def responding(seq_case):
            return just(impls)

    strategy = lists(
        tuples(seqs, test_cases),
        min_size=min_cases,
        max_size=max_cases,
        unique_by=(lambda sc: sc[0], lambda sc: sc[1].uniq()),
    ).map(
        lambda v: [_commands.SeqCase(seq=seq, case=case) for seq, case in v],
    )
    seq_cases = draw(strategy)

    return seq_cases, [
        draw(
            seq_results(
                seqs=just(seq_case.seq),
                implementations=just(id),
                min_tests=len(seq_case.case.tests),
                max_tests=len(seq_case.case.tests),
            ),
        )
        for seq_case in seq_cases
        for id in draw(responding(seq_case))
    ]


_cases_and_results = cases_and_results


@composite
def run_metadata(draw, dialects=known_dialects, implementations=None):
    """
    Generate just a report's metadata.
    """
    dialect = draw(dialects)
    if implementations is None:
        with_dialect = frozensets(
            dialects,
            max_size=4,
        ).map(lambda v: v | {dialect})
        infos = implementation_infos(dialects=with_dialect)
        implementations = _implementations(infos=infos)
    return RunMetadata(dialect=dialect, implementations=draw(implementations))


@composite
def report_data(
    draw,
    run_metadata=run_metadata(),
    cases_and_results=None,
    fail_fast=booleans(),
):
    """
    Generate Bowtie report data (suitable for `Report.from_input`).
    """
    metadata = draw(run_metadata)

    if cases_and_results is None:
        cases = test_cases(
            schemas=(
                schemas
                if metadata.dialect.has_boolean_schemas
                else object_schemas
            ),
        )
        cases_and_results = _cases_and_results(
            test_cases=cases,
            implementations=just(metadata.implementations),
        )

    seq_cases, results = draw(cases_and_results)
    return [  # FIXME: Combine with the logic in CaseReporter
        metadata.serializable(),
        *[seq_case.serializable() for seq_case in seq_cases],
        *[result.serializable() for result in results],
        {"did_fail_fast": draw(fail_fast)},
    ]


def reports(**kwargs):
    """
    Generate full Bowtie reports.
    """
    return report_data(**kwargs).map(Report.from_input)


# FIXME: These don't seem to do anything (in that builds() still fails?)
#        I also don't really understand why the builtin attrs support doesn't
#        autodetect more than it seems to be.
register_type_strategy(Dialect, dialects())
register_type_strategy(_commands.CaseResult, case_results())
register_type_strategy(_commands.CaseErrored, errored_cases())
register_type_strategy(_commands.CaseSkipped, skipped_cases())
register_type_strategy(Example, examples())
register_type_strategy(Test, tests())
register_type_strategy(TestCase, test_cases())
register_type_strategy(_commands.TestResult, successful_tests)
register_type_strategy(_commands.SkippedTest, skipped_tests)
register_type_strategy(_commands.ErroredTest, errored_tests)
register_type_strategy(_commands.AnyTestResult, test_results)
register_type_strategy(Report, reports())
