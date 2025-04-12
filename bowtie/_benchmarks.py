from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from statistics import geometric_mean
from typing import TYPE_CHECKING
import asyncio
import importlib
import importlib.metadata
import json
import os
import statistics
import subprocess
import tempfile

from attrs import asdict, field, frozen
from attrs.filters import exclude
from diagnostic import DiagnosticError
from rich import box
from rich.console import Console
from rich.progress import Progress
from rich.table import Column, Table
from url import URL
import pyperf  # type: ignore[reportMissingTypeStubs]

from bowtie import _report
from bowtie._core import (
    Dialect,
    Example,
    ImplementationInfo,
    Test,
    TestCase,
    convert_table_to_markdown,
)
from bowtie._direct_connectable import Direct

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from typing import Any

    from bowtie._commands import (
        Message,
    )
    from bowtie._connectables import Connectable, ConnectableId

Seq = int | str

Benchmark_Group_Name = str
Benchmark_Criteria = str

STDOUT = Console()
STDERR = Console(stderr=True)

benchmark_validator = (
    Direct.from_id("python-jsonschema")
    .registry()
    .for_uri(
        URL.parse("tag:bowtie.report,2024:benchmarks"),
    )
)
benchmark_validated, benchmark_invalidated = (
    benchmark_validator.validated,
    benchmark_validator.invalidated,
)


def get_benchmark_files(
    benchmark_type: str | None,
    dialect: Dialect,
    benchmarks: Iterable[str] = [],
) -> list[Path]:
    bowtie_parent_dir = Path(__file__).parent.parent
    benchmarks_dir = bowtie_parent_dir / "bowtie/benchmarks"
    files: list[Path] = []

    for file in benchmarks_dir.rglob("*"):
        relative_folder_path = file.parent.relative_to(bowtie_parent_dir)
        module_name = str(relative_folder_path).replace(os.sep, ".")
        benchmark_group = _load_benchmark_group_from_file(
            file,
            module_name,
        )
        if (
            benchmark_group is not None
            and (
                benchmark_group.benchmark_type == benchmark_type
                or benchmark_type is None
            )
            and dialect in benchmark_group.dialects_supported
        ):
            files.append(file)

    if benchmarks:
        files = [
            matched_file
            for benchmark in benchmarks
            if (
                matched_file := next(
                    (file for file in files if benchmark in str(file)),
                    None,
                )
            )
        ]

    return files


def combine_benchmark_reports_to_serialized(
    benchmark_report_files: Iterable[Path],
) -> str:
    merged_report = BenchmarkReport.merge(
        [
            BenchmarkReport.from_dict(
                **json.loads(report_file.read_text()),
            )
            for report_file in benchmark_report_files
        ],
    )
    return json.dumps(merged_report.serializable())


def _load_benchmark_group_from_file(
    file: Path,
    module: str | None = None,
):
    benchmark_group = None
    if file.suffix == ".py" and file.name != "__init__.py":
        benchmark_module_name = "." + file.stem
        loaded_class = importlib.import_module(
            benchmark_module_name,
            module,
        ).get_benchmark()
        if isinstance(loaded_class, Benchmark):
            benchmark_group = BenchmarkGroup.from_dict(
                loaded_class.serializable(),
                uri=URL.parse(file.absolute().as_uri()),
            )
        elif isinstance(loaded_class, BenchmarkGroup):
            benchmark_group = loaded_class

    elif file.suffix == ".json":
        data = json.loads(file.read_text())
        benchmark_group = BenchmarkGroup.from_dict(
            data,
            uri=URL.parse(file.absolute().as_uri()),
        )

    return benchmark_group


@frozen
class BenchmarkLoadError(Exception):
    message: str

    def __rich__(self):
        return DiagnosticError(
            code="benchmark-load-error",
            message=self.message,
            causes=[],
            hint_stmt=(
                "Make sure that the benchmarks are present "
                "in the appropriate folder and follow the specified schema."
            ),
        )


class BenchmarkError(Exception):
    pass


@frozen
class PyperfError(BenchmarkError):
    """
    Some Error with Pyperf while running the Benchmark.
    """

    error_stack: str

    def __rich__(self):
        return DiagnosticError(
            code="pyperf-benchmark-error",
            message="Pyperf command failed while running the Benchmark.",
            note_stmt=self.error_stack,
            causes=[],
            hint_stmt=(
                "Make sure that pyperf is installed and "
                "all the arguments are provided correctly."
            ),
        )


@frozen
class BowtieRunError(BenchmarkError):
    """
    Some Error with Bowtie while running the Benchmark.
    """

    error_stack: str
    connectable_id: ConnectableId | None

    def __rich__(self):
        return DiagnosticError(
            code="bowtie-benchmark-error",
            message="Bowtie Run command failed while running the Benchmark.",
            note_stmt=self.error_stack,
            causes=[],
            hint_stmt=(
                "Some internal error has occured while running the Benchmark "
                f"with {self.connectable_id}. (Probably some error with "
                "the harness)"
            ),
        )


