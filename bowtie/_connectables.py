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
from bowtie._direct_connectable import Direct, NoDirectConnection

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


def happy(id: str) -> Connector:
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
    except NoDirectConnection:
        return _containers.ConnectableImage(id=id)


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


@frozen
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
            connector = Connector(id)
        elif "/" in kind:  # special case allowing foo/bar:baz, image w/repo
            connector = CONNECTORS["image"](fqid)
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
        return Connectable.from_str(value)

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
