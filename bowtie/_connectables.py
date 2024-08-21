"""
Connectables implement a mini-language for connecting to supported harnesses.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, Any, Protocol

from attrs import field, frozen
from click.shell_completion import CompletionItem
from rpds import HashTrieMap
import click

from bowtie import _containers
from bowtie._core import Implementation
from bowtie._direct_connectable import Direct
from bowtie.exceptions import CannotConnect

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from contextlib import AbstractAsyncContextManager

    from bowtie._core import Connection


class UnknownConnector(Exception):
    """
    The connector provided does not exist.
    """


class Connector(Protocol):

    kind: str

    def connect(self) -> AbstractAsyncContextManager[Connection]: ...


#: A string identifying an implementation supporting Bowtie's harness protocol.
#: Connectable IDs should be unique within a run or report.
ConnectableId = str


def happy(id: str, **params: Any) -> Connector:
    """
    A happy (eyeballs) connector.

    Connectables using the Happy connector will connect directly if possible,
    or otherwise if not, will fallback to the image connector.

    This behavior connects "as quickly/reliably as possible" to any
    implementation supporting direct connection, and otherwise still ensures
    connection to any implementation where that isn't possible.

    The name is inspired by the Happy Eyeballs algorithm in networking.
    """
    try:
        return Direct.from_id(id=id)
    except CannotConnect as err:
        # FIXME: we seem to have trouble differentiating here between
        #        'we know which implementation that is but something is still
        #        wrong' and 'we don't know what implementation that is'.
        #        Specifically, using .hint to check seems off.
        if err.hint is not None:
            raise
        return _containers.ConnectableImage(id=id, **params)


CONNECTORS = HashTrieMap(
    [
        ("happy", happy),
        (Direct.kind, Direct.from_id),
        (_containers.ConnectableImage.kind, _containers.ConnectableImage),
        (
            _containers.ConnectableContainer.kind,
            _containers.ConnectableContainer,
        ),
    ],
)


def _params(with_params: str) -> tuple[tuple[str, ...], dict[str, str]]:
    args: list[str] = []
    kwargs: dict[str, str] = {}
    split = iter(with_params.split(","))

    for each in split:
        k, sep, v = each.partition("=")
        if not sep:
            args.append(k)
        else:
            kwargs[k] = v
            break
    for each in split:
        k, sep, v = each.partition("=")
        kwargs[k] = v

    return tuple(args), kwargs


@frozen(kw_only=True)
class Connectable:
    """
    A parsed connectable description.

    In this internal codebase and in docstrings, "connectable" refers to
    instances of this object, and we use "connectable description" to refer
    to the string which specifies the connectable.

    In user-facing documentation, we simplify talking about connectables by
    simply referring to the string as being the connectable itself.
    """

    _id: ConnectableId = field(alias="id", repr=False, eq=False)
    _connector: Connector = field(alias="connector")

    @classmethod
    def from_str(cls, fqid: ConnectableId):
        kind, sep, id = fqid.partition(":")
        if not sep:
            kind, id = "happy", kind
        Connector = CONNECTORS.get(kind)
        if Connector is not None:
            id, sep, raw_params = id.partition(":")
            if sep:
                args, kwargs = _params(raw_params)
                if len(args) == 1:
                    id, args = f"{id}:{args[0]}", ()
                connector = Connector(*args, id=id, **kwargs)
            else:
                connector = Connector(id=id)
        elif "/" in kind:  # special case allowing foo/bar:baz, image w/repo
            connector = CONNECTORS["image"](id=fqid)
        else:
            raise UnknownConnector(kind)
        return cls(id=fqid, connector=connector)

    @property
    def kind(self):
        return self._connector.kind

    @asynccontextmanager
    async def connect(self, **kwargs: Any) -> AsyncIterator[Implementation]:
        async with (
            self._connector.connect() as connection,
            Implementation.start(
                id=self._id,
                connection=connection,
                **kwargs,
            ) as implementation,
        ):
            yield implementation

    def to_terse(self) -> ConnectableId:
        """
        The tersest connectable description someone could write.
        """
        return self._id.removeprefix("image:").removeprefix(
            f"{_containers.IMAGE_REPOSITORY}/",
        )


class ClickParam(click.ParamType):
    """
    Select a supported Bowtie implementation by its connectable string.
    """

    name = "implementation"

    def convert(
        self,
        value: str,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> Connectable:
        try:
            return Connectable.from_str(value)
        except CannotConnect as err:
            if err.hint is None:
                raise
            raise click.BadParameter(err.hint)

    def shell_complete(
        self,
        ctx: click.Context,
        param: click.Parameter,
        incomplete: str,
    ) -> list[CompletionItem]:
        # FIXME: All supported Connectable values
        return [
            CompletionItem(name)
            for name in Implementation.known()
            if name.startswith(incomplete.lower())
        ]
