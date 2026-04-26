import io

from rich.console import Console
import pytest
import pytest_asyncio

from bowtie import _report
from bowtie._connectables import Connectable
from bowtie._direct_connectable import Direct
from bowtie._tui import TuiSession, _is_schema_like, _parse_json


def _silent_console() -> Console:
    return Console(file=io.StringIO(), highlight=False)


def _test_prompt(inputs: list[str]):
    it = iter(inputs)

    def prompt(msg: str) -> str:
        try:
            return next(it)
        except StopIteration:
            raise EOFError from None

    return prompt


def test_parse_json_invalid_raises_value_error():
    with pytest.raises(ValueError, match="Expecting property name"):
        _parse_json("{not valid json")


def test_is_schema_like_rejects_string():
    assert _is_schema_like("hello") is False


@pytest.fixture
def dialect():
    from bowtie._core import Dialect

    return Dialect.by_short_name()["draft2020-12"]


@pytest_asyncio.fixture
async def session(dialect):
    """
    A TuiSession backed by python-jsonschema DialectRunner.
    No Docker. No terminal
    """
    silent = _report.Reporter(write=lambda **_: None)
    registry = Direct.from_id("python-jsonschema").registry()
    connectable = Connectable.from_str("python-jsonschema")

    async with connectable.connect(reporter=silent, registry=registry) as impl:
        runner = await impl.start_speaking(dialect)
        yield TuiSession(
            runners=[(impl.id, impl.info.version or "?", runner)],
            dialect=dialect,
            console=_silent_console(),
            prompt=lambda _: (_ for _ in ()).throw(EOFError()),
        )


@pytest.mark.asyncio
async def test_run_once_valid_instance(session):
    results = await session.run_once(
        schema={"type": "integer"},
        instance=42,
    )
    assert len(results) == 1
    impl_id, _version, valid = results[0]
    assert valid is True
    assert "jsonschema" in impl_id


@pytest.mark.asyncio
async def test_run_once_invalid_instance(session):
    results = await session.run_once(
        schema={"type": "integer"},
        instance="not an integer",
    )
    assert len(results) == 1
    _, _, valid = results[0]
    assert valid is False


@pytest.mark.asyncio
async def test_repl_exits_on_q(session):
    session._prompt = _test_prompt(["q"])
    await session.repl()


@pytest.mark.asyncio
async def test_repl_non_schema_json_continues(session):
    session._prompt = _test_prompt(['"just a string"', "q"])
    await session.repl()


@pytest.mark.asyncio
async def test_repl_validates_and_continues(session):
    session._prompt = _test_prompt(
        [
            '{"type": "integer"}',
            "42",
            '{"type": "integer"}',
            '"hello"',
            "q",
        ],
    )
    await session.repl()
