from hypothesis import HealthCheck, given, settings
from hypothesis.strategies import data, integers, just, sampled_from, sets

from bowtie import hypothesis as strategies
from bowtie._report import Report


@given(strategies.test_cases())
def test_test_cases_have_at_least_one_test(case):
    assert len(case.tests) >= 1


@given(strategies.tests(valid=just(True)))
def test_tests_valid(test):
    assert test.valid


@given(strategies.tests(valid=just(False)))
def test_tests_invalid(test):
    assert not test.valid


@given(strategies.any_case_results())
def test_successful_case_results_have_at_least_one_test(result):
    assert result.results is None or len(result.results) >= 1


@given(data())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_cases_and_results_with_given_implementations(data):
    n = data.draw(integers(min_value=1, max_value=5))
    strategy = strategies.cases_and_results(
        implementations=strategies.implementations(min_size=n, max_size=n),
    )
    seq_cases, results = data.draw(strategy)
    # all implementations have results
    assert len(results) == n * len(seq_cases)


@given(strategies.cases_and_results())
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_cases_and_results_generates_correct_test_results(cases_results):
    """
    The number of test results for each test case matches the number of tests.
    """
    seq_cases, seq_results = cases_results
    for seq_case in seq_cases:
        results = [
            seq_result.result
            for seq_result in seq_results
            if seq_result.seq == seq_case.seq
        ]
        assert all(
            len([each.result_for(i) for i in range(len(seq_case.case.tests))])
            == len(seq_case.case.tests)
            for each in results
        )


@given(strategies.cases_and_results(min_cases=2))  # no point for 1
@settings(suppress_health_check=[HealthCheck.too_slow])
def test_cases_are_unique_by_default(cases_results):
    seq_cases, _ = cases_results
    assert len({each.case.uniq() for each in seq_cases}) == len(seq_cases)


@given(data())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_cases_and_results_with_not_all_responding(data):
    n = data.draw(integers(min_value=1, max_value=5))
    impls = data.draw(strategies.implementations(min_size=n, max_size=n))
    responding = data.draw(integers(min_value=1, max_value=n))
    strategy = strategies.cases_and_results(
        implementations=just(impls),
        responding=lambda seq_case: sets(
            sampled_from(sorted(impls)),
            min_size=responding,
            max_size=responding,
        ),
    )
    seq_cases, results = data.draw(strategy)
    # only responding implementations have results
    assert len(results) == responding * len(seq_cases)


@given(strategies.known_dialects)
def test_known_dialects(dialect):
    assert dialect.uri.host_str == "json-schema.org"


@given(strategies.report_data())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_report_data_generates_implementations_which_support_the_dialect(data):
    report = Report.from_input(data)
    assert all(
        report.metadata.dialect in implementation.dialects
        for implementation in report.implementations.values()
    )


@given(strategies.report_data())
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_report_data_generates_boolean_schemas_only_when_supported(data):
    report = Report.from_input(data)
    if not report.metadata.dialect.has_boolean_schemas:
        assert not any(
            isinstance(case.schema, bool)
            for case, _ in report.cases_with_results()
        )


@given(strategies.report_data(fail_fast=just(True)))
@settings(suppress_health_check=[HealthCheck.too_slow], deadline=None)
def test_report_data_can_be_marked_fail_fast(data):
    assert Report.from_input(data).did_fail_fast
