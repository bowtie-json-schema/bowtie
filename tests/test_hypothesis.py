from hypothesis import given
from hypothesis.strategies import just

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


@given(strategies.any_case_results)
def test_successful_case_results_have_at_least_one_test(result):
    assert (
        result.failed
        or result.errored
        or result.skipped
        or len(result.results) >= 1
    )


@given(strategies.cases_and_results(implementations=just({"foo", "bar"})))
def test_cases_and_results_with_given_implementations(seq_cases_results):
    seq_cases, results = seq_cases_results
    # all implementations have results
    assert len(results) == len({"foo", "bar"}) * len(seq_cases)


@given(strategies.dialects)
def test_dialects(dialect):
    assert dialect.host_str == "json-schema.org"


@given(strategies.report_data(fail_fast=just(True)))
def test_report_data_can_be_marked_fail_fast(data):
    assert Report.from_input(data).did_fail_fast
