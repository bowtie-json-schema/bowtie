from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast
from uuid import uuid4
import json

from attrs import Factory, asdict, evolve, field, frozen, mutable
from diagnostic import DiagnosticError, DiagnosticWarning
from referencing.jsonschema import EMPTY_REGISTRY, specification_with
from rich.panel import Panel
from rpds import HashTrieMap, HashTrieSet, List
from url import URL
import httpx
import referencing_loaders

from bowtie import HOMEPAGE
from bowtie._commands import (
    START_V1,
    CaseErrored,
    Dialect as DialectCommand,
    SeqCase,
    SeqResult,
    StartedDialect,
)
from bowtie.exceptions import DialectError, ProtocolError, UnsupportedDialect

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Callable,
        Iterable,
        Mapping,
        Sequence,
        Set,
    )
    from typing import Self

    from referencing import Specification
    from referencing.jsonschema import Schema, SchemaRegistry
    from rich.console import (
        Console,
        ConsoleOptions,
        RenderableType,
        RenderResult,
    )

    from bowtie._commands import (
        AnyCaseResult,
        Command,
        Message,
        Run,
        Seq,
    )
    from bowtie._connectables import ConnectableId
    from bowtie._registry import ValidatorRegistry
    from bowtie._report import Reporter


@frozen
class Dialect:
    """
    A dialect of JSON Schema.
    """

    pretty_name: str
    uri: URL = field(repr=False)
    short_name: str = field(repr=False)
    first_publication_date: date = field(repr=False)
    aliases: Set[str] = field(
        default=cast(frozenset[str], frozenset()),
        repr=False,
    )
    has_boolean_schemas: bool = field(default=True, repr=False)

    _top_schema: Schema | None = field(
        default=Factory(
            lambda self: {"$schema": str(self.uri)},
            takes_self=True,
        ),
        hash=False,
        repr=False,
        alias="top_schema",
    )
    _bottom_schema: Schema | None = field(
        default=Factory(
            lambda self: (
                None
                if self._top_schema is None
                else {"$schema": str(self.uri), "not": self.top_schema}
            ),
            takes_self=True,
        ),
        hash=False,
        repr=False,
        alias="bottom_schema",
    )

    def __lt__(self, other: Any):
        if other.__class__ is not Dialect:
            return NotImplemented
        return self.first_publication_date < other.first_publication_date

    @classmethod
    @cache
    def by_short_name(cls) -> HashTrieMap[str, Dialect]:
        return HashTrieMap((each.short_name, each) for each in cls.known())

    @classmethod
    @cache
    def by_alias(cls) -> HashTrieMap[str, Dialect]:
        return cls.by_short_name().update(
            (alias, dialect)
            for dialect in cls.known()
            for alias in dialect.aliases
        )

    @classmethod
    @cache
    def by_uri(cls) -> HashTrieMap[URL, Dialect]:
        return HashTrieMap((each.uri, each) for each in cls.known())

    @classmethod
    @cache
    def known(cls) -> Iterable[Dialect]:
        data = files("bowtie") / "data"
        if not data.is_dir():
            data = Path(__file__).parent.parent / "data"

        return frozenset(
            Dialect.from_dict(**each)
            for each in json.loads(data.joinpath("dialects.json").read_text())
        )

    @classmethod
    @cache
    def latest(cls):
        """
        The latest dialect known to Bowtie.
        """
        return max(cls.known())

    @classmethod
    def from_dict(
        cls,
        firstPublicationDate: str,
        prettyName: str,
        shortName: str,
        uri: str,
        aliases: Iterable[str] = (),
        hasBooleanSchemas: bool = True,
        **kwargs: Any,
    ) -> Self:

        for each in "top", "bottom":
            if each in kwargs:
                kwargs[f"{each}_schema"] = kwargs.pop(each)

        del kwargs["$schema"]
        return cls(
            uri=URL.parse(uri),
            pretty_name=prettyName,
            short_name=shortName,
            first_publication_date=date.fromisoformat(firstPublicationDate),
            aliases=frozenset(aliases),
            has_boolean_schemas=hasBooleanSchemas,
            **kwargs,
        )

    @classmethod
    def from_str(cls, uri: str):
        return cls.by_uri()[URL.parse(uri)]

    async def latest_report(self):
        url = HOMEPAGE / f"{self.short_name}.json"
        async with httpx.AsyncClient() as client:
            return await client.get(str(url))

    def serializable(self):
        return str(self.uri)

    def specification(self, **kwargs: Any) -> Specification[Schema]:
        return specification_with(str(self.uri), **kwargs)

    @property
    def top_schema(self):
        if self._top_schema is None:
            raise ValueError(f"{self} has no top schema.")
        return self._top_schema

    @property
    def bottom_schema(self):
        if self._bottom_schema is None:
            raise ValueError(f"{self} has no bottom schema.")
        return self._bottom_schema

    def top(self):
        """
        Create a validator in this dialect which allows all instances.
        """
        from bowtie._direct_connectable import Direct

        validators = Direct.from_id("python-jsonschema").registry()
        return validators.for_schema(self.top_schema)

    def bottom(self):
        """
        Create a validator in this dialect which does not allow any instances.
        """
        from bowtie._direct_connectable import Direct

        validators = Direct.from_id("python-jsonschema").registry()
        return validators.for_schema(self.bottom_schema)

    def top_test_case(
        self,
        examples: Iterable[Example],
        description: str = "top allows everything",
    ):
        return TestCase(
            description=description,
            schema=self.top_schema,
            tests=[example.expect(True) for example in examples],
        )

    def bottom_test_case(
        self,
        examples: Iterable[Example],
        description: str = "bottom allows nothing",
    ):
        return TestCase(
            description=description,
            schema=self.bottom_schema,
            tests=[example.expect(False) for example in examples],
        )


