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
from rich import box
from rich.console import Console
from rich.table import Column, Table
import pyperf  # type: ignore[reportMissingTypeStubs]
import structlog.stdlib

from bowtie import _connectables, _report
from bowtie._core import Dialect, Example, ImplementationInfo, Test

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence

    from bowtie._commands import (
        Message,
    )
    from bowtie._connectables import ConnectableId
    from bowtie._registry import ValidatorRegistry

Seq = int | str

Benchmark_Group_Name = str
Benchmark_Criteria = str


def _get_benchmark_groups_from_folder(folder, module="bowtie.benchmarks") -> Iterable[BenchmarkGroup]:
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

        if isinstance(data, dict):
            benchmark = Benchmark.from_dict(
                **data,
            ).maybe_set_dialect_from_schema()
            benchmark_group = BenchmarkGroup(name=benchmark.name, description=benchmark.description,
                                             benchmarks=[benchmark], path=file)
            yield benchmark_group
        elif isinstance(data, list):
            benchmarks = [
                Benchmark.from_dict(
                    **benchmark,
                ).maybe_set_dialect_from_schema()
                for benchmark in data
            ]
            benchmark_group = BenchmarkGroup(name=benchmarks[0].name, description="", benchmarks=benchmarks, path=file)
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
class BenchmarkResult:
    name: str
    description: str
    test_results: list[BenchmarkTestResult]


@frozen
class BenchmarkTestResult:
    description: str
    duration: float
    values: list[float]


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
    system_metadata: Mapping[str, Any] = field(factory=dict, repr=False)

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
        return asdict(
            self,
            filter=exclude("dialect", "implementations"),
        )


