"""
An interactive TUI for evaluating JSON Schema across implementations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import asyncio
import json

from rich.panel import Panel
from rich.table import Table

from bowtie._commands import SeqCase
from bowtie._core import Dialect, Example, TestCase

if TYPE_CHECKING:
    from collections.abc import Callable

    from rich.console import Console

    from bowtie._core import DialectRunner

_QUIT = {"q", "quit", "exit"}

_SINGLE = 0


class TuiSession:
    """
    An interactive TUI session over a set of running implementations.

    Keeps DialectRunners alive across multiple validate calls.
    Accepts injected I/O so the session logic is testable without a terminal.
    """

    def __init__(
        self,
        runners: list[tuple[str, str, DialectRunner]],
        dialect: Dialect,
        console: Console,
        prompt: Callable[[str], str],
    ) -> None:
        self._runners = runners
        self._dialect = dialect
        self._console = console
        self._prompt = prompt
        self._seq = 0

    async def run_once(
        self,
        schema: Any,
        instance: Any,
    ) -> list[tuple[str, str, bool | None]]:
        """
        Validate one instance against one schema across all runners.
        """
        self._seq += 1
        case = TestCase(
            description="bowtie tui",
            schema=schema,
            tests=[Example(description="", instance=instance)],
        )
        seq_case = SeqCase(seq=self._seq, case=case)

        tasks = [seq_case.run(runner=runner) for _, _, runner in self._runners]

        raw_results = await asyncio.gather(*tasks)

        output = []
        for (impl_id, version, _), seq_result in zip(
                self._runners, raw_results,
            ):
            test_result = seq_result.result_for(_SINGLE)
            if test_result.errored or test_result.skipped:
                valid = None
            else:
                valid = test_result.valid # type: ignore[reportUnknownMemberType]
            output.append((impl_id, version, valid))
        return output

    def show_results(
        self,
        results: list[tuple[str, str, bool | None]],
    ) -> None:
        table = Table(show_header=True, header_style="bold")
        table.add_column("Implementation")
        table.add_column("Version", style="dim")
        table.add_column("Result")

        for impl_id, version, valid in results:
            if valid is True:
                result_str = "[green] valid[/green]"
            elif valid is False:
                result_str = "[red] invalid[/red]"
            else:
                result_str = "[yellow] error[/yellow]"
            table.add_row(impl_id, version, result_str)

        self._console.print()
        self._console.print(table)

    async def repl(self) -> None:
        """
        Main loop: prompt for schema and instance, validate, display, repeat.
        """
        impl_count = len(self._runners)
        impl_word = "implementation" if impl_count == 1 else "implementations"

        self._console.print(
            Panel(
                f"Dialect: [bold]{self._dialect.pretty_name}[/bold]  "
                f"Running: [bold]{impl_count}[/bold] {impl_word}\n\n"
                "[dim]Enter a JSON schema, then one instance to validate.\n"
                "Type [bold]q[/bold] to quit.[/dim]",
                title="bowtie tui",
            ),
        )

        while True:
            try:
                raw_schema = self._prompt("Schema")
            except (KeyboardInterrupt, EOFError):
                break
            if raw_schema.strip().lower() in _QUIT:
                break
            try:
                schema = _parse_json(raw_schema)
            except ValueError as e:
                self._console.print(
                    f"[red]Invalid JSON for schema: {e}[/red]",
                )
                continue

            if not _is_schema_like(schema):
                self._console.print(
                    "[red]Schemas must be a JSON object or boolean "
                    f"(got {type(schema).__name__}).[/red]",
                )
                continue

            try:
                raw_instance = self._prompt("Instance")
            except (KeyboardInterrupt, EOFError):
                break
            if raw_instance.strip().lower() in _QUIT:
                break
            try:
                instance = _parse_json(raw_instance)
            except ValueError as e:
                self._console.print(
                    f"[red]Invalid JSON for instance: {e}[/red]",
                )
                continue

            results = await self.run_once(schema=schema, instance=instance)
            self.show_results(results=results)


def _parse_json(raw: str) -> Any:
    """
    Parse a JSON string, raising ValueError with a clean message on failure.
    """
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(str(e)) from e


def _is_schema_like(value: Any) -> bool:
    return isinstance(value, (dict, bool))
