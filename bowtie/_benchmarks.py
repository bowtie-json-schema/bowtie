from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from statistics import geometric_mean
from typing import TYPE_CHECKING, Any
import asyncio
import importlib
import importlib.metadata
import json
import statistics
import subprocess
import tempfile

from attrs import asdict, field, frozen
from attrs.filters import exclude
from diagnostic import DiagnosticError
from rich import box
from rich.console import Console
from rich.table import Column, Table
import pyperf  # type: ignore[reportMissingTypeStubs]

from bowtie import _connectables, _report
from bowtie._core import Dialect, Example, ImplementationInfo, Test

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from bowtie._commands import (
        Message,
    )
    from bowtie._connectables import ConnectableId, Connectable
    from bowtie._registry import ValidatorRegistry

Seq = int | str

Benchmark_Group_Name = str
Benchmark_Criteria = str

STDOUT = Console()
STDERR = Console(stderr=True)


@frozen
class BenchmarkLoadError(Exception):
    message: str | None = None

    def __rich__(self):
        return DiagnosticError(
            code="benchmark-load-error",
            message=self.message,
            causes=[],
            hint_stmt=(
                "Make sure that the benchmarks are present "
                "in the appropriate folder."
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
            )
        )


@frozen
class BowtieRunError(BenchmarkError):
    """
    Some Error with Bowtie while running the Benchmark.
    """

    error_stack: str
    connectable_id: ConnectableId

    def __rich__(self):
        return DiagnosticError(
            code="bowtie-benchmark-error",
            message="Bowtie Run command failed while running the Benchmark.",
            note_stmt=self.error_stack,
            causes=[],
            hint_stmt=(
                "Some internal error has occured while running the Benchmark"
                f"with {self.connectable_id}. (Probably some error with the harness)"
            ),
        )


def _get_benchmark_groups_from_folder(
    folder: Path,
    module: str = "bowtie.benchmarks",
) -> Iterable[BenchmarkGroup]:
    for file in folder.iterdir():
        data = None
        if file.suffix == ".py" and file.name != "__init__.py":
            benchmark_module_name = "." + file.stem
            data = importlib.import_module(
                benchmark_module_name,
                module,
            ).get_benchmark()
        elif file.suffix == ".json":
            data = json.loads(file.read_text())

        if data and "benchmarks" not in data:
            benchmark = Benchmark.from_dict(
                **data,
            ).maybe_set_dialect_from_schema()
            benchmark_group = BenchmarkGroup(name=benchmark.name, description=benchmark.description,
                                             benchmarks=[benchmark], path=file)
            yield benchmark_group
        elif data:
            benchmarks = [
                Benchmark.from_dict(
                    **benchmark,
                ).maybe_set_dialect_from_schema()
                for benchmark in data["benchmarks"]
            ]
            benchmark_group = BenchmarkGroup(
                name=data["name"],
                description=data["description"],
                benchmarks=benchmarks,
                path=file,
            )
            yield benchmark_group
        continue


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
        benchmark["dialect"] = Dialect.from_str(dialect_from_schema)  # type: ignore[reportUnknownArgumentType]
        return Benchmark.from_dict(**benchmark)


@frozen
class BenchmarkGroup:
    name: str
    benchmarks: Sequence[Benchmark]
    description: str
    path: Path


@frozen
class BenchmarkGroupResult:
    name: str
    description: str
    benchmark_results: list[BenchmarkResult]

    def serializable(self):
        return asdict(self)


@frozen
class BenchmarkResult:
    name: str
    description: str
    test_results: Sequence[TestResult]

    def serializable(self):
        return asdict(self)


@frozen
class TestResult:
    description: str
    connectable_results: Sequence[ConnectableResult | None]

    def serializable(self):
        return asdict(self)


@frozen
class ConnectableResult:
    connectable_id: ConnectableId
    duration: float
    values: list[float]

    def serializable(self):
        return asdict(self)


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
    system_metadata: dict[str, Any] = field(factory=dict, repr=False)

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
            # FIXME: This transformation is to support the UI parsing
            implementations={
                id: implementation.serializable()
                for id, implementation in self.implementations.items()
            },
        )
        return as_dict


@frozen
class BenchmarkReport:
    metadata: BenchmarkMetadata
    results: dict[Benchmark_Group_Name, BenchmarkGroupResult] = field(
        default={},
    )

    def serializable(self):
        as_dict = dict(metadata=self.metadata.serializable())
        as_dict["results"] = [
            benchmark_group_result.serializable()
            for benchmark_group, benchmark_group_result in self.results.items()
        ]
        return as_dict