@frozen
class BenchmarkReporter:
    _metadata: BenchmarkMetadata = field(alias="metadata")

    _log: structlog.stdlib.BoundLogger = field(
        factory=structlog.stdlib.get_logger,
    )
    _quiet: bool = field(default=False)
    _results: dict[
        Benchmark_Group_Name,
        dict[
            str,
            dict[ConnectableId, BenchmarkResult],
        ],
    ] = field(
        alias="results",
        default={},
    )
    _benchmark_group_path: dict[str, Path] = field(
        default={},
    )

    def update_system_metadata_if_needed(self, system_metadata):
        if not len(self._metadata.system_metadata):
            self._metadata.system_metadata.update(system_metadata)

    def started(self):
        if not self._quiet:
            print("Benchmarking Process Started\n")

    def report_incompatible_connectables(self, incompatible_connectables: Sequence[ConnectableId], dialect):
        for connectable in incompatible_connectables:
            print(f"{connectable} does not supports dialect {dialect.serializable()}")
        if len(incompatible_connectables):
            print()

    def running_benchmark_group(self, benchmark_group_name: str, path: Path):
        self._results[benchmark_group_name] = {}
        self._benchmark_group_path[benchmark_group_name] = path

        def running_connectable(connectable: ConnectableId):
            if not self._quiet:
                print(connectable)
                print()

            def benchmark_started(benchmark):
                if benchmark.name not in self._results[benchmark_group_name]:
                    self._results[benchmark_group_name][benchmark.name] = {}

                if not self._quiet:
                    print(f"Running Benchmark - {benchmark.name}\n")

                benchmark_test_results = []

                def got_test_result(test, test_result):
                    if not self._quiet:
                        print(f"Ran Test - {test.tests[0].description}")

                    benchmark_result = pyperf.Benchmark.loads(test_result)  # type: ignore[reportUnknownArgumentType]
                    benchmark_test_result = BenchmarkTestResult(
                        description=test.tests[0].description,
                        duration=benchmark_result.get_total_duration(),
                        values=benchmark_result.get_values(),
                    )
                    benchmark_test_results.append(benchmark_test_result)
                    return benchmark_result

                def benchmark_finished():
                    benchmark_result = BenchmarkResult(
                        name=benchmark.name,
                        description=benchmark.description,
                        test_results=benchmark_test_results,
                    )
                    self._results[benchmark_group_name][benchmark.name][connectable] = benchmark_result

                return got_test_result, benchmark_finished

            return benchmark_started

        return running_connectable

    def finished(self):
        self._print_results_table()

    def no_compatible_connectables(self):
        print("Skipping Benchmark, No Connectables to run !")

    def _sort_results_by_fastest_first(self):
        for benchmark_group, benchmark_results in self._results.items():
            for benchmark_name, implementation_results in benchmark_results.items():
                implementation_names = sorted(
                    implementation_results.keys(), key=(
                        lambda implementation_name: (
                            geometric_mean((
                                statistics.mean(test_result.values)
                                for test_result in implementation_results[implementation_name].test_results
                            ))
                        )
                    )
                )
                benchmark_results[benchmark_name] = {
                    implementation_name: implementation_results[implementation_name]
                    for implementation_name in implementation_names
                }
            self._results[benchmark_group] = benchmark_results

    def _print_results_table(self):

        def _format_value(value):
            if value < 1:
                return f"{round(value * 1000)}ms"
            return f"{round(value, 2)}s"

        group = "groups" if len(self._results) != 1 else "group"
        console = Console()
        table_caption = (
            f"Benchmark Metadata\n\n"
            f"Runs: {self._metadata.num_runs}\n"
            f"Values: {self._metadata.num_values}\n"
            f"Warmups: {self._metadata.num_warmups}\n\n"
            f"CPU Count: {self._metadata.system_metadata['cpu_count']}\n"
            f"CPU Frequency: {self._metadata.system_metadata['cpu_freq']}\n"
            f"CPU Model: {self._metadata.system_metadata['cpu_model_name']}\n\n"
            f"Hostname: {self._metadata.system_metadata['hostname']}\n"
        )

        table = Table(
            Column(header="Benchmark Group", vertical="middle", justify="center"),
            Column(header="Results", justify="center"),
            title="Benchmark",
            caption=table_caption,
        )

        self._sort_results_by_fastest_first()

        for benchmark_group, benchmark_results in self._results.items():
            benchmark_group_path = self._benchmark_group_path[benchmark_group]
            outer_table = Table(
                box=box.SIMPLE_HEAD,
                caption=str(benchmark_group_path),
            )
            for benchmark_name, implementation_results in benchmark_results.items():
                inner_table = Table(
                    benchmark_name,
                    box=box.SIMPLE_HEAD,
                    title=benchmark_name,
                    min_width=100,
                )
                fastest_implementation_name = next(iter(implementation_results))
                ref_row = ["Relative Comparison"]

                for implementation_name, implementation_result in implementation_results.items():
                    inner_table.add_column(
                        implementation_name,
                    )
                    ref_row.append(
                        geometric_mean((
                            statistics.mean(test_result.values)
                            for test_result in implementation_result.test_results
                        ))
                    )

                benchmark_test_names = [
                    test_result.description
                    for test_result in next(
                        iter(implementation_results.values())
                    ).test_results
                ]

                num_benchmark_tests = len(benchmark_test_names)
                fastest_implementation_results = next(iter(implementation_results.values())).test_results

                for idx in range(num_benchmark_tests):
                    row_elements = [
                        benchmark_test_names[idx],
                    ]
                    for num, implementation_result in enumerate(implementation_results.values()):
                        mean = statistics.mean(implementation_result.test_results[idx].values)
                        std_dev = statistics.stdev(implementation_result.test_results[idx].values)

                        fastest_implementation_mean = statistics.mean(fastest_implementation_results[idx].values)
                        relative = mean / fastest_implementation_mean

                        repr_string = f"{_format_value(mean)} +- {_format_value(std_dev)}"
                        if num != 0:
                            repr_string += f": {round(relative, 2)}x slower"

                        row_elements.append(repr_string)

                    inner_table.add_row(*row_elements)

                for implementation_idx in range(2, len(ref_row)):
                    ref_row[implementation_idx] = (
                        f"{round(ref_row[implementation_idx] / ref_row[1], 2)}x slower"
                    )

                ref_row[1] = "Reference"
                inner_table.add_section()
                if len(implementation_results)>1:
                    inner_table.add_row(*ref_row)
                outer_table.add_row(inner_table)

            table.add_row(
                benchmark_group,
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
            path=None
        )
        return cls(benchmark_groups=[benchmark_group], **kwargs)

    async def start(
        self,
        connectables: Iterable[_connectables.Connectable],
        dialect: Dialect,
        quiet: bool,
        registry: ValidatorRegistry[Any],
    ):
        acknowledged: Mapping[ConnectableId, ImplementationInfo] = {}
        compatible_connectables = []
        incompatible_connectables = []

        for connectable in connectables:
            silent_reporter = _report.Reporter(
                write=lambda **_: None,  # type: ignore[reportUnknownArgumentType]
            )
            async with connectable.connect(
                reporter=silent_reporter,
                registry=registry,
            ) as implementation:
                if dialect not in implementation.info.dialects:
                    incompatible_connectables.append(connectable.to_terse())
                    continue

                acknowledged[connectable.to_terse()] = implementation.info
                compatible_connectables.append(connectable)

        reporter = BenchmarkReporter(
            metadata=BenchmarkMetadata(
                implementations=acknowledged,
                dialect=dialect,
                num_runs=self._num_runs,
                num_loops=self._num_loops,
                num_values=self._num_values,
                num_warmups=self._num_warmups,
            ),
            quiet=quiet,
        )
        reporter.started()
        reporter.report_incompatible_connectables(incompatible_connectables, dialect)

        if not compatible_connectables:
            reporter.no_compatible_connectables()
            return

        for benchmark_group in self._benchmark_groups:
            report_running_connectable = reporter.running_benchmark_group(
                benchmark_group.name,
                benchmark_group.path
            )
            for connectable in compatible_connectables:
                report_running_benchmark = report_running_connectable(connectable.to_terse())
                for benchmark in benchmark_group.benchmarks:
                    report_got_test_result, report_benchmark_finished = report_running_benchmark(benchmark)
                    if benchmark.dialect and benchmark.dialect != dialect:
                        print(f"Skipping {benchmark.name} as it does not support dialect {dialect.serializable()}")
                        continue
                    tests = benchmark.tests
                    for test in tests:
                        benchmark_case = benchmark.benchmark_with_diff_tests(
                            tests=[test],
                        )
                        output = await self._run_benchmark(
                            benchmark_case,
                            dialect,
                            connectable,
                        )
                        bench = report_got_test_result(benchmark_case, output)
                        reporter.update_system_metadata_if_needed(bench.get_metadata())

                    report_benchmark_finished()

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
            try:
                output = await self._pyperf_benchmark_command(
                    "bowtie", "run", "-i", connectable.to_terse(),
                    "-D", dialect.serializable(),
                    fp.name,
                    name=benchmark_name,
                )
            except:
                print("err")
                return None

        return output  # type: ignore[reportUnknownVariableType]

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
                print(inner_err)
            else:
                print(err)
            raise Exception
        return output