@frozen
class NoSuchImplementation(Exception):
    """
    An implementation with the given name does not exist.
    """

    id: ConnectableId

    def __rich__(self):
        return DiagnosticError(
            code="no-such-implementation",
            message=f"{self.id!r} is not a known Bowtie implementation.",
            causes=[],
            hint_stmt=(
                "Check Bowtie's supported list of implementations "
                "to ensure you have the name correct. "
                "If you are developing a new harness, ensure you have "
                "built and tagged it properly."
            ),
        )


@frozen
class GotStderr(Exception):
    """
    An implementation sent data on standard error.

    We were trying to communicate with it (via Bowtie's protocol), but the
    implementation has likely encountered some unexpected error.

    It may have crashed.

    Implementations of the `Connection` protocol should raise this exception
    when they detect this kind of out-of-band error (in whatever concrete
    connection-specific mechanism indicates this has occurred).
    """

    stderr: bytes


class Restarted(Exception):
    """
    A connection was restarted, so we may need to replay some messages.
    """


@frozen
class InvalidResponse(Exception):
    """
    An invalid response was sent by a harnes.
    """

    contents: str


@frozen
class StartupFailed(Exception):
    id: ConnectableId
    stderr: str = ""
    data: Any = None

    def __rich_console__(
        self,
        console: Console,
        options: ConsoleOptions,
    ) -> RenderResult:
        cause = self.__cause__
        if cause is None:
            root_causes, hint = [], (
                "If you are developing a new harness, check if stderr "
                "(shown below) contains harness-specific information "
                "which can help. Otherwise, you may have an issue with your "
                "local container setup (podman, docker, etc.)."
            )
        else:
            root_causes: Iterable[Exception] = getattr(
                cause.__cause__,
                "exceptions",
                [],
            )
            hint = (
                "The harness sent an invalid response for Bowtie's protocol. "
                "Details for what was wrong are above. If you are developing "
                "support for a new harness you should address them, otherwise "
                "if you are not, this is a bug in Bowtie's harness for this "
                "implementation! File an issue on Bowtie's issue tracker."
            )

        yield DiagnosticError(
            code="startup-failed",
            message=f"{self.id!r} failed to start.",
            causes=[str(exc) for exc in root_causes],
            hint_stmt=hint,
        )
        if self.stderr:
            yield Panel(self.stderr, title="stderr")


R = TypeVar("R")


@frozen
class Link:
    description: str
    url: URL

    @classmethod
    def from_dict(cls, description: str, url: str):
        return cls(description=description, url=URL.parse(url))

    def serializable(self):
        return dict(description=self.description, url=str(self.url))


