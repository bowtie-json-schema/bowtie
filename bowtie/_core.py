from __future__ import annotations

from contextlib import asynccontextmanager, suppress
from typing import TYPE_CHECKING, Any, Protocol, TypeVar
import asyncio
import json

from aiodocker.exceptions import DockerError
from attrs import asdict, field, frozen, mutable
from referencing import Specification
from referencing.jsonschema import (
    EMPTY_REGISTRY,
    Schema,
    SchemaRegistry,
    specification_with,
)
from url import URL

from bowtie import _commands, exceptions
from bowtie._containers import (
    GotStderr,
    NoSuchImage,
    StartupFailed,
    Stream,
    StreamClosed,
)

if TYPE_CHECKING:
    from collections.abc import (
        AsyncIterator,
        Awaitable,
        Callable,
        Iterable,
        Mapping,
        Set,
    )

    from referencing.jsonschema import SchemaResource
    import aiodocker.containers
    import aiodocker.docker
    import aiodocker.stream

    from bowtie._report import Reporter


DRAFT2020 = URL.parse("https://json-schema.org/draft/2020-12/schema")
DRAFT2019 = URL.parse("https://json-schema.org/draft/2019-09/schema")
DRAFT7 = URL.parse("http://json-schema.org/draft-07/schema#")
DRAFT6 = URL.parse("http://json-schema.org/draft-06/schema#")
DRAFT4 = URL.parse("http://json-schema.org/draft-04/schema#")
DRAFT3 = URL.parse("http://json-schema.org/draft-03/schema#")


class _InvalidResponse:
    def __repr__(self) -> str:
        return "<InvalidResponse>"


INVALID = _InvalidResponse()

R = TypeVar("R")


@frozen
class DialectRunner:
    implementation: _commands.ImplementationId
    dialect: URL
    send: Callable[[_commands.Command[Any]], Awaitable[Any]]
    _start_response: _commands.StartedDialect = field(alias="start_response")

    @classmethod
    async def start(
        cls,
        send: Callable[[_commands.Command[R]], Awaitable[R]],
        dialect: URL,
        implementation: _commands.ImplementationId,
    ) -> DialectRunner:
        request = _commands.Dialect(dialect=str(dialect))
        return cls(
            implementation=implementation,
            send=send,
            dialect=dialect,
            start_response=await send(request),  # type: ignore[reportGeneralTypeIssues]  # uh?? no idea what's going on here.
        )

    def warn_if_unacknowledged(self, reporter: Reporter):
        if self._start_response != _commands.StartedDialect.OK:
            reporter.unacknowledged_dialect(
                implementation=self.implementation,
                dialect=self.dialect,
                response=self._start_response,
            )


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

    _image: _commands.ImplementationId = field(alias="image")

    name: str
    language: str
    homepage: URL
    issues: URL
    source: URL
    dialects: Set[URL]

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
            dialects=frozenset(URL.parse(dialect) for dialect in dialects),
            links=[Link.from_dict(**each) for each in links],
            **kwargs,
        )

    @property
    def id(self) -> _commands.ImplementationId:
        return self._image

    def serializable(self):
        as_dict = {
            k: v
            for k, v in asdict(self).items()
            if not k.startswith("_") and v
        }
        dialects = (str(d) for d in as_dict["dialects"])
        as_dict.update(
            homepage=str(as_dict["homepage"]),
            issues=str(as_dict["issues"]),
            source=str(as_dict["source"]),
            dialects=sorted(dialects, reverse=True),
            links=[link.serializable() for link in self.links],
        )
        return as_dict


