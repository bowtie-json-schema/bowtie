"""
Smoke testing of implementations.

Represents a sort of "absolute minimum level of assumed correctness" which we
can use to decide whether a harness is correctly written, even though
implementations may still be buggy / not fully compliant.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from attrs import evolve, field, frozen
from diagnostic import DiagnosticError, DiagnosticWarning
from referencing.jsonschema import EMPTY_REGISTRY
from rpds import HashTrieSet, List

from bowtie._core import Example, Test, TestCase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rich.console import Console, ConsoleOptions, RenderResult

    from bowtie._commands import SeqResult
    from bowtie._core import Dialect, Implementation, ImplementationInfo

EXAMPLES = [
    # FIXME: When horejsek/python-fastjsonschema#181 is merged
    #        and/or we special-case fastjsonschema...
    # Example(description="null", instance=None),  # noqa: ERA001
    Example(description="boolean", instance=True),
    Example(description="integer", instance=37),
    Example(description="number", instance=37.37),
    Example(description="string", instance="37"),
    Example(description="array", instance=[37]),
    Example(description="object", instance={"foo": 37}),
]


async def test(implementation: Implementation):
    result = Result(info=implementation.info)

    for dialect in implementation.info.dialects:
        unsuccessful = await implementation.failing(
            dialect=dialect,
            cases=[
                dialect.top_test_case(EXAMPLES),
                dialect.bottom_test_case(EXAMPLES),
            ],
        )
        if unsuccessful:
            result = result.dialect_failed(dialect, results=unsuccessful)

    last = result.latest_successful_dialect
    if last is not None:  # no point checking $ref for a broken dialect
        # We'd use a tag URI, but the goal is to use literally the simplest
        # possible thing that should work.
        simple_uri = "http://bowtie.report/cli/smoke/ref-to-string"
        resource = last.specification().create_resource({"type": "string"})
        ref_check = TestCase(
            description="$ref / registry support",
            schema={"$ref": simple_uri},
            registry=EMPTY_REGISTRY.with_resource(
                uri=simple_uri,
                resource=resource,
            ),
            tests=[
                Test(description="string", instance="valid", valid=True),
                Test(description="non-string", instance=37, valid=False),
            ],
        )
        unsuccessful = await implementation.failing(
            dialect=last,
            cases=[ref_check],
        )
        if unsuccessful:
            result = result.no_referencing(results=unsuccessful)

    return result


def results_to_causes(
    results: Sequence[tuple[TestCase, SeqResult]],
) -> list[str]:
    # FIXME
    return []


@frozen
class Result:
    """
    The result of smoke testing an implementation.
    """

    _info: ImplementationInfo = field(alias="info")
    _unsuccessful_dialects: HashTrieSet[Dialect] = field(
        default=HashTrieSet(),
        repr=False,
        alias="unsuccessful_dialects",
    )

    errors: List[DiagnosticError] = List()
    warnings: List[DiagnosticWarning] = List()

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.table import Column, Table

        table = Table.grid(
            Column("Label", no_wrap=True, justify="center"),
            Column("Content"),
            padding=(1, 4),
            pad_edge=True,
        )
        table.min_width = 79
        table.title_justify = "left"

        dialects = Table.grid(Column("Dialect", justify="right"))
        for dialect in sorted(self._info.dialects, reverse=True):
            style = "green" if dialect in self.confirmed_dialects else "red"
            dialects.add_row(f"{dialect.pretty_name}", style=style)
        table.add_row("Dialects\n[dim](Confirmed Working)", dialects)

        prefix = f"{self._info.id}[dim] seems to"
        if self.success:
            table.title = f"{prefix} [/][b green]work!"
        elif self.warnings:
            table.title = f"{prefix} be [/][b yellow]broken!"

            warnings = Table.grid(padding=1)
            for warning in self.warnings:
                subtable = Table.grid("Causes", pad_edge=True)
                for cause in warning.causes:
                    subtable.add_row(cause)
                warnings.add_row(warning.message)
                hint = Panel.fit(
                    Markdown(str(warning.hint_stmt)),
                    title="[blue]Hint",
                    padding=(1, 4),
                )
                warnings.add_row(hint)
                warnings.add_row(subtable)
            table.add_row("[yellow]Warnings", warnings)
        else:
            table.title = f"{prefix} be [/][b red]broken!"

            errors = Table.grid(padding=1)
            for error in self.errors:
                subtable = Table.grid("Causes", pad_edge=True)
                for cause in error.causes:
                    subtable.add_row(cause)
                errors.add_row(error.message)
                hint = Panel.fit(
                    Markdown(str(error.hint_stmt)),
                    title="[blue]Hint",
                    padding=(1, 4),
                )
                errors.add_row(hint)
                errors.add_row(subtable)
            table.add_row("[red]Errors", errors)
        yield table

    @property
    def latest_successful_dialect(self):
        return max(self.confirmed_dialects, default=None)

    @property
    def confirmed_dialects(self):
        return self._info.dialects.difference(self._unsuccessful_dialects)

    @property
    def success(self):
        return not self.errors and not self.warnings

    def dialect_failed(
        self,
        dialect: Dialect,
        results: Sequence[tuple[TestCase, SeqResult]],
    ):
        dialects = self._unsuccessful_dialects.insert(dialect)

        if dialects != self._info.dialects:
            errors = self.errors.push_front(
                DiagnosticError(
                    code="smoke-found-broken-dialect",
                    message=f"All {dialect.pretty_name} examples failed.",
                    causes=results_to_causes(results),
                    hint_stmt=(
                        "Verify that the implementation truly supports "
                        "the dialect. If you're sure it does, it is "
                        "likely that the Bowtie harness is not "
                        "functioning propertly."
                    ),
                ),
            )
        else:  # nothing succeeded, show an even stronger error
            prior_failures: Sequence[DiagnosticError] = []
            errors: List[DiagnosticError] = List()
            for error in self.errors:
                if error.code == "smoke-found-broken-dialect":
                    prior_failures.append(error)
                else:
                    errors = errors.push_front(error)
            errors = errors.push_front(
                DiagnosticError(
                    code="smoke-no-successful-results",
                    message="No successful results were seen.",
                    causes=[
                        cause
                        for each in prior_failures
                        for cause in each.causes
                    ],
                    hint_stmt=(
                        "The harness seems to be entirely broken.\n\n"
                        "Check for error messages it may have emitted (likely "
                        "to its standard error which is shown below).\n"
                        "Or use programming language-specific mechanisms "
                        "from the language the harness is written in "
                        "to diagnose."
                    ),
                ),
            )

        return evolve(self, unsuccessful_dialects=dialects, errors=errors)

    def no_referencing(self, results: Sequence[tuple[TestCase, SeqResult]]):
        return evolve(
            self,
            warnings=self.warnings.push_front(
                DiagnosticWarning(
                    code="smoke-broken-referencing",
                    message="Basic referencing support does not work.",
                    causes=results_to_causes(results),
                    hint_stmt=(
                        "The implementation was sent a simple `$ref` to "
                        "resolve and did not follow it correctly. "
                        "Check to be sure the harness is properly handling "
                        "the `registry` property when sent in a test case.\n"
                        "If however the implementation does not support "
                        "reference resolution in any form, you might not "
                        "be able to address this warning."
                    ),
                ),
            ),
        )

    def serializable(self) -> dict[str, Any]:
        as_dict: dict[str, Any] = dict(
            success=self.success,
            confirmed_dialects=[
                dialect.short_name
                for dialect in sorted(self.confirmed_dialects, reverse=True)
            ],
        )
        for each in "errors", "warnings":
            value = getattr(self, each)
            if value:
                as_dict[each] = [
                    dict(code=each.code, message=each.message)
                    for each in value
                ]
        return as_dict