@frozen
class Benchmark:
    description: str
    name: str
    schema: Any
    tests: Sequence[Example | Test]
    dialect: Dialect | None = None

    @classmethod
    def from_dict(
        cls,
        tests: Iterable[dict[str, Any]],
        name: str,
        **kwargs: Any,
    ):
        return cls(
            tests=[Example.from_dict(**test) for test in tests],
            name=name,
            **kwargs,
        )

    def serializable(self) -> Message:
        return asdict(
            self,
            filter=lambda _, v: v is not None,
        )

    def benchmark_with_diff_tests(self, tests: Sequence[Example | Test]):
        benchmark = self.serializable()
        benchmark["tests"] = tests
        return Benchmark(**benchmark)

    def maybe_set_dialect_from_schema(self):
        dialect_from_schema: str | None = (  # type: ignore[reportUnknownVariableType]
            self.schema.get("$schema")  # type: ignore[reportUnknownMemberType]
            if isinstance(self.schema, dict)
            else None
        )
        if not dialect_from_schema:
            return self

        benchmark = self.serializable()
        benchmark["dialect"] = Dialect.from_str(
            dialect_from_schema,  # type: ignore[reportUnknownArgumentType]
        )
        return Benchmark.from_dict(**benchmark)


@frozen
class BenchmarkGroup:
    name: str
    benchmarks: Sequence[Benchmark]
    description: str
    uri: URL | None
    benchmark_type: str
    dialects_supported: Sequence[Dialect] = list(Dialect.known())
    varying_parameter: str | None = None

    @classmethod
    def from_folder(
        cls,
        folder: Path,
        module: str = "bowtie.benchmarks",
    ) -> Iterable[BenchmarkGroup]:
        for file in folder.iterdir():
            benchmark_group = cls.from_file(file, module)
            if not benchmark_group:
                continue
            yield benchmark_group

    @classmethod
    def from_file(
        cls,
        file: Path,
        module: str = "bowtie.benchmarks",
    ) -> BenchmarkGroup | None:
        return _load_benchmark_group_from_file(
            file,
            module,
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        uri: URL | None = None,
    ) -> BenchmarkGroup:
        varying_parameter = data.pop("varying_parameter", None)
        benchmark_type = data.pop("benchmark_type", "None")
        dialects_supported = [
            (
                dialect
                if isinstance(dialect, Dialect)
                else Dialect.from_str(dialect)
            )
            for dialect in data.pop("dialects_supported", Dialect.known())
        ]

        if "benchmarks" not in data:
            benchmark = Benchmark.from_dict(
                **data,
            ).maybe_set_dialect_from_schema()
            return cls(
                name=benchmark.name,
                description=benchmark.description,
                benchmarks=[benchmark],
                uri=uri,
                benchmark_type=benchmark_type,
                dialects_supported=dialects_supported,
                varying_parameter=varying_parameter,
            )

        benchmarks = [
            Benchmark.from_dict(
                **benchmark,
            ).maybe_set_dialect_from_schema()
            for benchmark in data["benchmarks"]
        ]
        return cls(
            name=data["name"],
            description=data["description"],
            benchmarks=benchmarks,
            uri=uri,
            benchmark_type=benchmark_type,
            varying_parameter=varying_parameter,
            dialects_supported=dialects_supported,
        )

    def serializable(self) -> Message:
        serialized_dict = asdict(
            self,
            filter=lambda _, v: v is not None,
        )
        if "uri" in serialized_dict:
            serialized_dict["uri"] = str(serialized_dict["uri"])
        serialized_dict["dialects_supported"] = [
            dialect.serializable() for dialect in self.dialects_supported
        ]
        return serialized_dict


@frozen
class BenchmarkGroupResult:
    name: str
    benchmark_type: str
    description: str
    benchmark_results: list[BenchmarkResult]
    varying_parameter: str | None = None

    def serializable(self):
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        benchmark_results: list[dict[str, Any]],
        **kwargs: Any,
    ) -> BenchmarkGroupResult:
        return cls(
            benchmark_results=[
                BenchmarkResult.from_dict(**result)
                for result in benchmark_results
            ],
            **kwargs,
        )


@frozen
class BenchmarkResult:
    name: str
    description: str
    test_results: Sequence[TestResult]

    def serializable(self):
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        test_results: list[dict[str, Any]],
        **kwargs: Any,
    ) -> BenchmarkResult:
        return cls(
            test_results=[
                TestResult.from_dict(**result) for result in test_results
            ],
            **kwargs,
        )


