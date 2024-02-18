"""
Hand crafted classes which should undoubtedly be autogenerated from the schema.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, TypeVar
import re

try:
    from typing import dataclass_transform
except ImportError:
    from typing_extensions import dataclass_transform

from attrs import asdict, field, frozen

from bowtie import HOMEPAGE, exceptions

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Mapping, Sequence
    from typing import ClassVar, Self

    from structlog.stdlib import BoundLogger

    from bowtie._core import DialectRunner, TestCase


#: A unique identifier for a test case within a run or report.
Seq = int

#: A unique identifier for an implementation within a run or report.
ImplementationId = str

#: A JSON representation of the command
Message = dict[str, Any]


@frozen
class Unsuccessful:
    failed: int = 0
    errored: int = 0
    skipped: int = 0

    def __add__(self, other: Unsuccessful):
        return Unsuccessful(
            failed=self.failed + other.failed,
            errored=self.errored + other.errored,
            skipped=self.skipped + other.skipped,
        )

    def __bool__(self) -> bool:  # sigh, typing nonsense
        return bool(self.failed or self.errored or self.skipped)

    @property
    def causes_stop(self) -> bool:  # sigh, typing nonsense
        return bool(self.failed or self.errored)

    @property
    def total(self):
        """
        Any test which was not a successful result, including skips.
        """
        return self.errored + self.failed + self.skipped


@frozen
class SeqCase:
    seq: Seq
    case: TestCase

    def run(self, runner: DialectRunner) -> Awaitable[SeqResult]:
        run = Run(seq=self.seq, case=self.case.without_expected_results())
        expected = [t.valid for t in self.case.tests]
        return runner.validate(run, expected=expected)

    def serializable(self):
        return dict(seq=self.seq, case=self.case.serializable())


@frozen
class Started:
    implementation: dict[str, Any]
    version: int = field(
        validator=lambda _, __, got: exceptions.VersionMismatch.check(got),
    )


R_co = TypeVar("R_co", covariant=True)


class Command(Protocol[R_co]):
    def to_request(self, validate: Callable[..., None]) -> Message: ...

    @staticmethod
    def from_response(
        response: Message,
        validate: Callable[..., None],
    ) -> R_co: ...


@dataclass_transform(frozen_default=True)
def command(
    Response: Callable[..., R_co],
    name: str = "",
) -> Callable[[type], type[Command[R_co]]]:
    def _command(cls: type) -> type[Command[R_co]]:
        nonlocal name
        if not name:
            name = re.sub(r"([a-z])([A-Z])", r"\1-\2", cls.__name__).lower()

        uri = f"tag:{HOMEPAGE.host_str},2023:ihop:command:{name}"
        request_schema = {"$ref": str(uri)}
        response_schema = {"$ref": f"{uri}#response"}  # FIXME: crate-py/url#6

        def to_request(
            self: Command[R_co],
            validate: Callable[..., None],
        ) -> Message:
            request = dict(cmd=name, **asdict(self))
            validate(instance=request, schema=request_schema)
            return request

        @staticmethod
        def from_response(
            response: Message,
            validate: Callable[..., None],
        ) -> R_co:
            validate(instance=response, schema=response_schema)
            return Response(**response)

        cls.to_request = to_request
        cls.from_response = from_response
        return frozen(cls)

    return _command


@command(Response=Started)
class Start:
    version: int


START_V1 = Start(version=1)


@frozen
class StartedDialect:
    ok: bool

    OK: ClassVar[Self]


StartedDialect.OK = StartedDialect(ok=True)


@command(Response=StartedDialect)
class Dialect:
    dialect: str


class AnyTestResult(Protocol):
    @property
    def description(self) -> str:
        """
        A single word to use when displaying this result.
        """
        ...

    @property
    def skipped(self) -> bool: ...

    @property
    def errored(self) -> bool: ...


@frozen
class TestResult:
    errored = False
    skipped = False

    valid: bool

    VALID: ClassVar[Self]
    INVALID: ClassVar[Self]

    @property
    def description(self):
        return "valid" if self.valid else "invalid"

    @classmethod
    def from_dict(cls, data: Message) -> AnyTestResult:
        if data.pop("skipped", False):
            return SkippedTest(**data)
        elif data.pop("errored", False):
            return ErroredTest(**data)
        return cls(valid=data["valid"])


TestResult.VALID = TestResult(valid=True)
TestResult.INVALID = TestResult(valid=False)


@frozen
class SkippedTest:
    message: str | None = field(default=None)
    issue_url: str | None = field(default=None)

    errored = False
    skipped: bool = field(init=False, default=True)

    description = "skipped"

    @property
    def reason(self) -> str:
        if self.message is not None:
            return self.message
        if self.issue_url is not None:
            return self.issue_url
        return "skipped"

    @classmethod
    def in_skipped_case(cls):
        """
        A skipped test which mentions it is part of an entirely skipped case.
        """
        return cls(message="All tests in this test case were skipped.")


@frozen
class ErroredTest:
    context: dict[str, Any] = field(factory=dict)

    errored: bool = field(init=False, default=True)
    skipped: bool = False

    description = "error"

    @property
    def reason(self) -> str:
        message = self.context.get("message")
        if message:
            return message
        return "Encountered an error."

    @classmethod
    def in_errored_case(cls):
        """
        A errored test which mentions it is part of an entirely errored case.
        """
        return cls(
            context=dict(message="All tests in this test case errored."),
        )


class AnyCaseResult(Protocol):
    @property
    def results(self) -> Sequence[AnyTestResult] | None: ...

    def result_for(self, i: int) -> AnyTestResult: ...

    def log(self, log: BoundLogger) -> None: ...

    def unsuccessful(
        self,
        expected: Sequence[bool | None],
    ) -> Unsuccessful: ...


def _case_result(seq: Seq, **data: Any) -> tuple[Seq, AnyCaseResult]:
    # FIXME: Remove passing seq through which is mostly to support future
    #        validation that the seq we got back is the right one
    match data:
        case {"errored": True, **data}:
            return seq, CaseErrored(**data)
        case {"skipped": True, **skip}:
            return seq, CaseSkipped(**skip)
        case _:
            return seq, CaseResult.from_results(**data)


@frozen
class SeqResult:
    """
    A result along with its corresponding metadata.

    Contains the implementation an test case it corresponds to.

    Knows how long the result was *supposed* to be, and what the expected
    validation results were supposed to be if that information was provided at
    run-time.
    """

    seq: Seq
    implementation: ImplementationId

    result: AnyCaseResult
    expected: Sequence[bool | None]

    @classmethod
    def from_dict(
        cls,
        seq: Seq,
        implementation: str,
        expected: list[bool | None],
        **data: dict[str, Any],
    ):
        _, result = _case_result(seq=seq, **data)
        return cls(
            seq=seq,
            implementation=implementation,
            expected=expected,
            result=result,
        )

    def dots(self):
        """
        Represent the result via dot glyphs.
        """
        results = self.result.results
        if results is None:
            return "".join("❗" for _ in self.expected)

        return "".join(
            (
                "✓"
                if got
                == (got if expected is None else TestResult(valid=expected))
                else "✗"
            )
            for got, expected in zip(results, self.expected)
        )

    def result_for(self, i: int) -> AnyTestResult:
        return self.result.result_for(i)

    def unsuccessful(self) -> Unsuccessful:
        return self.result.unsuccessful(expected=self.expected)

    def log_and_be_serialized(self, log: BoundLogger) -> Mapping[str, Any]:
        self.result.log(log)
        return self.serializable()

    def serializable(self):
        serializable = asdict(self)
        serializable.update(serializable.pop("result"))
        return serializable


@frozen
class CaseResult:
    """
    A test case which at least was run by the implementation.
    """

    results: list[AnyTestResult]

    @classmethod
    def from_results(cls, results: list[dict[str, Any]]):
        return cls(results=[TestResult.from_dict(t) for t in results])

    def result_for(self, i: int) -> AnyTestResult:
        return self.results[i]

    def unsuccessful(self, expected: Sequence[bool | None]) -> Unsuccessful:
        skipped = errored = failed = 0
        for test, expecting in zip(self.results, expected):
            if test.skipped:
                skipped += 1
            elif test.errored:
                errored += 1
            elif expecting is not None and test != TestResult(valid=expecting):
                failed += 1
        return Unsuccessful(skipped=skipped, failed=failed, errored=errored)

    def log(self, log: BoundLogger):
        for result in self.results:
            if result.errored:
                log.error("", **result.context)  # type: ignore[reportGeneralTypeIssues, reportUnknownMemberType]


@frozen
class CaseErrored:
    """
    A full test case errored.
    """

    results = None

    context: Mapping[str, Any] = field()
    message: str = field(default="")
    caught: bool = field(default=True)
    errored: bool = field(default=True, init=False)

    @classmethod
    def uncaught(cls, message: str = "uncaught error", **context: Any):
        return cls(caught=False, message=message, context=context)

    def result_for(self, i: int) -> ErroredTest:
        return ErroredTest.in_errored_case()

    def unsuccessful(self, expected: Sequence[bool | None]) -> Unsuccessful:
        return Unsuccessful(errored=len(expected))

    def log(self, log: BoundLogger):
        log.error(self.message, **self.context)


@frozen
class CaseSkipped:
    """
    A full test case was skipped.
    """

    results = None

    message: str | None = None
    issue_url: str | None = None
    skipped: bool = field(init=False, default=True)

    def result_for(self, i: int) -> SkippedTest:
        return SkippedTest.in_skipped_case()

    def unsuccessful(self, expected: Sequence[bool | None]) -> Unsuccessful:
        return Unsuccessful(skipped=len(expected))

    def log(self, log: BoundLogger):
        log.info(self.message or "skipped case")


@frozen
class Empty:
    """
    An implementation didn't send a response.
    """

    results = None

    def result_for(self, i: int) -> ErroredTest:
        return ErroredTest.in_errored_case()

    def log(self, log: BoundLogger):
        log.error("No response")

    def unsuccessful(self, expected: Sequence[bool | None]) -> Unsuccessful:
        return Unsuccessful(errored=len(expected))


@command(Response=_case_result)
class Run:
    seq: Seq
    case: dict[str, Any]


@command(Response=Empty)
class Stop:
    pass


STOP = Stop()
