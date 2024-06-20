"""
Smoke testing of implementations.

Represents a sort of "absolute minimum level of assumed correctness" which we
can use to decide whether a harness is correctly written, even though
implementations may still be buggy / not fully compliant.
"""

from __future__ import annotations

from functools import cached_property
from textwrap import dedent
from typing import TYPE_CHECKING, Any
import json

from attrs import evolve, field, frozen
from referencing.jsonschema import EMPTY_REGISTRY
from rpds import HashTrieMap

from bowtie._core import Example, Test, TestCase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from rich.console import Console, ConsoleOptions, RenderResult

    from bowtie._commands import SeqResult
    from bowtie._core import ConnectableId, Dialect, Implementation

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
    dialects = DialectResults()

    for dialect in implementation.info.dialects:
        cases = [
            dialect.top_test_case(EXAMPLES),
            dialect.bottom_test_case(EXAMPLES),
        ]
        failures = await implementation.failing(dialect=dialect, cases=cases)
        dialects = dialects.with_result(dialect, failures)

    # no point checking $ref unless we have a working dialect
    last, ref = dialects.latest_successful, None
    if last is not None:
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
        failure = await implementation.failing(dialect=last, cases=[ref_check])
        if failure:
            (ref,) = failure

    return Result(id=implementation.id, dialects=dialects, ref=ref)


@frozen
class Result:
    """
    The result of smoke testing an implementation.
    """

    id: ConnectableId
    _dialects: DialectResults = field(repr=False, alias="dialects")
    _ref: tuple[TestCase, SeqResult] | None = field(repr=False, alias="ref")

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        from rich import box
        from rich.panel import Panel
        from rich.table import Column, Table

        epilog = Table.grid(padding=2, pad_edge=True)

        failures = self._dialects.failures

        prefix = f"{self.id} [dim]seems to"
        if failures:
            title = f"{prefix} be [/][b red]broken!"

            for dialect, cases_and_results in failures:
                first = cases_and_results[0][0]
                subtable = Table(
                    Column("Schema", vertical="middle", no_wrap=True),
                    Column("Instances", vertical="middle"),
                    title=f"{dialect.pretty_name} [red]Failures[/]",
                    padding=2,
                    box=box.MINIMAL,
                    show_header=False,
                    caption=dedent(
                        rf"""
                        [blue]bowtie validate -i {self.id} <(printf '
                            {json.dumps(first.schema)}
                        ') <(printf '
                            {json.dumps(first.tests[0].instance)}
                        ')

                        [/]can be used to reproduce one of the failures.
                        """,
                    ),
                    caption_justify="left",
                )
                for case, seq_result in cases_and_results:
                    instances = Table(box=None, padding=1)
                    for i, test in enumerate(case.tests):
                        result = seq_result.result.result_for(i)
                        if result.errored:
                            message = "[b red]errored"
                        else:
                            word = "valid" if result.valid else "invalid"  # type: ignore[reportUnknownMemberType]
                            message = f"[red]incorrectly[/] {word}"

                        instances.add_row(test.syntax(), message)

                    subtable.add_row(case.syntax(dialect), instances)
                epilog.add_row(subtable)
        elif self._ref:
            title = f"{prefix} be [/][b yellow]broken!"

            panel = Panel.fit(
                (
                    "The implementation was sent a simple `$ref` to "
                    "resolve and did not follow it correctly. "
                    "Check to be sure the harness is properly handling "
                    "the `registry` property when sent in a test case.\n"
                    "If however the implementation does not support "
                    "reference resolution in any form, you might not "
                    "be able to address this warning."
                ),
                title="[b yellow]Basic referencing support does not work.",
                padding=1,
            )
            epilog.add_row(panel)
        else:
            title = f"{prefix} [/][b green]work!"

        yield ""
        table = Table(
            Column("Label", no_wrap=True, justify="center"),
            Column("Content"),
            title=title,
            padding=1,
            box=None,
            show_header=False,
            pad_edge=True,
            min_width=79,
            title_justify="center",
        )
        table.add_row("Dialects\n[dim](Confirmed Working)", self._dialects)
        yield table
        yield epilog

    def for_each_dialect(self):
        return sorted(self._dialects, reverse=True)

    @cached_property
    def success(self):
        # We treat referencing failures as soft failures, since so many
        # implementations have issues :( Perhaps this will change.
        return not self._dialects.failures

    def serializable(self) -> dict[str, Any]:
        if self.success:
            return dict(
                success=True,
                dialects=[
                    each.short_name for each, _ in self.for_each_dialect()
                ],
                **{"registry": False} if self._ref else {},
            )
        return dict(
            success=False,
            dialects={  # FIXME: some standard representation of discrepancy
                dialect.short_name: [
                    dict(
                        schema=case.schema,
                        instances=[each.instance for each in case.tests],
                        expected=[
                            dict(valid=expect) for expect in each.expected
                        ],
                        **each.result.serializable(),
                    )
                    for case, each in failures
                ]
                for dialect, failures in self.for_each_dialect()
            },
        )


@frozen
class DialectResults:
    """
    An indication of whether each claimed supported dialect works.
    """

    _dialects: HashTrieMap[Dialect, Sequence[tuple[TestCase, SeqResult]]] = (
        HashTrieMap()
    )
    latest_successful: Dialect | None = None

    def __iter__(self):
        return iter(self._dialects.items())

    @cached_property
    def failures(self):
        return sorted(
            ((k, v) for k, v in self._dialects.items() if v),
            reverse=True,
        )

    def __rich__(self):
        from rich.table import Column, Table

        table = Table.grid(Column("Name", justify="right"))
        ordered = sorted(self._dialects.items(), reverse=True)
        for dialect, failures in ordered:
            style = "red" if failures else "green"
            table.add_row(f"{dialect.pretty_name}", style=style)
        return table

    def with_result(
        self,
        dialect: Dialect,
        results: Sequence[tuple[TestCase, SeqResult]],
    ):
        latest = self.latest_successful
        if not results and (latest is None or dialect > latest):
            latest = dialect
        dialects = self._dialects.insert(dialect, results)
        return evolve(self, dialects=dialects, latest_successful=latest)
