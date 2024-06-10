from __future__ import annotations

import os, pyperf
from typing import Callable

from attrs import field, frozen, asdict

from time import perf_counter_ns
from collections.abc import Iterable, Sequence
from pathlib import Path
import importlib, json, subprocess, asyncio
from typing import Any

from referencing.jsonschema import SchemaResource

from bowtie import _report
from bowtie._core import TestCase, Example, Test, Dialect
from bowtie._report import RunMetadata
from bowtie._commands import (
    Message,
)

BENCHMARKS_MODULE = "bowtie.benchmarks"


def get_default_benchmarks() -> Iterable[dict[str, Any]]:
    bowtie_dir = Path(__file__).parent
    benchmark_dir = bowtie_dir.joinpath("benchmarks").iterdir()

    for file in benchmark_dir:
        if file.suffix == ".py" and file.name != '__init__.py':
            benchmark_module_name = "." + file.stem
            benchmark = importlib.import_module(
                benchmark_module_name,
                BENCHMARKS_MODULE
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
        as_dict = asdict(
            self,
            filter=lambda _, v: v is not None,
        )
        return as_dict

    def benchmark_with_diff_tests(self, tests):
        benchmark = self.serializable()
        benchmark['tests'] = tests
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
        benchmark['dialect'] = Dialect.from_str(dialect_from_schema)
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
    def from_default_benchmarks(cls, **kwargs):
        benchmarks = [
            Benchmark.from_dict(
                **benchmark,
            ).maybe_set_dialect_from_schema()
            for benchmark in get_default_benchmarks()
        ]
        return cls(benchmarks=benchmarks, **kwargs)

    @classmethod
    def from_input(cls, schema, instances, description, **kwargs):
        tests = [Example(description=str(idx), instance=each) for idx, each in enumerate(instances)]
        benchmarks = [Benchmark(name=description, description=description, tests=tests, schema=schema)]
        return cls(benchmarks=benchmarks, **kwargs)

    async def start(
            self,
            connectables,
            dialect,
    ):
        bench_suites = []
        for connectable in connectables:

            silent_reporter = _report.Reporter(write=lambda **_: None)
            async with connectable.connect(
                    reporter=silent_reporter,
                    make_validator=self._do_not_validate,
            ) as implementation:
                supports_dialect = dialect in implementation.info.dialects

            if not supports_dialect:
                print(f"{connectable.to_terse()} does not supports dialect {dialect.serializable()}")
                continue

            print(connectable.to_terse())
            print()

            benchmark_results = []
            for benchmark in self._benchmarks:
                if benchmark.dialect and benchmark.dialect != dialect:
                    print(f"Skipping {benchmark.name} as it does not support dialect {dialect.serializable()}")
                    continue
                tests = benchmark.tests
                for test in tests:
                    benchmark_case = benchmark.benchmark_with_diff_tests(tests=[test])
                    bench = await self._run_benchmark(
                        benchmark_case,
                        dialect,
                        connectable,
                    )
                    if bench:
                        benchmark_results.append(bench)
            if len(benchmark_results):
                benchmark_suite = pyperf.BenchmarkSuite(benchmarks=benchmark_results)
                benchmark_suite.dump(f"/tmp/{connectable.to_terse()}.json")
                bench_suites.append(f"/tmp/{connectable.to_terse()}.json")

            print()

        await self._pyperf_compare_command(*bench_suites)
        self._delete_bench_suites_if_any(bench_suites)

    async def _run_benchmark(self, benchmark, dialect, connectable):
        start = perf_counter_ns()
        benchmark_name = f"{benchmark.name}  ::  {benchmark.tests[0].description}"

        tmp_file = f"/tmp/{benchmark_name}"
        benchmark_dict = benchmark.serializable()
        benchmark_dict.pop("name")
        if 'dialect' in benchmark_dict:
            benchmark_dict.pop("dialect")

        with open(tmp_file, "w") as file:
            json.dump(benchmark_dict, file)
        try:
            output = await self._pyperf_benchmark_command(
                "bowtie", "run", "-i", connectable.to_terse(),
                "-D", dialect.serializable(),
                tmp_file,
                name=benchmark_name,
            )
        except:
            print('err')
            return None, 0

        bench = pyperf.Benchmark.loads(output)
        os.remove(tmp_file)
        end = (perf_counter_ns() - start) / 1e9
        print(f"Running Benchmark - {benchmark_name}")
        return bench

    async def _run_subprocess(self, *cmd):
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return stdout, stderr

    async def _pyperf_benchmark_command(
            self,
            *benchmark_cmd,
            name,
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
                *benchmark_cmd
            )
            if inner_err:
                print(inner_err)
            else:
                print(err)
            raise Exception
        return output

    async def _pyperf_compare_command(self, *benchmark_suites):
        output, err = await self._run_subprocess(
            "pyperf", "compare_to",
            "--table",
            "--table-format", "md",
            *benchmark_suites,
        )
        print(output.decode())

    @staticmethod
    def _do_not_validate(*ignored: SchemaResource) -> Callable[..., None]:
        return lambda *args, **kwargs: None

    @staticmethod
    def _delete_bench_suites_if_any(bench_suites):
        for bench_suite in bench_suites:
            if os.path.isfile(bench_suite):
                os.remove(bench_suite)
