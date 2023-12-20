from hypothesis import given
from hypothesis.strategies import just

import bowtie.hypothesis


@given(bowtie.hypothesis.test_cases())
def test_test_cases_have_at_least_one_test(case):
    assert len(case.tests) >= 1


@given(bowtie.hypothesis.tests(valid=just(True)))
def test_tests_valid(test):
    assert test.valid


@given(bowtie.hypothesis.tests(valid=just(False)))
def test_tests_invalid(test):
    assert not test.valid


@given(bowtie.hypothesis.case_results())
def test_case_results_have_at_least_one_test(case_result):
    assert len(case_result.results) >= 1


@given(
    bowtie.hypothesis.cases_and_results(implementations=just({"foo", "bar"})),
)
def test_cases_and_results_with_given_implementations(seq_cases_results):
    seq_cases, results = seq_cases_results
    # all implementations have results
    assert len(results) == len({"foo", "bar"}) * len(seq_cases)
