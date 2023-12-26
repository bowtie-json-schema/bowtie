# type: ignore[reportMissingParameterType]
"""
Hypothesis strategies and support for Bowtie.

Note that this module depends on you having installed Hypothesis.
"""

from string import printable

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
    max_size=10,
)

seqs = integers(min_value=1)
implementations = text(printable, min_size=1, max_size=50)
dialects = sampled_from(list(TEST_SUITE_DIALECT_URLS))


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
    implementations=implementations,
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


def errored_cases(implementations=implementations, seqs=seqs):
    """
    A test case which errored under an implementation (caught or not).
    """
    return builds(
        _commands.CaseErrored,
        implementation=implementations,
        seq=seqs,
        expected=lists(booleans() | none()),
        context=dictionaries(  # FIXME
            keys=text(),
            values=text() | integers(),
            max_size=5,
        ),
        caught=booleans(),
    )


def skipped_cases(
    implementations=implementations,
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
    implementations=sets(implementations, min_size=1, max_size=5),
    seqs=seqs,
    test_cases=test_cases(),
    min_cases=1,
    max_cases=8,
):
    """
    A set of test cases along with their results for generated implementations.
    """
    impls = draw(implementations)

    strategy = lists(
        tuples(seqs, test_cases),
        min_size=min_cases,
        max_size=max_cases,
        unique_by=lambda each: each[0],
    )
    seq_cases = draw(strategy)

    return seq_cases, [
        draw(
            case_results(seqs=just(seq), implementations=just(implementation)),
        )
        for implementation in impls
        for (seq, _) in seq_cases
    ]


def implementations_with_metadata(
    implementations=sets(implementations, min_size=1, max_size=5),
    metadata=fixed_dictionaries({"language": text(min_size=1, max_size=20)}),
):
    """
    Implementations along with their metadata.
    """
    return implementations.flatmap(
        lambda impls: fixed_dictionaries(
            {
                name: metadata.map(
                    lambda data, name=name: dict(
                        image=f"bowtie-hypothesis-generated/{name}",
                        **data,
                    ),
                )
                for name in impls
            },
        ),
    )


def run_metadata(
    dialects=dialects,
    implementations_with_metadata=implementations_with_metadata,
):
    """
    Generate just a report's metadata.
    """
    return builds(
        RunMetadata,
        dialect=dialects,
        implementations=implementations_with_metadata,
    )


# Evade the s h a d o w
_implementations_with_metadata = implementations_with_metadata
_cases_and_results = cases_and_results
_run_metadata = run_metadata


@composite
def report_data(
    draw,
    dialects=dialects,
    implementations_with_metadata=None,
    run_metadata=None,
    cases_and_results=None,
    fail_fast=booleans(),
):
    """
    Generate Bowtie report data (suitable for `Report.from_input`).
    """
    if implementations_with_metadata is None:
        if cases_and_results is not None:
            raise ValueError(
                "Providing cases+results without implementations can lead to "
                "inconsistent reports.",
            )
        implementations_with_metadata = _implementations_with_metadata()
    implementations = draw(implementations_with_metadata)
    names = implementations.keys()

    if cases_and_results is None:
        cases_and_results = _cases_and_results(implementations=just(names))

    seq_cases, results = draw(cases_and_results)

    if run_metadata is None:
        run_metadata = _run_metadata(
            dialects=dialects,
            implementations_with_metadata=just(implementations),
        )
    return [  # FIXME: Combine with the logic in CaseReporter
        draw(run_metadata).serializable(),
        *[dict(case=case.serializable(), seq=seq) for seq, case in seq_cases],
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
