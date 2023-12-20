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