@mutable
class Implementation:
    """
    A running implementation under test.
    """

    name: str

    # TODO: Potential areas to split this class up on

    # Request/response validation -- probably can wrap protocol
    _make_validator: _MakeValidator = field(alias="make_validator")
    _maybe_validate: Callable[..., None] = field(alias="maybe_validate")

    # Error reporting
    _reporter: Reporter = field(alias="reporter")

    # Low level network / communication
    _docker: aiodocker.docker.Docker = field(repr=False, alias="docker")
    _stream: Stream = field(default=None, repr=False, alias="stream")

    # Possibly also related to the above networking, but also potentially
    # useful for not waiting forever for results that really will complete
    _read_timeout_sec: float | None = field(
        default=2.0,
        converter=lambda value: value or None,  # type: ignore[reportUnknownArgumentType]
        repr=False,
    )

    # Protocol fragile-ness, but also tolerance for how broken an
    # implementation is
    _restarts: int = field(default=20, repr=False, alias="restarts")

    _info: ImplementationInfo | None = None

    # FIXME: Still some refactoring into DialectRunner needed.
    _dialect: URL = None  # type: ignore[reportGeneralTypeIssues]

    @classmethod
    @asynccontextmanager
    async def start(
        cls,
        image_name: str,
        make_validator: _MakeValidator,
        **kwargs: Any,
    ) -> AsyncIterator[Implementation]:
        self = cls(
            name=image_name,
            make_validator=make_validator,
            maybe_validate=make_validator(),
            **kwargs,
        )

        try:
            await self._start_container()
        except GotStderr as error:
            err = StartupFailed(name=image_name, stderr=error.stderr.decode())
            raise err from None
        except StreamClosed:
            raise StartupFailed(name=image_name) from None
        except DockerError as err:
            # This craziness can go wrong in various ways, none of them
            # machine parseable.

            status, data, *_ = err.args
            if data.get("cause") == "image not known":
                raise NoSuchImage(name=image_name, data=data) from err

            message = ghcr = data.get("message", "")

            if status == 500:  # noqa: PLR2004
                try:
                    # GitHub Registry saying an image doesn't exist as reported
                    # within GitHub Actions' version of Podman...
                    # This is some crazy string like:
                    #   Get "https://ghcr.io/v2/bowtie-json-schema/image-name/tags/list": denied  # noqa: E501
                    # with seemingly no other indication elsewhere and
                    # obviously no real good way to detect this specific case
                    no_image = message.endswith('/tags/list": denied')
                except Exception:  # noqa: BLE001, S110
                    pass
                else:
                    if no_image:
                        raise NoSuchImage(name=image_name, data=data)

                try:
                    # GitHub Registry saying an image doesn't exist as reported
                    # locally via podman on macOS...

                    # message will be ... a JSON string !?! ...
                    error = json.loads(ghcr).get("message", "")
                except Exception:  # noqa: BLE001, S110
                    pass  # nonJSON / missing key
                else:
                    if "403 (forbidden)" in error.casefold():
                        raise NoSuchImage(name=image_name, data=data)

            raise StartupFailed(name=image_name, data=data) from err

        yield self
        await self._stop()

    async def _start_container(self):
        container = await self._docker.containers.run(  # type: ignore[reportUnknownMemberType]
            config=dict(
                Image=self.name,
                OpenStdin=True,
                HostConfig=dict(NetworkMode="none"),
            ),
        )
        self._stream = Stream.attached_to(
            container,
            read_timeout_sec=self._read_timeout_sec,
        )
        started: _commands.Started = await self._send(_commands.START_V1)  # type: ignore[reportGeneralTypeIssues]  # uh?? no idea what's going on here.
        if started is INVALID:
            raise StartupFailed(name=self.name)
        self._info = ImplementationInfo.from_dict(
            image=self.name,
            **started.implementation,
        )

    def info(self) -> ImplementationInfo:
        # FIXME: Do this higher up
        if self._info is None:
            raise StartupFailed(name=self.name)
        return self._info

    def start_speaking(self, dialect: URL) -> Awaitable[DialectRunner]:
        self._dialect = dialect
        current_dialect = current_dialect_resource(dialect)
        self._maybe_validate = self._make_validator(current_dialect)
        return DialectRunner.start(
            implementation=self.name,
            send=self._send,
            dialect=dialect,
        )

    async def _stop(self):
        request = _commands.STOP.to_request(validate=self._maybe_validate)  # type: ignore[reportUnknownMemberType]  # uh?? no idea what's going on here.
        with suppress(StreamClosed):
            await self._stream.send(request)  # type: ignore[reportUnknownArgumentType]
        await self._stream.ensure_deleted()

    async def _send_no_response(self, cmd: _commands.Command[R]) -> None:
        request = cmd.to_request(validate=self._maybe_validate)

        try:
            await self._stream.send(request)
        except StreamClosed:
            self._restarts -= 1
            await self._stream.ensure_deleted()
            await self._start_container()
            await self.start_speaking(dialect=self._dialect)
            await self._stream.send(request)

    async def _send(
        self,
        cmd: _commands.Command[R],
        retry: int = 3,
    ) -> R | _InvalidResponse:
        await self._send_no_response(cmd)
        for _ in range(retry):
            try:
                response = await self._stream.receive()
            except asyncio.exceptions.TimeoutError:
                continue

            try:
                return cmd.from_response(
                    response=response,
                    validate=self._maybe_validate,
                )
            except exceptions._ProtocolError as error:  # type: ignore[reportPrivateUsage]
                self._reporter.invalid_response(
                    error=error,
                    implementation=self,
                    response=response,
                    cmd=cmd,
                )
                break
        return INVALID

    async def smoke(
        self,
    ) -> AsyncIterator[tuple[_commands.SeqCase, _commands.SeqResult],]:
        """
        Smoke test this implementation.
        """
        # FIXME: All dialects / and/or newest dialect with proper sort
        dialect = max(self.info().dialects, key=str)
        runner = await self.start_speaking(dialect)

        instances = [
            ("nil", None),
            ("boolean", True),
            ("integer", 37),
            ("number", 37.37),
            ("string", "37"),
            ("array", [37]),
            ("object", {"foo": 37}),
        ]
        cases = [
            TestCase(
                description="allow-everything",
                schema={"$schema": str(dialect)},
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
                schema={"$schema": str(dialect), "not": {}},
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

        for seq_case in _commands.SeqCase.for_cases(cases):
            result = await seq_case.run(runner=runner)
            yield seq_case, result


def current_dialect_resource(dialect: URL):
    # it's of course unimportant what dialect is used for this referencing
    # schema, what matters is that the target dialect is applied
    from referencing.jsonschema import DRAFT202012

    return DRAFT202012.create_resource(
        {
            # Should match the magic value used for `schema` in `schemas/io/`
            "$id": "tag:bowtie.report,2023:ihop:__dialect__",
            "$ref": str(dialect),
        },
    )


@frozen
class Test:
    description: str
    instance: Any
    comment: str | None = None
    valid: bool | None = None


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
        dialect: URL,
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

    def serializable(self) -> dict[str, Any]:
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

    def without_expected_results(self) -> dict[str, Any]:
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
