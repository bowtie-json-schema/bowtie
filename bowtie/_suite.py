"""
Peculiarities related to how the official JSON Schema Test Suite is structured.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from fnmatch import fnmatch
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, cast
import json
import os
import zipfile

from diagnostic import DiagnosticError
from url import URL, RelativeURLWithoutBase
import click
import rich

from bowtie import GITHUB, _github
from bowtie._core import Dialect, TestCase

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any


TEST_SUITE_URL = GITHUB / "json-schema-org/JSON-Schema-Test-Suite"
TESTS_DIR_URL = TEST_SUITE_URL / "tree/main/tests"

URL_FOR_DIALECT = {
    dialect: TESTS_DIR_URL / dialect.short_name for dialect in Dialect.known()
}

ANNOTATIONS_DIR_URL = TEST_SUITE_URL / "tree/main/annotations/tests"

# Magic constants assumed/used by the official test suite for $ref tests
SUITE_REMOTE_BASE_URI = URL.parse("http://localhost:1234")


class ClickParam(click.ParamType):
    """
    A command line parameter which loads tests from the official test suite.
    """

    def __init__(self, is_annotations: bool = False):
        self._is_annotations = is_annotations
        kind = "annotation test cases" if is_annotations else "test cases"
        self.name = f"json-schema-org/JSON-Schema-Test-Suite {kind}"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any]]:
        if not isinstance(value, str):
            return value

        # Convert dialect URIs or shortnames to test suite URIs
        input_dialect = Dialect.by_alias().get(value)
        known_dialect = input_dialect if self._is_annotations else None
        if self._is_annotations and input_dialect is not None:
            value = ANNOTATIONS_DIR_URL
        else:
            value = input_dialect or value
            value = URL_FOR_DIALECT.get(value, value)

        def local(
            path: Path,
        ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any]]:
            dialect, cases = self._cases_and_dialect(
                path=path,
                ctx=ctx,
                known_dialect=known_dialect,
            )
            return cases, dialect, {}

        # On Windows, drive-letter paths like D:\... are misinterpreted by
        # URL.parse() as having a URL scheme (the drive letter).  Use
        # splitdrive() to catch these before attempting URL parsing.
        if isinstance(value, str) and (
            os.path.splitdrive(value)[0] or Path(value).exists()
        ):
            return local(Path(value))

        try:
            with suppress(TypeError):
                value = URL.parse(value)
        except RelativeURLWithoutBase:
            return local(Path(value))

        value = cast("URL", value)
        org, repo_name, *rest = value.path_segments
        path, ref = path_and_ref_from_gh_path(rest)

        downloaded = _github.download_tree(org, repo_name, ref)
        if downloaded is None:
            message = "Fetching the test suite from GitHub failed."
            error = DiagnosticError(
                code="suite-fetch-failed",
                message=message,
                causes=[
                    f"Retrieved the tree {ref}",
                    f"Tried to download {path} from within it.",
                ],
                hint_stmt=(
                    f"Check that {ref} is an existing branch and that "
                    "you have passed the right path to test cases."
                ),
                note_stmt="You also can pass a local path to test cases.",
            )
            rich.print(error)
            return self.fail(message)
        data, run_metadata = downloaded
        with zipfile.ZipFile(data) as zf:
            (contents,) = zipfile.Path(zf).iterdir()
            dialect, cases = self._cases_and_dialect(
                path=contents / path,
                ctx=ctx,
                known_dialect=known_dialect,
            )
            cases = list(cases)
        return cases, dialect, run_metadata

    def _cases_and_dialect(
        self,
        path: Any,
        ctx: click.Context | None,
        known_dialect: Dialect | None = None,
    ):
        if path.name.endswith(".json"):
            paths, version_path = [path], path.parent
        else:
            paths, version_path = _glob(path, "*.json"), path

        dialect = known_dialect
        if dialect is None:
            dialect = Dialect.by_short_name().get(version_path.name)
        if dialect is None and ctx is not None:
            dialect = ctx.params.get("dialect")
        if dialect is None:
            self.fail(f"{path} does not contain JSON Schema Test Suite cases.")

        if self._is_annotations:
            cases = annotation_cases_from(paths=paths, dialect=dialect)
        else:
            remotes = version_path.parent.parent / "remotes"
            cases = cases_from(paths=paths, remotes=remotes, dialect=dialect)

        return dialect, cases


_P = Path | zipfile.Path


def _remotes_in(path: Path, dialect: Dialect) -> Iterable[tuple[URL, Any]]:
    # This messy logic is because the test suite is terrible at indicating
    # what remotes are needed for what drafts, and mixes in schemas which
    # have no $schema and which are invalid under earlier versions, in with
    # other schemas which are needed for tests.
    #
    # FIXME: #40: for draft-next support

    for each in _rglob(path, "*.json"):
        schema = json.loads(each.read_bytes())

        relative = str(_relative_to(each, path)).replace("\\", "/")

        if (
            ("$schema" in schema and schema["$schema"] != str(dialect.uri))
            or (  # draft<NotThisDialect>/*.json
                relative.startswith("draft")
                and not relative.startswith(dialect.short_name)
            )
            or (  # invalid boolean schema
                not dialect.has_boolean_schemas and relative == "tree.json"
            )
        ):
            continue
        yield SUITE_REMOTE_BASE_URI / relative, schema


@cache
def remotes_in(path: Path, dialect: Dialect) -> dict[str, Any]:
    return {str(k): v for k, v in _remotes_in(path=path, dialect=dialect)}


def cases_from(
    paths: Iterable[_P],
    remotes: Path,
    dialect: Dialect,
) -> Iterable[TestCase]:
    for path in paths:
        if path.stem in {"refRemote", "dynamicRef", "vocabulary"}:
            registry = remotes_in(remotes, dialect=dialect)
        else:
            registry = {}

        for case in json.loads(path.read_bytes()):
            for test in case["tests"]:
                test["instance"] = test.pop("data")
            case.pop("specification", None)  # we do nothing with this now
            yield TestCase.from_dict(
                dialect=dialect,
                registry=registry,
                **case,
            )


# The version tokens the suite's compatibility grammar allows.
# Some are drafts Bowtie does not support.
# 9999 is a placeholder marking tests needing a draft which does not exist.
_COMPATIBILITY_VERSIONS = {
    str(each): each for each in (1, 2, 3, 4, 6, 7, 2019, 2020, 9999)
}


def _is_compatible(dialect: Dialect, compatibility: str | None) -> bool:
    if compatibility is None:
        return True

    version = int(dialect.short_name.removeprefix("draft").partition("-")[0])

    # Constraints naming an unknown version are never satisfied, not ignored.
    for constraint in compatibility.split(","):
        constraint = constraint.strip()
        if constraint.startswith("<="):
            bound = _COMPATIBILITY_VERSIONS.get(constraint[2:])
            satisfied = bound is not None and version <= bound
        elif constraint.startswith(">="):
            bound = _COMPATIBILITY_VERSIONS.get(constraint[2:])
            satisfied = bound is not None and version >= bound
        elif constraint.startswith("="):
            bound = _COMPATIBILITY_VERSIONS.get(constraint[1:])
            satisfied = bound is not None and version == bound
        else:
            bound = _COMPATIBILITY_VERSIONS.get(constraint)
            satisfied = bound is not None and version >= bound
        if not satisfied:
            return False
    return True


def annotation_cases_from(
    paths: Iterable[_P],
    dialect: Dialect,
) -> Iterable[TestCase]:
    for path in paths:
        data = json.loads(path.read_text())
        if "suite" not in data:
            continue
        for case in data["suite"]:
            compatibility = case.get("compatibility")
            if not _is_compatible(dialect, compatibility):
                continue

            tests: list[dict[str, Any]] = []
            for test in case["tests"]:
                assertions: list[dict[str, Any]] = []
                for assertion in test.get("assertions", []):
                    keyword = assertion["keyword"]
                    # The suite keys these by containing subschema location.
                    # Bowtie uses the location of the keyword itself.
                    expected = {
                        f"{location}/{keyword}": value
                        for location, value in assertion.get(
                            "expected",
                            {},
                        ).items()
                    }
                    assertions.append(
                        {
                            "instanceLocation": assertion.get("location", ""),
                            "keyword": keyword,
                            "expected": expected,
                        },
                    )
                tests.append(
                    {
                        "description": test.get("description", ""),
                        "instance": test["instance"],
                        "assertions": assertions,
                    },
                )

            if not tests:
                continue

            yield TestCase.from_dict(
                dialect=dialect,
                description=case["description"],
                schema=case["schema"],
                registry=case.get("externalSchemas", {}),
                tests=tests,
            )


def path_and_ref_from_gh_path(path: list[str]) -> tuple[str, str]:
    # Scan for the suite's root directories from the end.
    # Splitting at the first match breaks refs containing a tests segment.
    for root in "annotations", "tests":
        if root in path:
            i = len(path) - 1 - path[::-1].index(root)
            # remove tree/ or blob/ from the front of the ref
            return "/".join(path[i:]).rstrip("/"), "/".join(path[1:i])
    return "", "/".join(path[1:]).rstrip("/")


# Missing zipfile.Path methods...
def _glob(path: _P, path_pattern: str) -> Iterable[_P]:
    return (  # It's missing .match() too, so we fnmatch directly
        each for each in path.iterdir() if fnmatch(each.name, path_pattern)
    )


def _rglob(path: _P, path_pattern: str) -> Iterable[_P]:
    for each in path.iterdir():
        if fnmatch(each.name, path_pattern):
            yield each
        elif each.is_dir():
            yield from _rglob(each, path_pattern)


def _relative_to(path: _P, other: Path) -> Path:
    if hasattr(path, "relative_to"):
        return path.relative_to(other)  # type: ignore[reportGeneralTypeIssues]
    return Path(path.at).relative_to(other.at)  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]


#: The default git ref of the official suite to collect test cases from.
DEFAULT_REF = "main"


class SuiteNotAvailable(Exception):
    """
    The official test suite could not be retrieved from GitHub.
    """

    def __init__(self, ref: str):
        super().__init__(ref)
        self.ref = ref

    def diagnostic(self) -> DiagnosticError:
        return DiagnosticError(
            code="suite-fetch-failed",
            message="Fetching the test suite from GitHub failed.",
            causes=[f"Tried to retrieve the tree at {self.ref!r}."],
            hint_stmt=(
                f"Check that {self.ref!r} is an existing branch, tag or "
                "commit of the suite, or pass a local path to a checkout "
                "of it instead."
            ),
        )


def hour_start() -> datetime:
    """
    The start of the current hour, in UTC.

    Pinning the suite to this makes the choice deterministic within any
    given hour, so independent runs in the same hour collect against -- and
    can therefore be combined at -- the same commit, with no coordination
    needed between them.
    """
    return datetime.now(tz=UTC).replace(
        minute=0,
        second=0,
        microsecond=0,
    )


def download(ref: str | None = None) -> tuple[_P, dict[str, Any]]:
    """
    Download the whole official test suite once.

    With no ``ref``, the suite is pinned to the newest commit on its main
    branch at or before the start of the current hour -- a deterministic
    choice, so that independent runs within the same hour all collect
    against (and can therefore be combined at) the same commit. Pass an
    explicit ref (a branch, tag or commit) to override.

    Returns the suite's root directory (which contains ``tests/`` and
    ``remotes/``) alongside run metadata recording the exact commit.
    Every dialect collected from this one root is therefore guaranteed to
    share a single consistent commit, even if the suite moves meanwhile.
    """
    owner, name, *_ = cast("list[str]", TEST_SUITE_URL.path_segments)

    if ref is None:
        ref = (
            _github.latest_commit_before(
                owner,
                name,
                DEFAULT_REF,
                hour_start(),
            )
            or DEFAULT_REF
        )

    downloaded = _github.download_tree(owner, name, ref)
    if downloaded is None:
        raise SuiteNotAvailable(ref)
    data, run_metadata = downloaded
    (root,) = zipfile.Path(zipfile.ZipFile(data)).iterdir()

    return root, run_metadata


def dialects_in(root: _P) -> set[Dialect]:
    """
    Which dialects the suite rooted at the given path provides cases for.
    """
    by_short = Dialect.by_short_name()
    return {
        by_short[child.name]
        for child in (root / "tests").iterdir()
        if child.is_dir() and child.name in by_short
    }


def cases_for(root: _P, dialect: Dialect) -> Iterable[TestCase]:
    """
    The test cases for a single dialect within the suite at the given root.
    """
    version_path = root / "tests" / dialect.short_name
    return cases_from(
        paths=list(_glob(version_path, "*.json")),
        remotes=cast("Path", root / "remotes"),
        dialect=dialect,
    )
