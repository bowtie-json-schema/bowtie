from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import date
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, TypeVar
import json

from attrs import asdict, evolve, field, frozen, mutable
from referencing import Specification
from referencing.jsonschema import (
    EMPTY_REGISTRY,
    Schema,
    SchemaRegistry,
    specification_with,
)
from rpds import HashTrieMap
from url import URL

from bowtie._commands import (
    START_V1,
    STOP,
    CaseErrored,
    Dialect as DialectCommand,
    SeqCase,
    SeqResult,
    StartedDialect,
)
from bowtie.exceptions import ProtocolError

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        Iterable,
        Mapping,
        Sequence,
        Set,
    )
    from typing import Any, Self

    from referencing.jsonschema import SchemaResource

    from bowtie._commands import (
        AnyCaseResult,
        Command,
        ImplementationId,
        Message,
        Run,
        Seq,
    )
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
    aliases: Set[str] = field(default=frozenset(), repr=False)
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
        **_: Any,
    ) -> Self:

        return cls(
            uri=URL.parse(uri),
            pretty_name=prettyName,
            short_name=shortName,
            first_publication_date=date.fromisoformat(firstPublicationDate),
            aliases=frozenset(aliases),
        )

    def current_dialect_resource(self) -> SchemaResource:
        # it's of course unimportant what dialect is used for this referencing
        # schema, what matters is that the target dialect is applied
        from referencing.jsonschema import DRAFT202012

        return DRAFT202012.create_resource(
            {
                # Should match the magic value used for `schema` in `schemas/io/`
                "$id": "tag:bowtie.report,2023:ihop:__dialect__",
                "$ref": str(self.uri),
            },
        )


@frozen
class NoSuchImplementation(Exception):
    """
    An implementation with the given name does not exist.
    """

    name: str


@frozen
class GotStderr(Exception):
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
    name: str
    stderr: str = ""
    data: Any = None

    def __str__(self) -> str:
        if self.stderr:
            return f"{self.name}'s stderr contained: {self.stderr}"
        return self.name


R = TypeVar("R")