@frozen(order=True)
class ImplementationInfo:
    # FIXME: Combine with / separate out more from `Implementation`

    name: str
    language: str
    homepage: URL
    issues: URL
    source: URL
    dialects: frozenset[Dialect]

    version: str | None = None
    language_version: str | None = None
    os: str | None = None
    os_version: str | None = None
    documentation: URL | None = None
    links: Iterable[Link] = ()

    @classmethod
    def from_dict(
        cls,
        homepage: str,
        issues: str,
        source: str,
        dialects: list[str],
        links: Iterable[dict[str, Any]] = (),
        **kwargs: Any,
    ):
        return cls(
            homepage=URL.parse(homepage),
            issues=URL.parse(issues),
            source=URL.parse(source),
            dialects=frozenset(Dialect.from_str(each) for each in dialects),
            links=[Link.from_dict(**each) for each in links],
            **kwargs,
        )

    @property
    def id(self):
        """
        A unique identifier we use to refer to the implementation.

        This ID is *independent* of the connectable (i.e. how we speak to the
        implementation) but should be unique across disparate implementations.
        """
        return f"{self.language}-{self.name}"

    def serializable(self):
        return {
            **{
                k: (
                    str(v)
                    if k
                    in {
                        "homepage",
                        "issues",
                        "source",
                        "documentation",
                    }
                    else v
                )
                for k, v in asdict(self, recurse=False).items()
                if v
            },
            "dialects": sorted(
                (str(dialect.uri) for dialect in self.dialects),
                reverse=True,
            ),
            "links": [link.serializable() for link in self.links],
        }


class Connection(Protocol):
    """
    A connection to a specific JSON Schema implementation.

    Concrete implementations of this protocol will decide what means of
    communication are used -- e.g. sockets, files, in-memory -- as
    well as how the JSON Schema implementation is running -- in a separate
    process, in-memory, et cetera.
    """

    async def request(self, message: Message) -> Message | None:
        """
        Send a request to the harness.
        """
        ...


@frozen
class HarnessClient:
    """
    A client which speaks to a specific running implementation harness.
    """

    _connection: Connection = field(alias="connection")

    _registry: ValidatorRegistry[Any] = field(alias="registry")

    # FIXME: Remove this somehow by making the state machine even more explicit
    #: A sequence of commands to replay if we end up restarting the connection.
    _if_replaying: Sequence[Command[Any]] = ()

    async def _get_back_up_to_date(self):
        for each in self._if_replaying:
            await self.request(each)  # TODO: response assert?

    async def transition(self, cmd: Command[R]) -> tuple[Self, R | None]:
        response = await self.request(cmd)
        harness = evolve(self, if_replaying=[*self._if_replaying, cmd])
        return harness, response

    async def request(self, cmd: Command[R]) -> R | None:
        """
        Send a given command to the implementation and return its response.
        """
        request = cmd.to_request(registry=self._registry)
        try:
            response = await self._connection.request(request)
        except Restarted:
            await self._get_back_up_to_date()
            # FIXME: Probably handle infinitely restarting harnesses
            response = await self._connection.request(request)
        if response is not None:
            return cmd.from_response(response, registry=self._registry)


@frozen
class DialectRunner:
    """
    A running implementation which is speaking a specific dialect.
    """

    dialect: Dialect
    implementation: ConnectableId
    _harness: HarnessClient = field(repr=False, alias="harness")

    schema_without_dialect: Callable[[Any], None] = field(
        repr=False,
        alias="schema_without_dialect",
    )

    @classmethod
    async def for_dialect(
        cls,
        dialect: Dialect,
        implementation: ConnectableId,
        harness: HarnessClient,
        reporter: Reporter,
    ):
        new_harness: HarnessClient
        response: StartedDialect
        new_harness, response = await harness.transition(
            DialectCommand(dialect=str(dialect.uri)),  # type: ignore[reportArgumentType]
        )

        if response == StartedDialect.OK:

            def schema_without_dialect(_: Any):  # type: ignore[reportRedeclaration]
                pass

        else:

            def schema_without_dialect(schema: Any):
                reporter.schema_without_dialect(
                    schema=schema,
                    implementation=implementation,
                    dialect=dialect,
                )

        return cls(
            dialect=dialect,
            implementation=implementation,
            harness=new_harness,
            schema_without_dialect=schema_without_dialect,
        )

    async def validate(
        self,
        run: Run,
        expected: Sequence[bool | None],
    ) -> SeqResult:
        try:
            response: tuple[Seq, AnyCaseResult] | None = (
                await self._harness.request(run)  # type: ignore[reportArgumentType]
            )
            if response is None:
                result = CaseErrored.uncaught()
            else:
                seq, result = response
                if seq != run.seq:
                    result = CaseErrored.uncaught(
                        message="mismatched seq",
                        expected=run.seq,
                        got=seq,
                        response=result,
                    )
        except GotStderr as error:
            result = CaseErrored.uncaught(stderr=error.stderr.decode("utf-8"))
        except InvalidResponse as error:
            result = CaseErrored.uncaught(response=error.contents)
        return SeqResult(
            seq=run.seq,
            implementation=self.implementation,
            expected=expected,
            result=result,
        )


