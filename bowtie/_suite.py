"""
Peculiarities related to how the official JSON Schema Test Suite is structured.
"""

from __future__ import annotations

from contextlib import suppress
from fnmatch import fnmatch
from functools import cache
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING, cast
import json
import zipfile

from diagnostic import DiagnosticError
from url import URL, RelativeURLWithoutBase
import click
import rich

from bowtie import GITHUB
from bowtie._core import Dialect, TestCase, github

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any


TEST_SUITE_URL = GITHUB / "json-schema-org/JSON-Schema-Test-Suite"
TESTS_DIR_URL = TEST_SUITE_URL / "tree/main/tests"

URL_FOR_DIALECT = {
    dialect: TESTS_DIR_URL / dialect.short_name for dialect in Dialect.known()
}

ANNOTATIONS_DIR_URL = TEST_SUITE_URL / "tree/main/annotations/tests"

URL_FOR_ANNOTATION_DIALECT = dict.fromkeys(
    Dialect.known(), ANNOTATIONS_DIR_URL
)

# Magic constants assumed/used by the official test suite for $ref tests
SUITE_REMOTE_BASE_URI = URL.parse("http://localhost:1234")


class AnnotationClickParam(click.ParamType):
    """
    A command line parameter which loads annotation tests.
    """

    name = "json-schema-org/JSON-Schema-Test-Suite annotation test cases"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any]]:
        if not isinstance(value, str):
            return value

        # Convert dialect URIs or shortnames to annotation test suite URIs
        input_dialect = Dialect.by_alias().get(value)
        if input_dialect is not None:
            value = URL_FOR_ANNOTATION_DIALECT.get(input_dialect, value)

        try:
            with suppress(TypeError):
                value = URL.parse(value)
        except RelativeURLWithoutBase:
            _dialect_name, dialect, cases = self._resolve_local(
                path=Path(value),
                ctx=ctx,
                known_dialect=input_dialect,
            )
            run_metadata: dict[str, Any] = {}
        else:
            from github3.exceptions import (  # type: ignore[reportMissingTypeStubs]  # noqa: PLC0415
                NotFoundError,
            )

            gh = github()
            org, repo_name, *rest = value.path_segments
            repo = gh.repository(org, repo_name)  # type: ignore[reportUnknownMemberType]

            path, ref = path_and_ref_from_gh_path(rest)
            data = BytesIO()
            data.name = ""
            succeeded = repo.archive(format="zipball", path=data, ref=ref)  # type: ignore[reportUnknownMemberType]
            if not succeeded:
                message = "Fetching the annotation test suite failed."
                error = DiagnosticError(
                    code="annotation-suite-fetch-failed",
                    message=message,
                    causes=[
                        f"Retrieved the tree {ref}",
                        f"Tried to download {path} from within it.",
                    ],
                    hint_stmt=(
                        f"Check that {ref} is an existing branch and that "
                        "you have passed the right path to test cases."
                    ),
                    note_stmt="You can also pass a local path.",
                )
                rich.print(error)
                return self.fail(message)
            data.seek(0)
            with zipfile.ZipFile(data) as zf:
                (contents,) = zipfile.Path(zf).iterdir()
                _dialect_name, dialect, cases = self._resolve_local(
                    path=contents / path,
                    ctx=ctx,
                    known_dialect=input_dialect,
                )
                cases = list(cases)

                try:
                    commit = repo.commit(ref)  # type: ignore[reportOptionalMemberAccess]
                except NotFoundError:
                    commit_info = ref
                else:
                    sha = cast(
                        "str",
                        commit.sha,  # type: ignore[reportUnknownMemberType]
                    )
                    url = cast(
                        "str",
                        commit.html_url,  # type: ignore[reportUnknownMemberType]
                    )
                    commit_info = {
                        "text": sha[:7],
                        "href": url,
                    }
                run_metadata: dict[str, Any] = {"Commit": commit_info}

        return cases, dialect, run_metadata

        self.fail(
            f"{value!r} does not contain annotation test suite cases.",
        )

    def _resolve_local(
        self,
        path: Any,
        ctx: click.Context | None,
        known_dialect: Dialect | None = None,
    ) -> tuple[str, Dialect, Iterable[TestCase]]:
        if path.name.endswith(".json"):
            paths, version_path = [path], path.parent
        else:
            paths, version_path = _glob(path, "*.json"), path

        is_annotations = (
            version_path.name == "annotations"
            or version_path.parent.name == "annotations"
        )

        dialect_name = (
            version_path.parent.name if is_annotations else version_path.name
        )

        dialect = known_dialect
        if dialect is None:
            dialect = Dialect.by_short_name().get(dialect_name)
        if dialect is None and ctx is not None:
            dialect = ctx.params.get("dialect")

        if dialect is None:
            self.fail(
                f"{path} does not contain annotation test cases or "
                "could not infer dialect. Please use --dialect.",
            )

        cases = annotation_cases_from(paths=paths, dialect=dialect)
        return dialect_name, dialect, cases


