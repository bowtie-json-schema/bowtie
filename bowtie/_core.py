from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import date
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, TypeVar, cast
from uuid import uuid4
import json

from attrs import asdict, evolve, field, frozen, mutable
from diagnostic import DiagnosticError
from referencing.jsonschema import EMPTY_REGISTRY, Schema, specification_with
from rich.panel import Panel
from rpds import HashTrieMap
from url import URL
import httpx
import referencing_loaders

from bowtie import HOMEPAGE
from bowtie._commands import (
    START_V1,
    STOP,
    CaseErrored,
    Dialect as DialectCommand,
    SeqCase,
    SeqResult,
    StartedDialect,
)
from bowtie._registry import ValidatorRegistry
from bowtie.exceptions import DialectError, ProtocolError, UnsupportedDialect

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Iterable,
        Mapping,
        Sequence,
        Set,
    )
    from typing import Self

    from referencing import Specification
    from referencing.jsonschema import SchemaRegistry, SchemaResource
    from rich.console import Console, ConsoleOptions, RenderResult

    from bowtie._commands import (
        AnyCaseResult,
        Command,
        Message,
        Run,
        Seq,
    )
    from bowtie._connectables import ConnectableId
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
    def from_dict(
        cls,
        firstPublicationDate: str,
        prettyName: str,
        shortName: str,
        uri: str,
        aliases: Iterable[str] = (),
        hasBooleanSchemas: bool = True,
        **_: Any,
    ) -> Self:

        return cls(
            uri=URL.parse(uri),
            pretty_name=prettyName,
            short_name=shortName,
            first_publication_date=date.fromisoformat(firstPublicationDate),
            aliases=frozenset(aliases),
            has_boolean_schemas=hasBooleanSchemas,
        )

    @classmethod
    def from_str(cls, uri: str):
        return cls.by_uri()[URL.parse(uri)]

    async def latest_report(self):
        url = HOMEPAGE / f"{self.short_name}.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(str(url))

        from bowtie._report import Report

        return Report.from_serialized(response.iter_lines())

    def serializable(self):
        return str(self.uri)

    def specification(self, **kwargs: Any) -> Specification[SchemaResource]:
        return specification_with(str(self.uri), **kwargs)


@frozen
class NoSuchImplementation(Exception):
    """
    An implementation with the given name does not exist.
    """

    id: str

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
        causes: list[str] = []
        if self.__cause__ is None:
            hint = (
                "If you are developing a new harness, check if stderr "
                "(shown below) contains harness-specific information "
                "which can help. Otherwise, you may have an issue with your "
                "local container setup (podman, docker, etc.)."
            )
        else:
            errors = getattr(self.__cause__, "errors", [])
            hint = (
                "The harness sent an invalid response for Bowtie's protocol. "
                "Details for what was wrong are above. If you are developing "
                "support for a new harness you should address them, otherwise "
                "if you are not, this is a bug in Bowtie's harness for this "
                "implementation! File an issue on Bowtie's issue tracker."
            )
            causes.extend(str(error) for error in errors)

        yield DiagnosticError(
            code="startup-failed",
            message=f"{self.id!r} failed to start.",
            causes=causes,
            hint_stmt=hint,
        )
        if self.stderr:
            yield Panel(self.stderr, title="stderr")


R = TypeVar("R")


MakeValidator = Callable[[], Callable[[Any, Schema], None]]


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

    def serializable(self):
        return {
            **{k: v for k, v in asdict(self, recurse=False).items() if v},
            "dialects": sorted(
                (str(dialect.uri) for dialect in self.dialects),
                reverse=True,
            ),
            "homepage": str(self.homepage),
            "issues": str(self.issues),
            "source": str(self.source),
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

    async def poison(self, message: Message) -> None:
        """
        Poison the harness by sending a message which causes it to stop itself.
        """
        ...


@frozen
class HarnessClient:
    """
    A client which speaks to a specific running implementation harness.
    """

    _connection: Connection = field(alias="connection")

    _make_validator: MakeValidator = field(alias="make_validator")

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
        validate = self._make_validator()
        request = cmd.to_request(validate=validate)
        try:
            response = await self._connection.request(request)
        except Restarted:
            await self._get_back_up_to_date()
            # FIXME: Probably handle infinitely restarting harnesses
            response = await self._connection.request(request)
        if response is not None:
            return cmd.from_response(response, validate=validate)

    async def poison(self) -> None:
        validate = self._make_validator()
        await self._connection.poison(STOP.to_request(validate=validate))  # type: ignore[reportArgumentType]


@frozen
class DialectRunner:
    """
    A running implementation which is speaking a specific dialect.
    """

    dialect: Dialect
    implementation: ConnectableId
    _harness: HarnessClient = field(repr=False, alias="harness")

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

        if response != StartedDialect.OK:
            reporter.unacknowledged_dialect(
                implementation=implementation,
                dialect=dialect,
                response=response,
            )

        return cls(
            dialect=dialect,
            implementation=implementation,
            harness=new_harness,
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

        await _harness.poison()

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

    async def smoke(
        self,
    ) -> AsyncIterator[
        tuple[Dialect, AsyncIterator[tuple[TestCase, SeqResult]]]
    ]:
        """
        Smoke test this implementation.
        """
        instances = [
            # FIXME: When horejsek/python-fastjsonschema#181 is merged
            #        and/or we special-case fastjsonschema...
            # ("nulll", None),  # noqa: ERA001
            ("boolean", True),
            ("integer", 37),
            ("number", 37.37),
            ("string", "37"),
            ("array", [37]),
            ("object", {"foo": 37}),
        ]

        # FIXME: All dialects
        for dialect in [max(self.info.dialects)]:
            cases = [
                TestCase(
                    description="allow-everything",
                    schema={},
                    tests=[
                        Test(
                            description=json_type,
                            instance=instance,
                            valid=True,
                        )
                        for json_type, instance in instances
                    ],
                ).with_explicit_dialect(dialect),
                TestCase(
                    description="allow-nothing",
                    schema={"not": {}},
                    tests=[
                        Test(
                            description=json_type,
                            instance=instance,
                            valid=False,
                        )
                        for json_type, instance in instances
                    ],
                ).with_explicit_dialect(dialect),
            ]

            yield dialect, self.validate(dialect=dialect, cases=cases)


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


@frozen
class Group:
    description: str
    children: Sequence[Group | LeafGroup]
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
def validator_registry() -> ValidatorRegistry:
    resources = referencing_loaders.from_traversable(files("bowtie.schemas"))
    registry = EMPTY_REGISTRY.with_resources(resources).crawl()
    return ValidatorRegistry.jsonschema(registry=registry)
