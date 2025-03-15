from __future__ import annotations

from contextlib import asynccontextmanager, suppress
from datetime import date
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, cast
from uuid import uuid4
import json
import os

from attrs import Factory, asdict, evolve, field, frozen, mutable
from referencing.jsonschema import EMPTY_REGISTRY, specification_with
from rpds import HashTrieMap, HashTrieSet
from url import URL
import httpx
import referencing_loaders

from bowtie import HOMEPAGE, ORG_NAME
from bowtie._commands import (
    START_V1,
    CaseErrored,
    Dialect as DialectCommand,
    SeqCase,
    SeqResult,
    StartedDialect,
)
from bowtie.exceptions import (
    DialectError,
    GotStderr,
    InvalidResponse,
    ProtocolError,
    StartupFailed,
    UnsupportedDialect,
)

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
    from rich.console import RenderableType

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

ORG_API = URL.parse("https://api.github.com/orgs/") / ORG_NAME
CONTAINER_PACKAGES_API = ORG_API / "packages" / "container"


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
        default=cast("frozenset[str]", frozenset()),
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

        return HashTrieSet(
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
        url = URL.parse(uri)
        by_uri = cls.by_uri()

        if url.fragment is None:
            dialect = by_uri.get(url.with_fragment(""))
            if dialect is not None:
                return dialect

        return by_uri[url]

    async def latest_report(self):
        url = HOMEPAGE / f"{self.short_name}.json"
        async with httpx.AsyncClient(timeout=10) as client:
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


class Restarted(Exception):
    """
    A connection was restarted, so we may need to replay some messages.
    """


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

    async def transition[R](self, cmd: Command[R]) -> tuple[Self, R | None]:
        response = await self.request(cmd)
        harness = evolve(self, if_replaying=[*self._if_replaying, cmd])
        return harness, response

    async def request[R](self, cmd: Command[R]) -> R | None:
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
            response: tuple[Seq, int, AnyCaseResult] | None = (
                await self._harness.request(run)  # type: ignore[reportArgumentType]
            )
            if response is None:
                result = CaseErrored.uncaught()
            else:
                seq, length, result = response
                if seq != run.seq:
                    result = CaseErrored.uncaught(
                        message="mismatched seq",
                        expected=run.seq,
                        got=seq,
                        response=result,
                    )
                elif length and length != len(expected):
                    result = CaseErrored.uncaught(
                        message="wrong number of responses",
                        expected=len(expected),
                        got=length,
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
            result=result,  # type: ignore[reportUnknownArgumentType]  # pyright seems confused
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

    def supports(self, *dialects: Dialect) -> bool:
        """
        Does the implementation support (all of) the given dialect(s)?
        """
        return self.info.dialects.issuperset(dialects)

    async def get_versions(self) -> Iterable[str]:
        from github3.exceptions import (  # type: ignore[reportMissingTypeStubs]
            GitHubError,
        )
        from github3.models import (  # type: ignore[reportMissingTypeStubs]
            GitHubCore,
        )

        url = CONTAINER_PACKAGES_API / self.id / "versions"

        gh = github()
        pages: list[GitHubCore] = []
        with suppress(GitHubError):
            pages = gh._iter(count=-1, url=str(url), cls=GitHubCore)  # type: ignore[reportPrivateUsage]

        versions: Set[str] = (
            {self.info.version} if self.info.version else set()
        )
        for page in pages:
            try:
                tags = cast(
                    "Iterable[str]",
                    page.as_dict()["metadata"]["container"]["tags"],
                )
            except KeyError:
                continue
            else:
                versions.update([tag for tag in tags if "." in tag])

        return sorted(versions, key=sortable_version_key, reverse=True)

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

    def smoke(self):
        """
        Smoke test this implementation.
        """
        from bowtie import _smoke

        return _smoke.test(self)


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
        instance: Any = None,
        valid: bool | None = None,
        **data: Any,
    ) -> Example | Test:
        if valid is None:
            return cls(**data, instance=instance)
        return Test(**data, instance=instance, valid=valid)


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


def convert_table_to_markdown(
    columns: list[str],
    rows: list[list[str]],
):
    widths = [max(len(row[i]) for row in rows) for i in range(len(columns))]
    rows = [[elt.center(w) for elt, w in zip(line, widths)] for line in rows]

    header = "| " + " | ".join(columns) + " |"
    border_left = "|:"
    border_center = ":|:"
    border_right = ":|"

    separator = (
        border_left
        + border_center.join(["-" * w for w in widths])
        + border_right
    )

    # body of the table
    body = [""] * len(rows)  # empty string list that we fill after
    for idx, line in enumerate(rows):
        # for each line, change the body at the correct index
        body[idx] = "| " + " | ".join(line) + " |"
    body = "\n".join(body)

    return f"\n{header}\n{separator}\n{body}"


def sortable_version_key(version: str):
    """
    Generate a sortable key for version strings like "1.2.3".
    """
    parts = version.split(".")
    return [int(part) if part.isdigit() else part for part in parts]


def github():
    """
    Construct a GitHub client, optionally looking for a token.

    This extra behavior is just useful in GitHub actions workflows, and
    presumably if ``github3.py`` was more active would be default behavior.
    """
    from github3 import GitHub  # type: ignore[reportMissingTypeStubs]

    return GitHub(token=os.environ.get("GITHUB_TOKEN", ""))