class _MakeValidator(Protocol):
    def __call__(
        self,
        *more_schemas: SchemaResource,
    ) -> Callable[..., None]: ...


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

    _image: ImplementationId = field(alias="image")

    name: str
    language: str
    homepage: URL
    issues: URL
    source: URL
    dialects: Set[Dialect]

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
        BY_URI = Dialect.by_uri()
        return cls(
            homepage=URL.parse(homepage),
            issues=URL.parse(issues),
            source=URL.parse(source),
            dialects=frozenset(BY_URI[URL.parse(each)] for each in dialects),
            links=[Link.from_dict(**each) for each in links],
            **kwargs,
        )

    @property
    def id(self):
        return self._image

    def serializable(self):
        as_dict = {
            k: v
            for k, v in asdict(self, recurse=False).items()
            if not k.startswith("_") and v
        }
        dialects = (str(dialect.uri) for dialect in as_dict["dialects"])
        as_dict.update(
            homepage=str(as_dict["homepage"]),
            issues=str(as_dict["issues"]),
            source=str(as_dict["source"]),
            dialects=sorted(dialects, reverse=True),
            links=[link.serializable() for link in self.links],
        )
        return as_dict


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

    _make_validator: _MakeValidator = field(alias="make_validator")
    _resources_for_validation: Sequence[SchemaResource] = field(
        default=(),
        alias="resources_for_validation",
    )

    # FIXME: Remove this somehow by making the state machine even more explicit
    #: A sequence of commands to replay if we end up restarting the connection.
    _if_replaying: Sequence[Command[Any]] = ()

    async def _get_back_up_to_date(self):
        for each in self._if_replaying:
            await self.request(each)  # TODO: response assert?

    async def transition(
        self,
        cmd: Command[R],
        resources: Sequence[SchemaResource] = (),
    ) -> tuple[Self, R | None]:
        response = await self.request(cmd)
        harness = evolve(
            self,
            if_replaying=[*self._if_replaying, cmd],
            resources_for_validation=resources,
        )
        return harness, response

    async def request(self, cmd: Command[R]) -> R | None:
        """
        Send a given command to the implementation and return its response.
        """
        validate = self._make_validator(*self._resources_for_validation)
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
    implementation: ImplementationId
    _harness: HarnessClient = field(repr=False, alias="harness")

    @classmethod
    async def for_dialect(
        cls,
        dialect: Dialect,
        implementation: ImplementationId,
        harness: HarnessClient,
        reporter: Reporter,
    ):
        new_harness: HarnessClient
        response: StartedDialect
        new_harness, response = await harness.transition(
            DialectCommand(dialect=str(dialect.uri)),  # type: ignore[reportArgumentType]
            resources=[dialect.current_dialect_resource()],
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

    info: ImplementationInfo
    _harness: HarnessClient = field(repr=False, alias="harness")
    _reporter: Reporter = field(alias="reporter")

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        id: ImplementationId,
        reporter: Reporter,
        **kwargs: Any,
    ) -> AsyncIterator[Self]:
        _harness = HarnessClient(**kwargs)

        try:
            harness, started = await _harness.transition(START_V1)  # type: ignore[reportArgumentType]
        except ProtocolError as err:
            raise StartupFailed(name=id) from err
        except GotStderr as err:
            raise StartupFailed(name=id, stderr=err.stderr.decode()) from err
        else:
            if started is None:
                raise StartupFailed(name=id)

        info = ImplementationInfo.from_dict(image=id, **started.implementation)  # type: ignore[reportUnknownArgumentType]

        yield cls(harness=harness, info=info, reporter=reporter)

        await _harness.poison()

    @property
    def name(self):
        return self.info.id

    async def validate(
        self,
        dialect: Dialect,
        cases: Iterable[TestCase],
    ) -> AsyncIterator[tuple[TestCase, SeqResult]]:
        """
        Run a collection of test cases under the given dialect.
        """
        runner = await self.start_speaking(dialect)
        for seq_case in SeqCase.for_cases(cases):
            yield seq_case.case, await seq_case.run(runner=runner)

    def start_speaking(self, dialect: Dialect) -> Awaitable[DialectRunner]:
        return DialectRunner.for_dialect(
            implementation=self.name,
            dialect=dialect,
            harness=self._harness,
            reporter=self._reporter,
        )

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
                    schema={"$schema": str(dialect.uri)},
                    tests=[
                        Test(
                            description=json_type,
                            instance=instance,
                            valid=True,
                        )
                        for json_type, instance in instances
                    ],
                ),
                TestCase(
                    description="allow-nothing",
                    schema={"$schema": str(dialect.uri), "not": {}},
                    tests=[
                        Test(
                            description=json_type,
                            instance=instance,
                            valid=False,
                        )
                        for json_type, instance in instances
                    ],
                ),
            ]

            yield dialect, self.validate(dialect=dialect, cases=cases)


@frozen
class Test:
    description: str
    instance: Any
    comment: str | None = None
    valid: bool | None = None


@frozen
class Group:
    description: str
    children: Sequence[ChildTests]
    comment: str | None = None
    registry: SchemaRegistry = EMPTY_REGISTRY


@frozen
class LeafGroup:
    description: str
    schema: Schema
    children: Sequence[Test]
    comment: str | None = None
    registry: SchemaRegistry = EMPTY_REGISTRY


ChildTests = Group | LeafGroup


@frozen
class TestCase:
    description: str
    schema: Any
    tests: list[Test]
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
            default_specification=specification_with(
                str(dialect),
                default=Specification.OPAQUE,
            ),
        )
        return cls(
            tests=[Test(**test) for test in tests],
            registry=populated,
            **kwargs,
        )

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