class ClickParam(click.ParamType):
    """
    A command line parameter which loads tests from the official test suite.
    """

    name = "json-schema-org/JSON-Schema-Test-Suite test cases"

    def convert(
        self,
        value: Any,
        param: click.Parameter | None,
        ctx: click.Context | None,
    ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any], bool]:
        if not isinstance(value, str):
            return value

        # Convert dialect URIs or shortnames to test suite URIs
        value = Dialect.by_alias().get(value, value)
        value = URL_FOR_DIALECT.get(value, value)

        try:
            with suppress(TypeError):
                value = URL.parse(value)
        except RelativeURLWithoutBase:
            cases, dialect, is_annotations = self._cases_and_dialect(
                path=Path(value),
                ctx=ctx,
            )
            run_metadata: dict[str, Any] = {}
        else:
            from github3.exceptions import (  # type: ignore[reportMissingTypeStubs]  # noqa: PLC0415
                NotFoundError,
            )

            gh = github()
            org, repo_name, *rest = value.path_segments
            repo = gh.repository(org, repo_name)  # type: ignore[reportUnknownMemberType]

            path, ref = path_and_ref_from_gh_path(rest)
            data = BytesIO()
            data.name = ""
            succeeded = repo.archive(format="zipball", path=data, ref=ref)  # type: ignore[reportUnknownMemberType]
            if not succeeded:
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
            data.seek(0)
            with zipfile.ZipFile(data) as zf:
                (contents,) = zipfile.Path(zf).iterdir()
                cases, dialect, is_annotations = self._cases_and_dialect(
                    path=contents / path,
                    ctx=ctx,
                )
                cases = list(cases)

                try:
                    commit = repo.commit(ref)  # type: ignore[reportOptionalMemberAccess]
                except NotFoundError:
                    commit_info = ref
                else:
                    # TODO: Make this the tree URL maybe, but I see tree(...)
                    #       doesn't come with an html_url
                    sha = cast(
                        "str",
                        commit.sha,  # type: ignore[reportUnknownMemberType]
                    )
                    url = cast(
                        "str",
                        commit.html_url,  # type: ignore[reportUnknownMemberType]
                    )
                    commit_info = {
                        "text": sha[:7],
                        "href": url,
                    }
                run_metadata: dict[str, Any] = {"Commit": commit_info}

        return cases, dialect, run_metadata, is_annotations

        self.fail(f"{value!r} does not contain JSON Schema Test Suite cases.")

    def _cases_and_dialect(self, path: Any, ctx: click.Context | None):
        if path.name.endswith(".json"):
            paths, version_path = [path], path.parent
        else:
            paths, version_path = _glob(path, "*.json"), path

        is_annotations = (
            version_path.name == "annotations"
            or version_path.parent.name == "annotations"
        )

        remotes = version_path.parent.parent / "remotes"

        dialect_name = (
            version_path.parent.name if is_annotations else version_path.name
        )
        dialect = Dialect.by_short_name().get(dialect_name)
        if dialect is None and ctx is not None:
            dialect = ctx.params.get("dialect")

        if dialect is None:
            self.fail(
                f"{path} does not contain JSON Schema Test Suite cases or "
                "could not infer dialect. Please use --dialect.",
            )

        if is_annotations:
            cases = annotation_cases_from(paths=paths, dialect=dialect)
        else:
            cases = cases_from(paths=paths, remotes=remotes, dialect=dialect)

        return cases, dialect, is_annotations


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


def _is_compatible(dialect: Dialect, compatibility: str | None) -> bool:
    if compatibility is None:
        return True

    for constraint in compatibility.split(","):
        constraint = constraint.strip()
        if constraint.startswith("<="):
            b = Dialect.by_alias().get(constraint[2:])
            if b is not None and dialect > b:
                return False
        elif constraint.startswith("="):
            b = Dialect.by_alias().get(constraint[1:])
            if b is not None and dialect != b:
                return False
        else:
            b = Dialect.by_alias().get(constraint)
            if b is not None and dialect < b:
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

            tests = [
                {
                    "description": test.get("description", ""),
                    "instance": test.get("instance", test.get("data", {})),
                    "assertions": test.get("assertions", []),
                }
                for test in case["tests"]
            ]

            if not tests:
                continue

            yield TestCase.from_dict(
                dialect=dialect,
                description=case["description"],
                schema=case["schema"],
                tests=tests,
            )


def path_and_ref_from_gh_path(path: list[str]):
    ROOTS = {"tests", "annotations"}
    for i in range(1, len(path)):
        if path[i] in ROOTS:
            ref = "/".join(path[1:i])
            subpath = "/".join(path[i:]).rstrip("/")
            return subpath, ref
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
