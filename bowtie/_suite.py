"""
Peculiarities related to how the official JSON Schema Test Suite is structured.
"""

from __future__ import annotations

from contextlib import suppress
from datetime import UTC, datetime
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, cast
import json
import os
import zipfile

from diagnostic import DiagnosticError, DiagnosticWarning
from url import URL, RelativeURLWithoutBase
import click
import rich
import rich.console

from bowtie import GITHUB, _github
from bowtie._core import Dialect, TestCase

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from typing import Any


TEST_SUITE_URL = GITHUB / "json-schema-org/JSON-Schema-Test-Suite"
TESTS_DIR_URL = TEST_SUITE_URL / "tree/unify/validation/tests"

ANNOTATIONS_DIR_URL = TEST_SUITE_URL / "tree/main/annotations/tests"

_STDERR = rich.console.Console(stderr=True)


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

        # Cases cover every dialect, so where they live says nothing about
        # which to run them under. A dialect given as the input runs the
        # suite from GitHub under it, otherwise --dialect says which.
        dialect = Dialect.by_alias().get(value)
        if dialect is not None:
            value = (
                ANNOTATIONS_DIR_URL if self._is_annotations else TESTS_DIR_URL
            )
        elif ctx is not None:
            dialect = ctx.params.get("dialect")
        if dialect is None:
            self.fail("No dialect was given to run the test suite under.")

        def local(
            path: Path,
        ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any]]:
            rewritten = None
            if not self._is_annotations:
                rewritten = _from_old_layout(path.parts)
            if rewritten is None:
                cases = self._cases_from(path=path, dialect=dialect)
                return cases, dialect, {}

            parts, old_dialect = rewritten
            new = Path(*parts)
            if not new.exists():
                self.fail(_OLD_LAYOUT_UNSUPPORTED.format(path=path))
            _warn_old_layout(old=path, new=new, dialect=old_dialect)
            cases = self._cases_from(path=new, dialect=old_dialect)
            return cases, old_dialect, {}

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

        rewritten = None
        if not self._is_annotations:
            rewritten = _from_old_layout(path.split("/"))
        if rewritten is not None:
            parts, dialect = rewritten
            new_path = "/".join(parts)
            _warn_old_layout(
                old=value,
                new=GITHUB / org / repo_name / rest[0] / ref / new_path,
                dialect=dialect,
            )
            path = new_path

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
            if rewritten is not None and not (contents / path).exists():
                self.fail(_OLD_LAYOUT_UNSUPPORTED.format(path=value))
            cases = list(
                self._cases_from(path=contents / path, dialect=dialect),
            )
        return cases, dialect, run_metadata

    def _cases_from(self, path: Any, dialect: Dialect) -> Iterable[TestCase]:
        if path.name.endswith(".json"):
            paths = [path]
        else:
            paths = list(_glob(path, "*.json"))
        if not paths:
            self.fail(f"{path} does not contain JSON Schema Test Suite cases.")

        if self._is_annotations:
            return annotation_cases_from(paths=paths, dialect=dialect)
        return validation_cases_from(paths=paths, dialect=dialect)


_P = Path | zipfile.Path


_OLD_LAYOUT_UNSUPPORTED = (
    "{path} is from a version of the test suite which predates its unified "
    "format, which is no longer supported."
)


def _from_old_layout(
    parts: Sequence[str],
) -> tuple[list[str], Dialect] | None:
    """
    Rewrite a path in the suite's layout from before its unified format.

    There, each dialect's cases lived in a ``tests/<dialect>`` directory of
    their own. Now, cases for every dialect live in ``validation/tests``.
    """
    by_short_name = Dialect.by_short_name()
    for i in reversed(range(len(parts) - 1)):
        if parts[i] == "tests" and parts[i + 1] in by_short_name:
            rewritten = [*parts[:i], "validation", "tests", *parts[i + 2 :]]
            return rewritten, by_short_name[parts[i + 1]]
    return None


def _warn_old_layout(old: object, new: object, dialect: Dialect) -> None:
    _STDERR.print(
        DiagnosticWarning(
            code="deprecated-suite-path",
            message=(
                "Test suite paths from before its unified format are "
                "deprecated."
            ),
            causes=[
                (
                    f"{old} uses the old tests/{dialect.short_name} "
                    "directory, but cases for every dialect now live in "
                    "validation/tests."
                ),
            ],
            hint_stmt=(
                f"Pass {new} with --dialect {dialect.short_name} instead, "
                "which is what is being run."
            ),
        ),
    )


# The version tokens the suite's compatibility grammar allows.
# Some are drafts Bowtie does not support.
# 9999 is a placeholder marking tests needing a draft which does not exist.
_COMPATIBILITY_VERSIONS = {
    str(each): each for each in (1, 2, 3, 4, 6, 7, 2019, 2020, 9999)
}

#: Dialects whose short name is not a compatibility version.
#: A prerelease is tested against features not yet in any release.
_COMPATIBILITY_VERSION_FOR = {"v1": 9999}


#: Dialects whose schemas (including remote ones) the suite gave an explicit
#: ``$schema`` before its unified format. Harnesses which cannot be told the
#: dialect to use may rely on it.
_EXPLICIT_DIALECTS = {"draft2019-09", "draft2020-12"}


def _with_explicit_dialect(schema: Any, dialect: Dialect) -> Any:
    if isinstance(schema, bool):
        return schema
    return {"$schema": str(dialect.uri), **schema}


