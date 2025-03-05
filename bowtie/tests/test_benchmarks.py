from pathlib import Path
import json

import pytest

from bowtie import HOMEPAGE, REPO, _benchmarks, benchmarks
from bowtie._core import Dialect, ImplementationInfo, TestCase
from bowtie._direct_connectable import Direct

# Make pytest ignore this class matching Test*
TestCase.__test__ = False

validators = Direct.from_id("python-jsonschema").registry()

benchmark_report_validator = validators.for_uri(
    "tag:bowtie.report,2024:benchmark_report",
)
benchmark_validator = validators.for_uri("tag:bowtie.report,2024:benchmarks")


def collect_benchmarks(directory):
    return sorted(
        path
        for path in directory.iterdir()
        if path.suffix in {".json", ".py"} and path.name != "__init__.py"
    )


BENCHMARKS_DIR = Path(benchmarks.__file__).parent
BENCHMARK_PATHS = collect_benchmarks(BENCHMARKS_DIR)
KEYWORD_BENCHMARK_PATHS = collect_benchmarks(BENCHMARKS_DIR / "keywords")

DIRECT_CONNECTABLE = "python-jsonschema"


@pytest.fixture
def valid_single_benchmark():
    from bowtie.tests.benchmarks import valid_single_benchmark

    return valid_single_benchmark.get_benchmark()


@pytest.fixture
def valid_benchmark_group(valid_single_benchmark):
    from bowtie.tests.benchmarks import valid_benchmark_group

    return valid_benchmark_group.get_benchmark()


@pytest.fixture
def invalid_benchmark():
    from bowtie.tests.benchmarks import invalid_benchmark

    return invalid_benchmark.get_benchmark()


@pytest.fixture
def benchmarker_run_args():
    return {
        "runs": 1,
        "loops": 1,
        "warmups": 1,
        "values": 2,
    }


def _validate_benchmark_file(file, module):
    data = _benchmarks._load_benchmark_group_from_file(file, module)
    assert benchmark_validator.is_valid(data.serializable())


class TestBenchmarkFormat:

    def test_validate_single_benchmark(self, valid_single_benchmark):
        assert benchmark_validator.is_valid(
            valid_single_benchmark.serializable(),
        )

    def test_validate_benchmark_group(self, valid_benchmark_group):
        assert benchmark_validator.is_valid(
            valid_benchmark_group.serializable(),
        )

    @pytest.mark.parametrize("path", BENCHMARK_PATHS, ids=str)
    def test_validate_default_benchmark_format(self, path):
        benchmark_module = "bowtie.benchmarks"
        _validate_benchmark_file(path, benchmark_module)

    @pytest.mark.parametrize("path", KEYWORD_BENCHMARK_PATHS, ids=str)
    def test_validate_keyword_benchmark_format(self, path):
        benchmark_module = "bowtie.benchmarks.keywords"
        _validate_benchmark_file(path, benchmark_module)


class TestLoadBenchmark:

    def test_benchmark_set_dialect(self, valid_single_benchmark):
        benchmark_json = valid_single_benchmark.serializable()
        benchmark_json["schema"]["$schema"] = Dialect.latest().serializable()
        benchmark_with_explicit_dialect = _benchmarks.Benchmark.from_dict(
            **benchmark_json,
        ).maybe_set_dialect_from_schema()
        assert benchmark_with_explicit_dialect.dialect == Dialect.latest()

    def test_load_benchmark_with_diff_tests(self, valid_single_benchmark):
        benchmark = valid_single_benchmark.benchmark_with_diff_tests(
            tests=valid_single_benchmark.tests * 10,
        )
        assert benchmark_validator.is_valid(benchmark.serializable())

    def test_load_single_benchmark_group_from_dict(
        self,
        valid_single_benchmark,
    ):
        benchmark = valid_single_benchmark.serializable()
        benchmark["benchmark_type"] = "test"
        benchmark_group = _benchmarks.BenchmarkGroup.from_dict(benchmark)

        assert benchmark_validator.is_valid(benchmark_group.serializable())

    def test_load_benchmark_group_from_dict(self, valid_benchmark_group):
        benchmark_json = valid_benchmark_group.serializable()
        benchmark_group = _benchmarks.BenchmarkGroup.from_dict(
            benchmark_json,
            uri=valid_benchmark_group.uri,
        )

        serializable = benchmark_group.serializable()

        assert benchmark_validator.is_valid(serializable)
        assert valid_benchmark_group.serializable() == serializable

    def test_load_single_benchmark_group_from_json(
        self,
        tmp_path,
        valid_single_benchmark,
    ):
        tmp_path = tmp_path / "test_file.json"
        single_benchmark_json = valid_single_benchmark.serializable()
        single_benchmark_json["benchmark_type"] = "test"
        tmp_path.write_text(json.dumps(single_benchmark_json))
        benchmark_group = _benchmarks.BenchmarkGroup.from_file(tmp_path)
        assert benchmark_validator.is_valid(benchmark_group.serializable())

    def test_load_benchmark_group_from_json(
        self,
        tmp_path,
        valid_benchmark_group,
    ):
        tmp_path = tmp_path / "test_file.json"

        benchmark_group_json = valid_benchmark_group.serializable()
        benchmark_group_json["uri"] = str(tmp_path.absolute().as_uri())
        tmp_path.write_text(json.dumps(benchmark_group_json))

        loaded_benchmark_group = _benchmarks.BenchmarkGroup.from_file(tmp_path)

        assert (
            benchmark_validator.validated(
                loaded_benchmark_group.serializable(),
            )
            == benchmark_group_json
        )

    def test_load_benchmark_groups_from_folder(self):
        benchmark_groups = _benchmarks.BenchmarkGroup.from_folder(
            Path(__file__).parent / "benchmarks",
            module="bowtie.tests.benchmarks",
        )
        valid_benchmarks_for_test = 3
        valid_count = 0

        for benchmark_group in benchmark_groups:
            assert benchmark_validator.is_valid(benchmark_group.serializable())
            valid_count += 1

        assert valid_count == valid_benchmarks_for_test


