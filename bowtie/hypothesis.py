# type: ignore[reportMissingParameterType]
"""
Hypothesis strategies and support for Bowtie.

Note that this module depends on you having installed Hypothesis.
"""

from string import ascii_lowercase, digits, printable

from attrs import asdict
from hypothesis.strategies import (
    booleans,
    builds,
    composite,
    dictionaries,
    fixed_dictionaries,
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
from bowtie._cli import TEST_SUITE_DIALECT_URLS
from bowtie._report import Report, RunMetadata

# FIXME: probably via hypothesis-jsonschema
schemas = booleans() | dictionaries(
    keys=text(),
    values=recursive(
        none() | booleans() | floats() | text(printable),
        lambda children: lists(children)
        | dictionaries(text(printable), children),
        max_leaves=3,
    ),
    max_size=5,
)

seqs = integers(min_value=1)
implementation_names = text(  # FIXME: see the start command schema
    ascii_lowercase + digits + "-+_",
    min_size=1,
    max_size=50,
)
languages = text(printable, min_size=1, max_size=20)
dialects = sampled_from(list(TEST_SUITE_DIALECT_URLS))


def implementations(
    names=implementation_names,
    languages=languages,
    min_size=1,
    max_size=5,
):
    """
    Generate (unique) collections of implementations with their metadata.
    """
    return sets(
        tuples(names, languages),
        min_size=min_size,
        max_size=max_size,
    ).map(
        lambda values: {
            (image := f"bowtie-hypothesis-generated/{language}/{name}"): dict(
                image=image,
                name=name,
                language=language,
            )
            for name, language in values
        },
    )


implementation_images = implementations(min_size=1, max_size=1).map(
    lambda result: next(iter(result)),
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
    tests=lists(tests(), min_size=1, max_size=8),
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
    issue_url=text(min_size=1, max_size=50) | none(),
)
test_results = successful_tests | errored_tests | skipped_tests


def case_results(
    implementations=implementation_images,
    seqs=seqs,
    min_tests=1,
    max_tests=10,
):
    """
    A successfully executed (though perhaps still failing) test case result.

    Note that the `Seq` for this result will be arbitrary, so don't use this to
    generate results in isolation without controlling for these IDs being what
    they need to be (i.e. report-wide unique).
    """
    return integers(min_value=min_tests, max_value=max_tests).flatmap(
        lambda size: builds(
            _commands.CaseResult,
            implementation=implementations,
            seq=seqs,
            results=lists(test_results, min_size=size, max_size=size),
            expected=lists(booleans() | none(), min_size=size, max_size=size),
        ),
    )


def errored_cases(implementations=implementation_images, seqs=seqs):
    """
    A test case which errored under an implementation (caught or not).
    """
    return builds(
        _commands.CaseErrored,
        implementation=implementations,
        seq=seqs,
        expected=lists(booleans() | none()),
        context=dictionaries(
            keys=text(),
            values=text() | integers(),
            max_size=5,
        ),
        caught=booleans(),
    )


def skipped_cases(
    implementations=implementation_images,
    seqs=seqs,
    message=text(min_size=1, max_size=50) | none(),
    issue_url=text(min_size=1, max_size=50) | none(),
):
    """
    A test case which was skipped by an implementation.
    """
    return builds(
        _commands.CaseSkipped,
        implementation=implementations,
        seq=seqs,
        expected=lists(booleans() | none()),
        message=message,
        issue_url=issue_url,
    )


any_case_results = case_results() | errored_cases() | skipped_cases()


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
            case_results(
                seqs=just(seq_case.seq),
                implementations=just(implementation),
            ),
        )
        for seq_case in seq_cases
        for implementation in draw(responding(seq_case))
    ]


def run_metadata(dialects=dialects, implementations=implementations()):
    """
    Generate just a report's metadata.
    """
    return builds(
        RunMetadata,
        dialect=dialects,
        implementations=implementations,
    )


# Evade the s h a d o w
_implementations = implementations
_cases_and_results = cases_and_results
_run_metadata = run_metadata


@composite
def report_data(
    draw,
    dialects=dialects,
    implementations=None,
    run_metadata=None,
    cases_and_results=None,
    fail_fast=booleans(),
):
    """
    Generate Bowtie report data (suitable for `Report.from_input`).
    """
    if implementations is None:
        if cases_and_results is not None:
            raise ValueError(
                "Providing cases+results without implementations can lead to "
                "inconsistent reports.",
            )
        implementations = _implementations()
    impls = draw(implementations)

    if cases_and_results is None:
        cases_and_results = _cases_and_results(implementations=just(impls))

    seq_cases, results = draw(cases_and_results)

    if run_metadata is None:
        run_metadata = _run_metadata(
            dialects=dialects,
            implementations=just(impls),
        )
    return [  # FIXME: Combine with the logic in CaseReporter
        draw(run_metadata).serializable(),
        *[seq_case.serializable() for seq_case in seq_cases],
        *[asdict(result) for result in results],
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
register_type_strategy(_commands.CaseResult, case_results())
register_type_strategy(_commands.CaseErrored, errored_cases())
register_type_strategy(_commands.CaseSkipped, skipped_cases())
register_type_strategy(_commands.Seq, seqs)
register_type_strategy(_commands.Test, tests())
register_type_strategy(_commands.TestCase, test_cases())
register_type_strategy(_commands.TestResult, successful_tests)
register_type_strategy(_commands.SkippedTest, skipped_tests)
register_type_strategy(_commands.ErroredTest, errored_tests)
register_type_strategy(_commands.AnyTestResult, test_results)
register_type_strategy(Report, reports())
