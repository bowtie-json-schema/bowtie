from __future__ import annotations

from pathlib import Path
from statistics import geometric_mean
from typing import TYPE_CHECKING, Any
import asyncio
import importlib
import json
import os
import subprocess
import tempfile

from attrs import asdict, field, frozen
import pyperf  # type: ignore[reportMissingTypeStubs]

from bowtie import _connectables, _report
from bowtie._core import Dialect, Example, Test

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from bowtie._commands import (
        Message,
    )
    from bowtie._registry import ValidatorRegistry

BENCHMARKS_MODULE = "bowtie.benchmarks"


def get_default_benchmarks() -> Iterable[dict[str, Any]]:
    bowtie_dir = Path(__file__).parent
    benchmark_dir = bowtie_dir.joinpath("benchmarks").iterdir()

    for file in benchmark_dir:
        if file.suffix == ".py" and file.name != "__init__.py":
            benchmark_module_name = "." + file.stem
            benchmark = importlib.import_module(
                benchmark_module_name,
                BENCHMARKS_MODULE,
            ).get_benchmark()
        elif file.suffix == ".json":
            benchmark = json.loads(file.read_text())
        else:
            continue
        yield benchmark


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
class BenchmarkReport:
    pass
    # metadata: RunMetadata


@frozen
class Benchmarker:
    _benchmarks: Sequence[Benchmark] = field(alias="benchmarks")
    _num_processes: int = field(
        alias="processes",
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
    _report: BenchmarkReport = field(
        alias="report",
        default=BenchmarkReport(),
    )

    @classmethod
    def from_default_benchmarks(cls, **kwargs: Any):
        benchmarks = [
            Benchmark.from_dict(
                **benchmark,
            ).maybe_set_dialect_from_schema()
            for benchmark in get_default_benchmarks()
        ]
        return cls(benchmarks=benchmarks, **kwargs)

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
        return cls(benchmarks=benchmarks, **kwargs)

    async def start(
        self,
        connectables: Iterable[_connectables.Connectable],
        dialect: Dialect,
        registry: ValidatorRegistry[Any],
    ):
        bench_suite_for_connectable: dict[str, pyperf.BenchmarkSuite] = {}
        for connectable in connectables:

            silent_reporter = _report.Reporter(
                write=lambda **_: None,  # type: ignore[reportUnknownArgumentType]
            )
            async with connectable.connect(
                reporter=silent_reporter,
                registry=registry,
            ) as implementation:
                supports_dialect = dialect in implementation.info.dialects

            if not supports_dialect:
                print(f"{connectable.to_terse()} does not supports dialect {dialect.serializable()}")
                continue

            print(connectable.to_terse())
            print()

            benchmark_results: list[pyperf.Benchmark] = []
            for benchmark in self._benchmarks:
                if benchmark.dialect and benchmark.dialect != dialect:
                    print(f"Skipping {benchmark.name} as it does not support dialect {dialect.serializable()}")
                    continue
                tests = benchmark.tests
                for test in tests:
                    benchmark_case = benchmark.benchmark_with_diff_tests(
                        tests=[test],
                    )
                    bench = await self._run_benchmark(
                        benchmark_case,
                        dialect,
                        connectable,
                    )
                    if bench:
                        benchmark_results.append(bench)
            if len(benchmark_results):
                benchmark_suite = pyperf.BenchmarkSuite(
                    benchmarks=benchmark_results,
                )
                bench_suite_for_connectable[
                    connectable.to_terse()
                ] = benchmark_suite

            print()

        bench_suite_for_connectable = self._sort_benchmark_suites(
            bench_suite_for_connectable,
        )
        await self._compare_benchmark_suites(bench_suite_for_connectable)

    async def _compare_benchmark_suites(
        self,
        bench_suite_for_connectable: dict[str, pyperf.BenchmarkSuite],
    ):
        with tempfile.TemporaryDirectory(
            delete=True,
        ) as tmp_dir_path:
            benchmark_suite_filenames: list[str] = []
            for (
                    connectable_name,
                    bench_suite,
            ) in bench_suite_for_connectable.items():
                bench_suite_tmp_filename = os.path.join(tmp_dir_path, f"{connectable_name}.json")
                bench_suite.dump(bench_suite_tmp_filename)  # type: ignore[reportUnknownMemberType]
                benchmark_suite_filenames.append(bench_suite_tmp_filename)

            await self._pyperf_compare_command(*benchmark_suite_filenames)

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
            with open(fp.name, "w") as file:
                json.dump(benchmark_dict, file)
            try:
                output = await self._pyperf_benchmark_command(
                    "bowtie", "run", "-i", connectable.to_terse(),
                    "-D", dialect.serializable(),
                    fp.name,
                    name=benchmark_name,
                )
            except:
                print('err')
                return None

        bench = pyperf.Benchmark.loads(output)  # type: ignore[reportUnknownArgumentType]
        print(f"Running Benchmark - {benchmark_name}")
        return bench  # type: ignore[reportUnknownVariableType]

    async def _run_subprocess(
        self,
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
            "--processes", str(self._num_processes),
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

    async def _pyperf_compare_command(self, *benchmark_suite_filenames: str):
        output, err = await self._run_subprocess(
            "pyperf", "compare_to",
            "--table",
            "--table-format", "md",
            *benchmark_suite_filenames,
        )
        if err:
            print(err)
        print(output.decode())

    @staticmethod
    def _sort_benchmark_suites(
        bench_suite_for_connectable: dict[str, pyperf.BenchmarkSuite],
    ) -> dict[str, pyperf.BenchmarkSuite]:

        def _geometric_mean_of_bench_suite(bench_suite: pyperf.BenchmarkSuite):
            means = [b.mean() for b in bench_suite.get_benchmarks()]  # type: ignore[reportUnknownVariableType]
            return geometric_mean(means)  # type: ignore[reportUnknownArgumentType]

        return dict(sorted(
            bench_suite_for_connectable.items(),
            key=lambda item: _geometric_mean_of_bench_suite(item[1]),
        ))
