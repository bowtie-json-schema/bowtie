from hypothesis import given
from hypothesis.strategies import just

from bowtie import hypothesis as strategies


@given(strategies.test_cases())
def test_test_cases_have_at_least_one_test(case):
    assert len(case.tests) >= 1


@given(strategies.tests(valid=just(True)))
def test_tests_valid(test):
    assert test.valid


@given(strategies.tests(valid=just(False)))
def test_tests_invalid(test):
    assert not test.valid


@given(strategies.case_results())
def test_case_results_have_at_least_one_test(case_result):
    assert len(case_result.results) >= 1


@given(strategies.cases_and_results(implementations=just({"foo", "bar"})))
def test_cases_and_results_with_given_implementations(seq_cases_results):
    seq_cases, results = seq_cases_results
    # all implementations have results
    assert len(results) == len({"foo", "bar"}) * len(seq_cases)


@given(strategies.dialects)
def test_dialects(dialect):
    assert dialect.host_str == "json-schema.org"