@frozen
class TestResult:
    description: str
    connectable_results: Sequence[ConnectableResult]

    def serializable(self):
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        connectable_results: list[dict[str, Any]],
        **kwargs: Any,
    ) -> TestResult:
        return cls(
            connectable_results=[
                ConnectableResult.from_dict(**result)
                for result in connectable_results
            ],
            **kwargs,
        )


@frozen
class ConnectableResult:
    connectable_id: ConnectableId
    duration: float
    values: list[float]
    errored: bool = False

    def serializable(self):
        return asdict(self, filter=lambda _, v: v is not None)

    @classmethod
    def from_dict(cls, **kwargs: Any) -> ConnectableResult:
        return cls(
            **kwargs,
        )


@frozen
class BenchmarkMetadata:
    dialect: Dialect
    implementations: Mapping[ConnectableId, ImplementationInfo] = field(
        alias="implementations",
    )
    num_runs: int
    num_values: int
    num_warmups: int
    num_loops: int
    system_metadata: dict[str, Any] = field(
        factory=dict[str, "Any"],
        repr=False,
    )

    bowtie_version: str = field(
        default=importlib.metadata.version("bowtie-json-schema"),
        eq=False,
        repr=False,
    )
    started: datetime = field(
        factory=lambda: datetime.now(UTC),
        eq=False,
        repr=False,
    )

    def serializable(self):
        as_dict = asdict(
            self,
            filter=exclude("dialect"),
            recurse=False,
        )
        as_dict.update(
            dialect=self.dialect.serializable(),
            started=as_dict.pop("started").isoformat(),
            implementations={
                id: implementation.serializable()
                for id, implementation in self.implementations.items()
            },
        )
        return as_dict

    @classmethod
    def from_dict(
        cls,
        dialect: str,
        implementations: dict[str, dict[str, Any]],
        started: str | None = None,
        **kwargs: Any,
    ) -> BenchmarkMetadata:
        if started is not None:
            kwargs["started"] = datetime.fromisoformat(started)
        return cls(
            dialect=Dialect.from_str(dialect),
            implementations={
                id: ImplementationInfo.from_dict(**data)
                for id, data in implementations.items()
            },
            **kwargs,
        )


@frozen
class BenchmarkReport:
    metadata: BenchmarkMetadata
    results: dict[Benchmark_Group_Name, BenchmarkGroupResult] = field(
        factory=dict[Benchmark_Group_Name, BenchmarkGroupResult],
    )

    def serializable(self):
        as_dict: dict[str, Any] = dict(metadata=self.metadata.serializable())
        as_dict["results"] = [
            benchmark_group_result.serializable()
            for _, benchmark_group_result in self.results.items()
        ]
        return as_dict

    @classmethod
    def from_dict(
        cls,
        metadata: dict[str, Any],
        results: list[dict[str, Any]],
    ) -> BenchmarkReport:
        return cls(
            metadata=BenchmarkMetadata.from_dict(**metadata),
            results={
                r["name"]: BenchmarkGroupResult.from_dict(**r) for r in results
            },
        )

    @classmethod
    def merge(
        cls,
        benchmark_reports: list[BenchmarkReport],
    ) -> BenchmarkReport:
        return BenchmarkReport(
            metadata=benchmark_reports[0].metadata,
            results={
                k: v
                for report in benchmark_reports
                for k, v in report.results.items()
            },
        )