class TestBenchmarker:

    def test_default_benchmarker(self, benchmarker_run_args):
        _benchmarks.Benchmarker.from_default_benchmarks(**benchmarker_run_args)

    @pytest.mark.parametrize(
        "dialect",
        Dialect.known(),
        ids=lambda param: param.short_name,
    )
    def test_keywords_benchmarker(self, dialect, benchmarker_run_args):
        _benchmarks.Benchmarker.for_keywords(dialect, **benchmarker_run_args)

    def test_test_cases_benchmarker(
        self,
        valid_single_benchmark,
        benchmarker_run_args,
    ):
        test_case = TestCase(
            description=valid_single_benchmark.description,
            schema=valid_single_benchmark.schema,
            tests=valid_single_benchmark.tests,
        )

        _benchmarks.Benchmarker.from_test_cases(
            [test_case],
            **benchmarker_run_args,
        )

    def test_input_benchmarker(
        self,
        valid_single_benchmark,
        benchmarker_run_args,
    ):
        _benchmarks.Benchmarker.from_input(
            valid_single_benchmark.serializable(),
            **benchmarker_run_args,
        )


class TestBenchmarkReport:

    def test_merge_benchmark_reports(
        self,
    ):
        benchmark_metadata = _benchmarks.BenchmarkMetadata(
            implementations={
                "foo": ImplementationInfo(
                    name="foo",
                    language="blub",
                    homepage=HOMEPAGE,
                    issues=REPO / "issues",
                    source=REPO,
                    dialects=frozenset([Dialect.latest()]),
                ),
            },
            dialect=Dialect.latest(),
            num_runs=1,
            num_loops=1,
            num_values=1,
            num_warmups=1,
        )

        benchmark_results = [
            _benchmarks.BenchmarkResult(
                name="benchmark1",
                description="test",
                test_results=[
                    _benchmarks.TestResult(
                        description="test",
                        connectable_results=[
                            _benchmarks.ConnectableResult(
                                connectable_id="foo",
                                duration=1.0,
                                values=[1.0],
                                errored=False,
                            ),
                        ],
                    ),
                ],
            ),
        ]
        benchmark_report1 = _benchmarks.BenchmarkReport(
            metadata=benchmark_metadata,
            results={
                "benchmark_group_1": _benchmarks.BenchmarkGroupResult(
                    name="benchmark_group_1",
                    description="test",
                    benchmark_type="test",
                    benchmark_results=benchmark_results,
                ),
            },
        )
        benchmark_report2 = _benchmarks.BenchmarkReport(
            metadata=benchmark_metadata,
            results={
                "benchmark_group_2": _benchmarks.BenchmarkGroupResult(
                    name="benchmark_group_2",
                    description="test",
                    benchmark_type="test",
                    benchmark_results=benchmark_results,
                ),
            },
        )
        merged_report = _benchmarks.BenchmarkReport.merge(
            [benchmark_report1, benchmark_report2],
        )
        assert len(merged_report.results.items()) == len(
            benchmark_report1.results.items(),
        ) + len(benchmark_report2.results.items())
        assert "benchmark_group_1" in merged_report.results
        assert "benchmark_group_2" in merged_report.results