@frozen
class BenchmarkReporter:
    _report: BenchmarkReport = field(alias="report")

    _quiet: bool = field(default=False)
    _format: str = field(default="pretty")
    _benchmark_group_path: dict[str, Path] = field(
        default={},
    )

    def update_system_metadata(self, system_metadata: dict[str, Any]):
        system_metadata.pop("command")
        system_metadata.pop("name")
        self._report.metadata.system_metadata.update(system_metadata)

    def started(self):
        if not self._quiet:
            STDOUT.print("Benchmarking Process Started\n")

    @staticmethod
    def report_incompatible_connectables(incompatible_connectables: Sequence[Connectable], dialect: Dialect):
        for connectable in incompatible_connectables:
            STDERR.print(f"{connectable.to_terse()} does not supports dialect {dialect.serializable()}\n")

    def running_benchmark_group(
        self,
        benchmark_group_name: str,
        benchmark_group_description: str,
        path: Path,
    ):
        benchmark_results = []
        self._benchmark_group_path[benchmark_group_name] = path

        if not self._quiet:
            STDOUT.print(f"Benchmark Group - {benchmark_group_name}\n")

        def benchmark_started(benchmark_name: str, benchmark_description: str):
            test_results = []
            if not self._quiet:
                STDOUT.print(f"Running Benchmark - {benchmark_name}\n")

            def test_started(test_description):
                if not self._quiet:
                    STDOUT.print(f"Test - {test_description}")
                connectable_results = []

                def got_connectable_result(
                    connectable: ConnectableId,
                    test_result,
                ):
                    if not self._quiet:
                        if not test_result:
                            STDERR.print(f"Failed Test for - {connectable}")
                            # connectable_results.append(None)
                            # return
                        else:
                            STDOUT.print(f"Got Result for - {connectable}")

                    benchmark_result = pyperf.Benchmark.loads(test_result)
                    connectable_result = ConnectableResult(
                        connectable_id=connectable,
                        duration=benchmark_result.get_total_duration(),
                        values=benchmark_result.get_values(),
                    )
                    if not len(self._report.metadata.system_metadata):
                        self.update_system_metadata(benchmark_result.get_metadata())
                    connectable_results.append(connectable_result)

                def test_finished():
                    test_result = TestResult(
                        description=test_description,
                        connectable_results=connectable_results,
                    )
                    test_results.append(test_result)

                return got_connectable_result, test_finished

            def benchmark_finished():
                if not self._quiet:
                    STDOUT.print()
                benchmark_result = BenchmarkResult(
                    name=benchmark_name,
                    description=benchmark_description,
                    test_results=test_results,
                )
                benchmark_results.append(benchmark_result)

            return test_started, benchmark_finished

        def benchmark_group_finished():
            if not self._quiet:
                STDOUT.print()
            benchmark_group_result = BenchmarkGroupResult(
                name=benchmark_group_name,
                description=benchmark_group_description,
                benchmark_results=benchmark_results,
            )
            self._report.results[benchmark_group_name] = benchmark_group_result

        return benchmark_started, benchmark_group_finished

    def finished(self):
        if self._format == "pretty":
            self._print_results_table()
        else:
            STDOUT.print(json.dumps(self._report.serializable(), indent=2))

    @staticmethod
    def no_compatible_connectables():
        STDERR.print("Skipping Benchmark, No Connectables to run !")

    def _print_results_table(self):

        def _format_value(value: float) -> str:
            if value < 1:
                return f"{round(value * 1000)}ms"
            return f"{round(value, 2)}s"

        console = Console()
        table_caption = (
            f"Benchmark Metadata\n\n"
            f"Runs: {self._report.metadata.num_runs}\n"
            f"Values: {self._report.metadata.num_values}\n"
            f"Warmups: {self._report.metadata.num_warmups}\n\n"
            f"{'CPU Count: '}{self._report.metadata.system_metadata.get('cpu_count', 'Not Available')}\n"
            f"{'CPU Frequency: '}{self._report.metadata.system_metadata.get('cpu_freq', 'Not Available')}\n"
            f"{'CPU Model: '}{self._report.metadata.system_metadata.get('cpu_model_name', 'Not Available')}\n\n"
            f"Hostname: {self._report.metadata.system_metadata['hostname']}\n"
        )

        table = Table(
            Column(header="Benchmark Group", vertical="middle", justify="center"),
            Column(header="Results", justify="center"),
            title="Benchmark",
            caption=table_caption,
        )

        for benchmark_group_name, benchmark_group_result in self._report.results.items():
            benchmark_group_path = self._benchmark_group_path[benchmark_group_name]
            outer_table = Table(
                box=box.SIMPLE_HEAD,
                caption='File "' +str(benchmark_group_path) + '"',
            )
            for benchmark_result in benchmark_group_result.benchmark_results:
                inner_table = Table(
                    "Test Name",
                    box=box.SIMPLE_HEAD,
                    title=benchmark_result.name,
                    min_width=100,
                )

                ref_row = [""]
                results_for_connectable: dict[
                    ConnectableId, list[tuple[float, float]]
                ] = {}

                for idx, connectable_result in enumerate(
                    benchmark_result.test_results[0].connectable_results,
                ):
                    connectable_results = [
                        (
                            statistics.mean(
                                test_result.connectable_results[idx].values,
                            ),
                            statistics.stdev(
                                test_result.connectable_results[idx].values,
                            ),
                        ) for test_result in benchmark_result.test_results
                    ]
                    results_for_connectable[connectable_result.connectable_id] = connectable_results

                sorted_connectables = sorted(
                    results_for_connectable.keys(), key=(
                        lambda connectable_id: (
                            geometric_mean((
                                result_mean
                                for result_mean, _ in results_for_connectable[connectable_id]
                            ))
                        )
                    ),
                )
                results_for_connectable = {
                    connectable: results_for_connectable[connectable] for connectable in sorted_connectables
                }

                for connectable_id, connectable_results in results_for_connectable.items():
                    inner_table.add_column(
                        connectable_id,
                    )
                    ref_row.append(
                        geometric_mean((
                            result_mean for result_mean, _ in connectable_results
                        )),
                    )

                fastest_connectable_results = next(iter(results_for_connectable.values()))

                for idx, test_result in enumerate(benchmark_result.test_results):
                    row_elements = [
                        test_result.description,
                    ]
                    for connectable_idx, results in enumerate(results_for_connectable.items()):
                        _, connectable_results = results
                        _mean, std_dev = connectable_results[idx]

                        fastest_implementation_mean, _ = fastest_connectable_results[idx]
                        relative = _mean / fastest_implementation_mean

                        repr_string = f"{_format_value(_mean)} +- {_format_value(std_dev)}"
                        if connectable_idx != 0 and relative > 1:
                            repr_string += f": {round(relative, 2)}x slower"
                        elif connectable_idx:
                            repr_string += f": {round(1 / relative, 2)}x faster"

                        row_elements.append(repr_string)

                    inner_table.add_row(*row_elements)

                for implementation_idx in range(2, len(ref_row)):
                    ref_row[implementation_idx] = (
                        f"{round(ref_row[implementation_idx] / ref_row[1], 2)}x slower"
                    )

                ref_row[1] = "Reference"
                inner_table.add_section()
                if len(results_for_connectable) > 1:
                    inner_table.add_row(*ref_row)
                outer_table.add_row(inner_table)
            if len(benchmark_group_result.benchmark_results) > 0:
                table.add_row(
                    benchmark_group_name,
                    outer_table,
                )

        console.print()
        console.print(table)


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

    @classmethod
    def from_default_benchmarks(cls, **kwargs: Any):
        bowtie_dir = Path(__file__).parent
        benchmark_dir = bowtie_dir.joinpath("benchmarks")

        if not benchmark_dir.exists():
            raise BenchmarkLoadError("Default Benchmarks not found.")

        return cls(
            benchmark_groups=_get_benchmark_groups_from_folder(
                benchmark_dir,
            ),
            **kwargs,
        )

    @classmethod
    def for_keywords(cls, dialect: Dialect, **kwargs: Any):
        bowtie_dir = Path(__file__).parent
        keywords_benchmark_dir = bowtie_dir.joinpath("benchmarks").joinpath("keywords")
        dialect_keyword_benchmarks_dir = keywords_benchmark_dir.joinpath(dialect.short_name)

        if not keywords_benchmark_dir.exists():
            raise BenchmarkLoadError("Keyword Benchmarks Folder not found.")
        if not dialect_keyword_benchmarks_dir.exists():
            raise BenchmarkLoadError(
                message=(
                    f"Keyword Specific Benchmarks not present for {dialect.serializable()}"
                )
            )

        module_name = f"bowtie.benchmarks.keywords.{dialect.short_name}"

        return cls(
            benchmark_groups=_get_benchmark_groups_from_folder(
                dialect_keyword_benchmarks_dir,
                module=module_name,
            ),
            **kwargs,
        )

    @classmethod
    def from_input(
        cls,
        schema: Any,
        instances: Iterable[Any],
        description: str,
        **kwargs: Any,
    ):
        tests = [
            Example(description=str(idx), instance=each)
            for idx, each in enumerate(instances)
        ]
        benchmarks = [
            Benchmark(
                name=description,
                description=description,
                tests=tests,
                schema=schema,
            ),
        ]
        benchmark_group = BenchmarkGroup(
            name=description,
            description=description,
            benchmarks=benchmarks,
            path=None,
        )
        return cls(benchmark_groups=[benchmark_group], **kwargs)

    async def start(
        self,
        connectables: Iterable[_connectables.Connectable],
        dialect: Dialect,
        quiet: bool,
        registry: ValidatorRegistry[Any],
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
                registry=registry,
            ) as implementation:
                if dialect not in implementation.info.dialects:
                    incompatible_connectables.append(connectable)
                    continue

                acknowledged[connectable.to_terse()] = implementation.info
                compatible_connectables.append(connectable)

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
        )
        reporter.started()
        reporter.report_incompatible_connectables(incompatible_connectables, dialect)

        if not compatible_connectables:
            reporter.no_compatible_connectables()
            return

        for benchmark_group in self._benchmark_groups:
            benchmark_started, benchmark_group_finished = reporter.running_benchmark_group(
                benchmark_group.name,
                benchmark_group.description,
                benchmark_group.path,
            )
            for benchmark in benchmark_group.benchmarks:
                test_started, benchmark_finished = benchmark_started(benchmark.name, benchmark.description)
                if benchmark.dialect and benchmark.dialect != dialect:
                    STDERR.print(f"Skipping {benchmark.name} as it does not support dialect {dialect.serializable()}")
                    continue
                tests = benchmark.tests
                for test in tests:
                    got_connectable_result, test_finished = test_started(test.description)
                    benchmark_case = benchmark.benchmark_with_diff_tests(
                        tests=[test],
                    )
                    for connectable in compatible_connectables:
                        try:
                            output = await self._run_benchmark(
                                benchmark_case,
                                dialect,
                                connectable,
                            )
                        except (PyperfError, BowtieRunError) as err:
                            STDERR.print(err)
                            return

                        got_connectable_result(connectable.to_terse(), output)

                    test_finished()

                benchmark_finished()

            benchmark_group_finished()

        reporter.finished()

    async def _run_benchmark(
        self,
        benchmark: Benchmark,
        dialect: Dialect,
        connectable: _connectables.Connectable,
    ) -> Any:
        benchmark_name = f"{benchmark.name}::{benchmark.tests[0].description}"

        benchmark_dict = benchmark.serializable()
        benchmark_dict.pop("name")

        if "dialect" in benchmark_dict:
            benchmark_dict.pop("dialect")

        with tempfile.NamedTemporaryFile(
            delete=True,
        ) as fp:
            path = Path(fp.name)
            path.write_text(json.dumps(benchmark_dict))
            output = await self._pyperf_benchmark_command(
                "bowtie", "run", "-i", connectable.to_terse(),
                "-D", dialect.serializable(),
                fp.name,
                connectable_id=connectable.to_terse(),
                name=benchmark_name,
            )

        return output

    @staticmethod
    async def _run_subprocess(
        *cmd: str,
    ):
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return stdout, stderr

    async def _pyperf_benchmark_command(
        self,
        *benchmark_cmd: str,
        connectable_id: ConnectableId,
        name: str,
    ):
        stdout_fd = "1"

        output, err = await self._run_subprocess(
            "pyperf", "command",
            "--pipe", stdout_fd,
            "--processes", str(self._num_runs),
            "--values", str(self._num_values),
            "--warmups", str(self._num_warmups),
            "--loops", str(self._num_loops),
            "--name", name,
            *benchmark_cmd,
        )
        if err:
            _, inner_err = await self._run_subprocess(
                *benchmark_cmd,
            )
            if inner_err:
                raise BowtieRunError(inner_err.decode(), connectable_id)
            raise PyperfError(err.decode())

        return output