@frozen
class BenchmarkReporter:
    _progress_bar: Progress = field(alias="progress_bar")
    _report: BenchmarkReport = field(alias="report")

    _quiet: bool = field(alias="quiet", default=False)
    _format: str = field(alias="format", default="pretty")
    _benchmark_group_uri: dict[str, URL | None] = field(
        factory=dict[str, URL | None],
    )
    _mean_threshold: float = field(alias="mean_threshold", default=0.10)

    def update_system_metadata(self, system_metadata: dict[str, Any]):
        system_metadata.pop("command")
        system_metadata.pop("name")
        self._report.metadata.system_metadata.update(system_metadata)

    def started(self):
        pass

    def report_incompatible_connectables(
        self,
        incompatible_connectables: Sequence[Connectable],
        dialect: Dialect,
    ):
        for connectable in incompatible_connectables:
            if not self._quiet:
                STDOUT.log(
                    f"{connectable.to_terse()} does not support "
                    f"dialect {dialect.serializable()}\n",
                )

    @staticmethod
    def _total_tests_in_benchmark_group(benchmark_group: BenchmarkGroup):
        num = 0
        for benchmark in benchmark_group.benchmarks:
            num += len(benchmark.tests)
        return num

    def running_benchmark_group(
        self,
        benchmark_group: BenchmarkGroup,
    ):
        progress_bar_task = None
        if not self._quiet:
            progress_bar_task = self._progress_bar.add_task(
                f"Running Benchmark Group: {benchmark_group.name}",
                total=len(self._report.metadata.implementations)
                * self._total_tests_in_benchmark_group(benchmark_group),
            )
        benchmark_results: list[BenchmarkResult] = []
        self._benchmark_group_uri[benchmark_group.name] = benchmark_group.uri

        def benchmark_started(benchmark_name: str, benchmark_description: str):
            test_results: list[TestResult] = []

            def test_started(test_description: str):
                connectable_results: dict[
                    ConnectableId,
                    ConnectableResult,
                ] = {}

                def got_connectable_result(
                    connectable: ConnectableId,
                    test_result: str,
                    retry_count: int,
                    measured_time_values: list[float],
                    errored: bool = False,
                ):
                    retry_needed = False

                    if errored:
                        if not self._quiet:
                            STDOUT.log(
                                f"WARNING!\n{benchmark_group.name}:"
                                f"{benchmark_name}:{test_description}\n"
                                f"Some Error was encountered while running"
                                f"test for {connectable}\n ",
                            )
                        connectable_result = ConnectableResult(
                            connectable_id=connectable,
                            duration=0,
                            values=[1e9, 1e9],
                            errored=True,
                        )
                        connectable_results[connectable] = connectable_result

                    else:
                        benchmark_result = pyperf.Benchmark.loads(test_result)  # type: ignore[reportUnknownVariableType]

                        # Ignoring Warmup Values
                        result_values = measured_time_values[
                            self._report.metadata.num_warmups
                            * self._report.metadata.num_runs :
                        ]

                        if not len(result_values):
                            raise BowtieRunError(
                                "No results were returned",
                                connectable,
                            )

                        benchmark_duration: float = float(
                            benchmark_result.get_total_duration(),  # type: ignore[reportUnknownMemberType]
                        )
                        connectable_result = ConnectableResult(
                            connectable_id=connectable,
                            duration=benchmark_duration,
                            values=result_values,
                        )

                        mean = statistics.mean(result_values)
                        std_dev = statistics.stdev(result_values)
                        if (
                            std_dev / mean > self._mean_threshold
                            and not self._quiet
                        ):
                            retry_needed = True
                            if retry_count == 0:
                                STDOUT.log(
                                    f"WARNING!\n{benchmark_name}:"
                                    f"{test_description}:{connectable}\n"
                                    f"Benchmark Might Be Unstable "
                                    f"(std_dev = {(std_dev / mean) * 100}%)",
                                )

                        if not len(self._report.metadata.system_metadata):
                            self.update_system_metadata(
                                benchmark_result.get_metadata(),  # type: ignore[reportUnknownMemberType]
                            )
                        connectable_results[connectable] = connectable_result

                    if progress_bar_task is not None:
                        if benchmark_group.name == benchmark_name:
                            self._progress_bar.update(
                                progress_bar_task,
                                description=(
                                    f"Running Benchmark: {benchmark_name}\n"
                                    f"Test: {test_description}\n"
                                    f"Connectable: {connectable}"
                                ),
                                advance=1,
                            )
                        else:
                            self._progress_bar.update(
                                progress_bar_task,
                                description=(
                                    f"Running Benchmark Group: "
                                    f"{benchmark_group.name}\n"
                                    f"Benchmark: {benchmark_name}\n"
                                    f"Test: {test_description}\n"
                                    f"Connectable: {connectable}"
                                ),
                                advance=1,
                            )

                    return retry_needed

                def test_finished():
                    test_result = TestResult(
                        description=test_description,
                        connectable_results=list(connectable_results.values()),
                    )
                    test_results.append(test_result)

                return got_connectable_result, test_finished

            def benchmark_finished():
                benchmark_result = BenchmarkResult(
                    name=benchmark_name,
                    description=benchmark_description,
                    test_results=test_results,
                )
                benchmark_results.append(benchmark_result)

            return test_started, benchmark_finished

        def benchmark_group_finished():
            benchmark_group_result = BenchmarkGroupResult(
                name=benchmark_group.name,
                benchmark_type=benchmark_group.benchmark_type,
                description=benchmark_group.description,
                benchmark_results=benchmark_results,
                varying_parameter=benchmark_group.varying_parameter,
            )
            self._report.results[benchmark_group.name] = benchmark_group_result
            if progress_bar_task is not None:
                self._progress_bar.update(progress_bar_task, visible=False)

        return benchmark_started, benchmark_group_finished

    def finished(self):
        if self._format in ("pretty", "markdown"):
            self._print_results_table()
        else:
            STDOUT.print_json(data=self._report.serializable())

    def no_compatible_connectables(self):
        if not self._quiet:
            STDOUT.log("Skipping Benchmark, No Connectables to run !")

    def _print_results_table(self):

        def _format_value(value: float) -> str:

            if value * 1000 < 1:
                return f"{round(value * 1000 * 1000)}us"
            elif value < 1:
                return f"{round(value * 1000)}ms"
            return f"{round(value, 2)}s"

        def _get_sorted_table_from_test_results(
            test_results: Sequence[TestResult],
        ):
            results_for_connectable: dict[
                ConnectableId,
                list[tuple[float, float, bool]],
            ] = {}
            ref_row: list[str] = [""]

            for idx, connectable_result in enumerate(
                test_results[0].connectable_results,
            ):
                connectable_results = [
                    (
                        statistics.mean(
                            test_result.connectable_results[idx].values,
                        ),
                        statistics.stdev(
                            test_result.connectable_results[idx].values,
                        ),
                        test_result.connectable_results[idx].errored,
                    )
                    for test_result in test_results
                ]
                results_for_connectable[connectable_result.connectable_id] = (
                    connectable_results
                )

            sorted_connectables = sorted(
                results_for_connectable.keys(),
                key=(
                    lambda connectable_id: (
                        geometric_mean(
                            [
                                result_mean
                                for (
                                    result_mean,
                                    _,
                                    errored,
                                ) in results_for_connectable[connectable_id]
                                if not errored
                            ]
                            or [1e9],
                        )
                    )
                ),
            )
            results_for_connectable = {
                connectable: results_for_connectable[connectable]
                for connectable in sorted_connectables
            }
            columns = ["Test Name"]
            rows: list[list[str]] = []
            for (
                connectable_id,
                connectable_results,
            ) in results_for_connectable.items():
                columns.append(
                    connectable_id,
                )
                g_mean = geometric_mean(
                    [
                        result_mean
                        for result_mean, _, errored in connectable_results
                        if not errored
                    ]
                    or [1e9],
                )
                if g_mean == geometric_mean([1e9]):
                    ref_row.append("Errored")
                else:
                    ref_row.append(
                        str(g_mean),
                    )

            fastest_connectable_results = next(
                iter(
                    results_for_connectable.values(),
                ),
            )

            for idx, test_result in enumerate(
                test_results,
            ):
                row_elements = [
                    test_result.description,
                ]
                for connectable_idx, results in enumerate(
                    results_for_connectable.items(),
                ):
                    _, connectable_results = results
                    _mean, std_dev, errored = connectable_results[idx]

                    fastest_implementation_mean, _, __ = (
                        fastest_connectable_results[idx]
                    )
                    relative = _mean / fastest_implementation_mean

                    if errored:
                        repr_string = "Errored"
                    else:
                        repr_string = (
                            f"{_format_value(_mean)} +- "
                            f"{_format_value(std_dev)}"
                        )
                        if connectable_idx != 0 and relative > 1:
                            repr_string += f": {round(relative, 2)}x slower"
                        elif connectable_idx:
                            repr_string += (
                                f": {round(1 / relative, 2)}x faster"
                            )

                    row_elements.append(repr_string)

                rows.append(row_elements)

            for implementation_idx in range(2, len(ref_row)):
                if ref_row[implementation_idx] == "Errored":
                    continue
                rounded_off_val = round(
                    float(ref_row[implementation_idx]) / float(ref_row[1]),
                    2,
                )
                ref_row[implementation_idx] = f"{rounded_off_val}x slower"

            ref_row[1] = "Reference"

            if len(results_for_connectable) > 1:
                rows.append(ref_row)

            return rows, columns

        def _table_for_benchmark_result(
            benchmark_result: BenchmarkResult,
        ):
            markdown_content = (
                f"\n\nBenchmark: Tests with {benchmark_result.name}\n"
            )
            inner_table = Table(
                box=box.SIMPLE_HEAD,
                title=(f"Tests with {benchmark_result.name}"),
                min_width=100,
            )
            rows, columns = _get_sorted_table_from_test_results(
                benchmark_result.test_results,
            )
            for column in columns:
                inner_table.add_column(column)
            for row in rows:
                inner_table.add_row(*row)
            markdown_content += convert_table_to_markdown(columns, rows)
            markdown_content += "\n\n"
            return inner_table, markdown_content

        def _table_for_common_tests(
            benchmark_results: list[BenchmarkResult],
        ):
            markdown_content = (
                f"\nBenchmark: Tests with varying "
                f"{benchmark_group_result.varying_parameter}\n"
            )
            common_tests = {
                test.description for test in benchmark_results[0].test_results
            }
            for benchmark_result in benchmark_results[1:]:
                common_tests.intersection_update(
                    test.description for test in benchmark_result.test_results
                )

            common_test = next(iter(common_tests))
            common_test_table = Table(
                box=box.SIMPLE_HEAD,
                title=(
                    f"Tests with varying "
                    f"{benchmark_group_result.varying_parameter}"
                ),
                min_width=100,
            )
            common_test_results: list[TestResult] = [
                TestResult(
                    description=benchmark_result.name,
                    connectable_results=test_result.connectable_results,
                )
                for benchmark_result in benchmark_results
                for test_result in benchmark_result.test_results
                if test_result.description == common_test
            ]

            rows, columns = _get_sorted_table_from_test_results(
                common_test_results,
            )
            for column in columns:
                common_test_table.add_column(column)
            for row in rows:
                common_test_table.add_row(*row)

            markdown_content += convert_table_to_markdown(
                columns,
                rows,
            )
            markdown_content += "\n\n"
            return common_test_table, markdown_content

        cpu_count = self._report.metadata.system_metadata.get(
            "cpu_count",
            "Not Available",
        )
        cpu_freq = self._report.metadata.system_metadata.get(
            "cpu_freq",
            "Not Available",
        )
        cpu_model = self._report.metadata.system_metadata.get(
            "cpu_model_name",
            "Not Available",
        )
        hostname = self._report.metadata.system_metadata.get(
            "hostname",
            "Not Available",
        )

        benchmark_metadata = (
            f"Benchmark Metadata\n\n"
            f"Runs: {self._report.metadata.num_runs}\n"
            f"Values: {self._report.metadata.num_values}\n"
            f"Warmups: {self._report.metadata.num_warmups}\n\n"
            f"CPU Count: {cpu_count}\n"
            f"CPU Frequency: {cpu_freq}\n"
            f"CPU Model: {cpu_model}\n"
            f"Hostname: {hostname}"
        )

        markdown_content = "# Benchmark Summary\n"
        table = Table(
            Column(
                header="Benchmark Group",
                vertical="middle",
                justify="center",
            ),
            Column(header="Results", justify="center"),
            title="Benchmark Summary",
            caption=benchmark_metadata,
        )

        for (
            benchmark_group_name,
            benchmark_group_result,
        ) in self._report.results.items():
            benchmark_group_path = self._benchmark_group_uri[
                benchmark_group_name
            ]

            markdown_content += f"## Benchmark Group: {benchmark_group_name}\n"
            markdown_content += f"Benchmark File: {benchmark_group_path}\n"
            outer_table = Table(
                box=box.SIMPLE_HEAD,
                caption='File "' + str(benchmark_group_path) + '"',
            )

            if benchmark_group_result.varying_parameter:
                common_tests_table, common_tests_table_markdown = (
                    _table_for_common_tests(
                        benchmark_group_result.benchmark_results,
                    )
                )

                outer_table.add_row(common_tests_table)
                markdown_content += common_tests_table_markdown

            inner_table, inner_table_markdown = _table_for_benchmark_result(
                benchmark_group_result.benchmark_results[-1],
            )

            outer_table.add_row(inner_table)
            markdown_content += inner_table_markdown

            if len(benchmark_group_result.benchmark_results) > 0:
                table.add_row(
                    benchmark_group_name,
                    outer_table,
                )

        markdown_content += "## " + benchmark_metadata

        if self._format == "markdown":
            STDOUT.print(markdown_content)
        elif self._format == "pretty":
            STDOUT.print(table)


