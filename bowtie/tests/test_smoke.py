import pytest

from bowtie._commands import CaseResult, ErroredTest, SeqResult, TestResult
from bowtie._core import Dialect, Test, TestCase
from bowtie._smoke import DialectResults, Result


@pytest.fixture
def draft202012():
    return Dialect.by_short_name()["draft2020-12"]


@pytest.fixture
def draft7():
    return Dialect.by_short_name()["draft7"]


@pytest.fixture
def sample_failure():
    case = TestCase(
        description="test",
        schema={"type": "string"},
        tests=[Test(description="test", instance=37, valid=True)],
    )
    seq_result = SeqResult(
        seq="test-1",
        implementation="test-impl",
        result=CaseResult(results=[TestResult(valid=False)]),
        expected=[True],
    )
    return (case, seq_result)


class TestSmokeResult:
    def test_is_completely_broken_all_failures(
        self, draft202012, draft7, sample_failure
    ):
        dialects = DialectResults()
        dialects = dialects.with_result(draft202012, [sample_failure])
        dialects = dialects.with_result(draft7, [sample_failure])

        result = Result(id="test-impl", dialects=dialects, ref=None)

        assert result.is_completely_broken is True

    def test_is_completely_broken_some_success(
        self, draft202012, draft7, sample_failure
    ):
        dialects = DialectResults()
        dialects = dialects.with_result(draft202012, [])
        dialects = dialects.with_result(draft7, [sample_failure])

        result = Result(id="test-impl", dialects=dialects, ref=None)

        assert result.is_completely_broken is False

    def test_all_tests_errored_false_when_no_failures(self, draft202012):
        dialects = DialectResults().with_result(draft202012, [])
        result = Result(id="test-impl", dialects=dialects, ref=None)

        assert result.all_tests_errored is False

    def test_all_tests_errored_true(self, draft202012):
        case = TestCase(
            description="test",
            schema={"type": "string"},
            tests=[
                Test(description="test1", instance=37, valid=True),
                Test(description="test2", instance="foo", valid=True),
            ],
        )
        seq_result = SeqResult(
            seq="test-1",
            implementation="test-impl",
            result=CaseResult(
                results=[
                    ErroredTest(context={"message": "error 1"}),
                    ErroredTest(context={"message": "error 2"}),
                ],
            ),
            expected=[True, True],
        )
        dialects = DialectResults().with_result(
            draft202012, [(case, seq_result)]
        )
        result = Result(id="test-impl", dialects=dialects, ref=None)

        assert result.all_tests_errored is True