@frozen
class Smoked:
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


@mutable
class Implementation:
    """
    A running implementation under test.
    """

    id: ConnectableId
    info: ImplementationInfo
    _harness: HarnessClient = field(repr=False, alias="harness")
    _reporter: Reporter = field(alias="reporter")

    @classmethod
    def known(cls) -> Set[ConnectableId]:
        data = files("bowtie") / "data"
        if data.is_dir():
            path = data / "known_implementations.json"
            known = json.loads(path.read_text())
        else:
            root = Path(__file__).parent.parent
            dir = root.joinpath("implementations").iterdir()
            known = (d.name for d in dir if not d.name.startswith("."))
        return frozenset(known)

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        id: ConnectableId,
        reporter: Reporter,
        **kwargs: Any,
    ) -> AsyncIterator[Self]:
        _harness = HarnessClient(**kwargs)

        try:
            harness, started = await _harness.transition(START_V1)  # type: ignore[reportArgumentType]
        except ProtocolError as err:
            raise StartupFailed(id=id) from err
        except GotStderr as err:
            raise StartupFailed(id=id, stderr=err.stderr.decode()) from err
        else:
            if started is None:
                raise StartupFailed(id=id)

        info = ImplementationInfo.from_dict(**started.implementation)  # type: ignore[reportUnknownArgumentType]

        yield cls(harness=harness, id=id, info=info, reporter=reporter)

    def supports(self, *dialects: Dialect) -> bool:
        """
        Does the implementation support (all of) the given dialect(s)?
        """
        return self.info.dialects.issuperset(dialects)

    async def validate(
        self,
        dialect: Dialect,
        cases: Iterable[TestCase],
    ) -> AsyncIterator[tuple[TestCase, SeqResult]]:
        """
        Run a collection of test cases under the given dialect.
        """
        runner = await self.start_speaking(dialect)

        for case in cases:
            seq_case = SeqCase(seq=uuid4().hex, case=case)
            yield case, await seq_case.run(runner=runner)

    async def failing(
        self,
        dialect: Dialect,
        cases: Iterable[TestCase],
    ) -> Sequence[tuple[TestCase, SeqResult]]:
        """
        Run the given cases and yield ones which the implementation fails.
        """
        results = self.validate(dialect=dialect, cases=cases)
        return [each async for each in results if each[1].unsuccessful()]

    async def start_speaking(self, dialect: Dialect) -> DialectRunner:
        if not self.supports(dialect):
            raise UnsupportedDialect(implementation=self, dialect=dialect)
        try:
            return await DialectRunner.for_dialect(
                implementation=self.id,
                dialect=dialect,
                harness=self._harness,
                reporter=self._reporter,
            )
        except GotStderr as error:
            # the implementation failed on the dialect request.
            # there's likely no reason to continue, so we throw an exception
            raise DialectError(
                implementation=self,
                dialect=dialect,
                stderr=error.stderr,
            ) from error

    async def smoke(self) -> Smoked:
        """
        Smoke test this implementation.
        """
        examples = [
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

        smoked = Smoked(info=self.info)

        for dialect in self.info.dialects:
            unsuccessful = await self.failing(
                dialect=dialect,
                cases=[
                    dialect.top_test_case(examples),
                    dialect.bottom_test_case(examples),
                ],
            )
            if unsuccessful:
                smoked = smoked.dialect_failed(dialect, results=unsuccessful)

        last = smoked.latest_successful_dialect
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
            unsuccessful = await self.failing(dialect=last, cases=[ref_check])
            if unsuccessful:
                smoked = smoked.no_referencing(results=unsuccessful)

        return smoked


def results_to_causes(
    results: Sequence[tuple[TestCase, SeqResult]],
) -> list[str]:
    # FIXME
    return []


@frozen
class Example:
    """
    A validation example where we don't have any particularly expected result.
    """

    description: str
    instance: Any
    comment: str | None = None

    def expected(self) -> None:
        """
        We have no expected result.
        """
        return None

    def expect(self, valid: bool) -> Test:
        """
        Decide we really do expect some specific result.
        """
        return Test(**asdict(self), valid=valid)

    def syntax(self) -> RenderableType:
        from pygments.lexers.data import (  # type: ignore[reportMissingTypeStubs]
            JsonLexer,
        )
        from rich.syntax import Syntax

        return Syntax(
            json.dumps(self.instance),
            lexer=JsonLexer(),
            background_color="default",
            word_wrap=True,
        )

    @classmethod
    def from_dict(
        cls,
        valid: bool | None = None,
        **data: Any,
    ) -> Example | Test:
        if valid is None:
            return cls(**data)
        return Test(**data, valid=valid)


@frozen
class Test:
    """
    An `Example` with a specific expected result.
    """

    description: str
    instance: Any
    valid: bool
    comment: str | None = None

    def expected(self) -> bool:
        """
        Expect our expected validity result.
        """
        return self.valid

    def syntax(self) -> RenderableType:
        from pygments.lexers.data import (  # type: ignore[reportMissingTypeStubs]
            JsonLexer,
        )
        from rich.syntax import Syntax

        return Syntax(
            json.dumps(self.instance),
            lexer=JsonLexer(),
            background_color="default",
            word_wrap=True,
        )


@frozen
class Group:
    description: str
    children: Sequence[Group] | Sequence[LeafGroup]
    comment: str | None = None
    registry: SchemaRegistry = EMPTY_REGISTRY


@frozen
class LeafGroup:
    description: str
    schema: Schema
    children: Sequence[Example | Test]
    comment: str | None = None
    registry: SchemaRegistry = EMPTY_REGISTRY


@frozen
class TestCase:
    description: str
    schema: Any
    tests: Sequence[Example | Test]
    comment: str | None = None
    registry: SchemaRegistry = EMPTY_REGISTRY

    @classmethod
    def from_dict(
        cls,
        dialect: Dialect,
        tests: Iterable[dict[str, Any]],
        registry: Mapping[str, Schema] = {},
        **kwargs: Any,
    ):
        populated = EMPTY_REGISTRY.with_contents(
            registry.items(),
            default_specification=dialect.specification(),
        )
        return cls(
            tests=[Example.from_dict(**test) for test in tests],
            registry=populated,
            **kwargs,
        )

    def with_explicit_dialect(self, dialect: Dialect):
        """
        Return a version of this test case with an explicit dialect ID.
        """
        schema = self.schema
        if not isinstance(self.schema, bool):
            schema = {"$schema": str(dialect.uri), **self.schema}
        return evolve(self, schema=schema)

    def serializable(self) -> Message:
        as_dict = asdict(
            self,
            filter=lambda k, v: k.name != "registry"
            and (k.name != "comment" or v is not None),
        )
        if self.registry:
            # FIXME: Via python-jsonschema/referencing#16
            as_dict["registry"] = {
                k: v.contents for k, v in self.registry.items()
            }
        return as_dict

    def syntax(self, dialect: Dialect) -> RenderableType:
        from jsonschema_lexer import JSONSchemaLexer
        from rich.syntax import Syntax

        return Syntax(
            json.dumps(self.schema, indent=2),
            lexer=JSONSchemaLexer(str(dialect.uri)),
            background_color="default",
            word_wrap=True,
        )

    def uniq(self) -> str:
        """
        An internally used unique identifier when we want unique cases.

        Really this is just the JSON-serialized, normalized case.

        But that can change.
        """
        return json.dumps(self.serializable(), sort_keys=True)

    def expected_results(self) -> Sequence[bool | None]:
        return [each.expected() for each in self.tests]

    def without_expected_results(self) -> Message:
        serializable = self.serializable()
        serializable["tests"] = [
            {
                k: v
                for k, v in test.items()
                if k != "valid" and (k != "comment" or v is not None)
            }
            for test in serializable.pop("tests")
        ]
        return serializable


@cache
def registry():
    resources = referencing_loaders.from_traversable(files("bowtie.schemas"))
    return EMPTY_REGISTRY.with_resources(resources).crawl()