#: Dialects whose ``format`` asserts by default, rather than annotating.
_FORMAT_ASSERTING = {"v1"}


def _expected_tags(dialect: Dialect) -> frozenset[str]:
    """
    The tagged behaviors Bowtie expects implementations to have by default.

    The suite runs a case only if the implementation provides the behavior
    associated with each of its tags. Cases tagged with any other behavior
    (e.g. a ``format`` behavior that isn't the dialect's default) are skipped.
    """
    if dialect.short_name in _FORMAT_ASSERTING:
        return frozenset({"format-assertion"})
    return frozenset({"format-annotation"})


def _compatibility_version(dialect: Dialect) -> int:
    version = _COMPATIBILITY_VERSION_FOR.get(dialect.short_name)
    if version is not None:
        return version
    return int(dialect.short_name.removeprefix("draft").partition("-")[0])


def _is_compatible(dialect: Dialect, compatibility: str | None) -> bool:
    if compatibility is None:
        return True

    version = _compatibility_version(dialect)

    # Constraints are ordered smallest to largest, as the suite requires,
    # and are checked only until one reaches the version under test.
    # An unknown version token reached that way makes the case incompatible.
    is_valid = True
    for constraint in compatibility.split(","):
        constraint = constraint.strip()
        if constraint.startswith("<="):
            operator, token = "<=", constraint[2:]
        elif constraint.startswith(">="):
            operator, token = ">=", constraint[2:]
        elif constraint.startswith("="):
            operator, token = "=", constraint[1:]
        else:
            operator, token = ">=", constraint

        bound = _COMPATIBILITY_VERSIONS.get(token)
        if bound is None:
            return False

        if operator == "<=":
            is_valid = version <= bound
        elif operator == "=":
            is_valid = version == bound
        else:
            is_valid = version >= bound

        if version <= bound:
            break
    return is_valid


def validation_cases_from(
    paths: Iterable[_P],
    dialect: Dialect,
) -> Iterable[TestCase]:
    expected_tags = _expected_tags(dialect)
    for path in paths:
        data = json.loads(path.read_text())

        if "tests" not in data:
            continue

        for case in data["tests"]:
            compatibility = case.get("compatibility")
            if not _is_compatible(dialect, compatibility):
                continue
            if not expected_tags.issuperset(case.get("tags", [])):
                continue

            tests = [
                {
                    **{
                        key: value
                        for key, value in test.items()
                        if key != "data"
                    },
                    "instance": test["data"],
                }
                for test in case["tests"]
            ]

            schema = case["schema"]
            registry = case.get("externalSchemas", {})
            if dialect.short_name in _EXPLICIT_DIALECTS:
                schema = _with_explicit_dialect(schema, dialect)
                registry = {
                    uri: _with_explicit_dialect(each, dialect)
                    for uri, each in registry.items()
                }

            yield TestCase.from_dict(
                dialect=dialect,
                description=case["description"],
                comment=case.get("comment"),
                schema=schema,
                registry=registry,
                tests=tests,
            )


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
    # Scan for the suite's tests directory from the end.
    # Splitting at the first match breaks refs containing a tests segment.
    for i in reversed(range(1, len(path))):
        if path[i] != "tests":
            continue
        # A validation/tests directory is the unified validation suite.
        # An annotations/tests directory is the annotation suite,
        # unless what follows is a validation suite version directory.
        after = [each for each in path[i + 1 :] if each]
        if path[i - 1] == "validation" or (
            path[i - 1] == "annotations"
            and (not after or after[0].endswith(".json"))
        ):
            i -= 1
        # remove tree/ or blob/ from the front of the ref
        return "/".join(path[i:]).rstrip("/"), "/".join(path[1:i])
    return "", "/".join(path[1:]).rstrip("/")


# Missing zipfile.Path methods...
def _glob(path: _P, path_pattern: str) -> Iterable[_P]:
    return (  # It's missing .match() too, so we fnmatch directly
        each for each in path.iterdir() if fnmatch(each.name, path_pattern)
    )


#: The default git ref of the official suite to collect test cases from.
DEFAULT_REF = "unify"


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

    With no ``ref``, the suite is pinned to the newest commit on its
    `DEFAULT_REF` branch at or before the start of the current hour -- a
    deterministic choice, so that independent runs within the same hour all
    collect against (and can therefore be combined at) the same commit. Pass
    an explicit ref (a branch, tag or commit) to override.

    Returns the suite's root directory (which contains ``validation/tests/``
    directory of unified-format test case files, covering all dialects)
    alongside run metadata recording the exact commit. Every dialect collected
    from this one root is therefore guaranteed to share a single consistent
    commit, even if the suite moves meanwhile.
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

    Unified-format cases cover every dialect, so a suite with any provides
    all of them. One without (e.g. from before the unified format) has none.
    """
    tests_path = root / "validation" / "tests"
    if (
        not tests_path.is_dir()
        or next(_glob(tests_path, "*.json"), None) is None
    ):
        return set()
    return set(Dialect.known())


def predates_unified_format(root: _P) -> bool:
    """
    Is the suite rooted at the given path from before its unified format?
    """
    return (root / "tests").is_dir() and not (root / "validation").is_dir()


def cases_for(root: _P, dialect: Dialect) -> Iterable[TestCase]:
    """
    The test cases for a single dialect within the suite at the given root.
    """
    tests_path = root / "validation" / "tests"
    return validation_cases_from(
        paths=list(_glob(tests_path, "*.json")),
        dialect=dialect,
    )