@frozen
class Benchmarker:
    _benchmark_groups: Iterable[BenchmarkGroup] = field(
        alias="benchmark_groups",
    )
    _num_runs: int = field(
        alias="runs",
    )
    _num_loops: int = field(
        alias="loops",
    )
    _num_warmups: int = field(
        alias="warmups",
    )
    _num_values: int = field(
        alias="values",
    )
    _num_retries: int = field(
        default=8,
    )

    @classmethod
    def from_default_benchmarks(cls, **kwargs: Any):
        bowtie_dir = Path(__file__).parent
        benchmark_dir = bowtie_dir / "benchmarks"

        if not benchmark_dir.exists():
            raise BenchmarkLoadError("Default Benchmarks not found.")

        return cls._from_dict(
            benchmark_groups=BenchmarkGroup.from_folder(
                benchmark_dir,
            ),
            **kwargs,
        )

    @classmethod
    def from_test_cases(
        cls,
        cases: Iterable[TestCase],
        **kwargs: Any,
    ):
        benchmark_groups = [
            BenchmarkGroup(
                name=case.description,
                description=case.description,
                benchmarks=[
                    Benchmark(
                        name=case.description,
                        schema=case.schema,
                        description=case.description,
                        tests=case.tests,
                    ),
                ],
                uri=None,
                benchmark_type="test_case",
            )
            for case in cases
        ]

        return cls._from_dict(
            benchmark_groups=benchmark_groups,
            **kwargs,
        )

    @classmethod
    def for_keywords(cls, dialect: Dialect, **kwargs: Any):
        bowtie_parent_dir = Path(__file__).parent.parent
        keywords_benchmark_dir = (
            bowtie_parent_dir / "bowtie/benchmarks/keywords"
        )

        if not keywords_benchmark_dir.exists():
            raise BenchmarkLoadError("Keyword Benchmarks Folder not found.")

        keyword_benchmarks = get_benchmark_files(
            benchmark_type="keyword",
            dialect=dialect,
        )

        benchmark_groups: list[BenchmarkGroup] = []
        for keyword_benchmark in keyword_benchmarks:
            relative_folder_path = keyword_benchmark.parent.relative_to(
                bowtie_parent_dir,
            )
            module_name = str(relative_folder_path).replace(os.sep, ".")
            benchmark_group = BenchmarkGroup.from_file(
                keyword_benchmark,
                module_name,
            )
            if (
                benchmark_group is not None
                and dialect in benchmark_group.dialects_supported
            ):
                benchmark_groups.append(
                    benchmark_group,
                )

        return cls._from_dict(
            benchmark_groups=benchmark_groups,
            **kwargs,
        )

    @classmethod
    def for_benchmark_files(
        cls,
        benchmark_files: Iterable[str],
        **kwargs: Any,
    ):
        benchmark_groups: list[BenchmarkGroup] = []
        for benchmark_filename in benchmark_files:
            benchmark_file = Path(benchmark_filename).absolute()
            bowtie_parent_dir = Path(__file__).parent.parent

            benchmark_folder = benchmark_file.parent
            relative_path = benchmark_folder.relative_to(bowtie_parent_dir)

            if not benchmark_file.exists():
                raise BenchmarkLoadError("Benchmark File not found !!")

            module_name = str(relative_path).replace(os.sep, ".")

            benchmark_group = BenchmarkGroup.from_file(
                benchmark_file,
                module=module_name,
            )
            if benchmark_group:
                benchmark_groups.append(benchmark_group)

        return cls._from_dict(
            benchmark_groups=benchmark_groups,
            **kwargs,
        )

    @classmethod
    def from_input(
        cls,
        benchmark: dict[str, Any],
        **kwargs: Any,
    ):
        benchmark["benchmark_type"] = "from_input"
        benchmark_validated(benchmark)
        benchmark_group = BenchmarkGroup.from_dict(
            benchmark,
        )
        return cls._from_dict(benchmark_groups=[benchmark_group], **kwargs)

    @classmethod
    def _from_dict(
        cls,
        benchmark_groups: Iterable[BenchmarkGroup],
        runs: int,
        values: int,
        loops: int,
        warmups: int,
        **kwargs: Any,
    ):
        return cls(
            benchmark_groups=benchmark_groups,
            runs=runs,
            values=values,
            loops=loops,
            warmups=warmups,
        )

    async def start(
        self,
        connectables: Iterable[Connectable],
        dialect: Dialect,
        quiet: bool,
        format: str,
    ):

        acknowledged: Mapping[ConnectableId, ImplementationInfo] = {}
        compatible_connectables: list[Connectable] = []
        incompatible_connectables: list[Connectable] = []

        for connectable in connectables:
            silent_reporter = _report.Reporter(
                write=lambda **_: None,  # type: ignore[reportUnknownArgumentType]
            )
            async with connectable.connect(
                reporter=silent_reporter,
                registry=Direct.from_id("null").registry(),
            ) as implementation:
                if dialect not in implementation.info.dialects:
                    incompatible_connectables.append(connectable)
                    continue
                acknowledged[connectable.to_terse()] = implementation.info
                compatible_connectables.append(connectable)

        with Progress(
            console=STDOUT,
            transient=True,
            disable=quiet,
        ) as progress:
            reporter = BenchmarkReporter(
                report=BenchmarkReport(
                    metadata=BenchmarkMetadata(
                        implementations=acknowledged,
                        dialect=dialect,
                        num_runs=self._num_runs,
                        num_loops=self._num_loops,
                        num_values=self._num_values,
                        num_warmups=self._num_warmups,
                    ),
                ),
                quiet=quiet,
                format=format,
                progress_bar=progress,
            )
            reporter.started()
            reporter.report_incompatible_connectables(
                incompatible_connectables,
                dialect,
            )

            if not compatible_connectables:
                reporter.no_compatible_connectables()
                return
            some_benchmark_ran = False
            some_benchmark_ran_successfully = False
            for benchmark_group in self._benchmark_groups:
                if dialect not in benchmark_group.dialects_supported:
                    if not quiet:
                        STDOUT.log(
                            f"Skipping Benchmark Group: {benchmark_group.name}"
                            f" as it does not support dialect"
                            f" {dialect.serializable()}",
                        )
                    continue
                (
                    benchmark_started,
                    benchmark_group_finished,
                ) = reporter.running_benchmark_group(
                    benchmark_group,
                )
                for benchmark in benchmark_group.benchmarks:
                    if benchmark.dialect and benchmark.dialect != dialect:
                        if not quiet:
                            STDOUT.log(
                                f"Skipping {benchmark.name} as it does not "
                                f"support dialect {dialect.serializable()}",
                            )
                        continue
                    test_started, benchmark_finished = benchmark_started(
                        benchmark.name,
                        benchmark.description,
                    )
                    tests = benchmark.tests
                    for test in tests:
                        (
                            got_connectable_result,
                            test_finished,
                        ) = test_started(test.description)
                        benchmark_case = benchmark.benchmark_with_diff_tests(
                            tests=[test],
                        )
                        for connectable in compatible_connectables:
                            run_needed, retries_allowed = (
                                True,
                                self._num_retries,
                            )
                            output = ""
                            while run_needed:
                                with tempfile.NamedTemporaryFile(
                                    delete=True,
                                ) as fp:
                                    try:
                                        output = await self._run_benchmark(
                                            benchmark_case,
                                            dialect,
                                            connectable,
                                            fp.name,
                                        )
                                    except BowtieRunError as err:
                                        got_connectable_result(
                                            connectable.to_terse(),
                                            "Errored",
                                            0,
                                            [1e9]
                                            * self._num_runs
                                            * self._num_values,
                                            errored=True,
                                        )
                                        if not quiet:
                                            STDOUT.log(err)

                                        run_needed = False
                                        some_benchmark_ran = True

                                    if run_needed:
                                        lines = (
                                            Path(
                                                fp.name,
                                            )
                                            .read_text()
                                            .splitlines()
                                        )

                                        measured_time_values = [
                                            float(line) / 1e9 for line in lines
                                        ]

                                        run_needed = got_connectable_result(
                                            connectable.to_terse(),
                                            output,
                                            retries_allowed,
                                            measured_time_values,
                                        )

                                        some_benchmark_ran = True
                                        some_benchmark_ran_successfully = True

                                        if not retries_allowed:
                                            run_needed = False

                                        if run_needed:
                                            retries_allowed -= 1

                        test_finished()

                    benchmark_finished()

                benchmark_group_finished()

            if not some_benchmark_ran and not quiet:
                STDOUT.log("No Benchmark ran.")

            if not some_benchmark_ran_successfully:
                raise BowtieRunError("No Benchmark Ran Successfully!", None)

            reporter.finished()

    async def _run_benchmark(
        self,
        benchmark: Benchmark,
        dialect: Dialect,
        connectable: Connectable,
        time_output_file: str,
    ) -> Any:
        benchmark_name = f"{benchmark.name}::{benchmark.tests[0].description}"

        benchmark_dict = benchmark.serializable()
        benchmark_dict["schema"]["$schema"] = str(dialect.uri)
        if "name" in benchmark_dict:
            benchmark_dict.pop("name")

        if "dialect" in benchmark_dict:
            benchmark_dict.pop("dialect")

        with tempfile.NamedTemporaryFile(
            delete=True,
        ) as fp:
            path = Path(fp.name)
            path.write_text(json.dumps(benchmark_dict))
            return await self._pyperf_benchmark_command(
                "bowtie",
                "run",
                "-i",
                connectable.to_terse(),
                "-D",
                dialect.serializable(),
                fp.name,
                time_output_file=time_output_file,
                connectable_id=connectable.to_terse(),
                name=benchmark_name,
            )

    @staticmethod
    async def _run_subprocess(
        *cmd: str,
        env: dict[str, Any] = {},
    ):
        env = {**os.environ, **env}
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await process.communicate()
        return stdout, stderr

    async def _pyperf_benchmark_command(
        self,
        *benchmark_cmd: str,
        time_output_file: str,
        connectable_id: ConnectableId,
        name: str,
    ):
        stdout_fd = "1"

        output, err = await self._run_subprocess(
            "pyperf",
            "command",
            "--pipe",
            stdout_fd,
            "--copy-env",
            "--processes",
            str(self._num_runs),
            "--values",
            str(self._num_values),
            "--warmups",
            str(self._num_warmups),
            "--loops",
            str(self._num_loops),
            "--name",
            name,
            *benchmark_cmd,
            env={
                "TIME_OUTPUT_FILE": time_output_file,
            },
        )
        if err:
            _, inner_err = await self._run_subprocess(
                *benchmark_cmd,
            )
            if inner_err:
                raise BowtieRunError(inner_err.decode(), connectable_id)
            raise PyperfError(err.decode())

        return output
