"""
Peculiarities related to how the official JSON Schema Test Suite is structured.
"""

from __future__ import annotations

from contextlib import suppress
from fnmatch import fnmatch
from functools import cache
from io import BytesIO
from pathlib import Path
from typing import TYPE_CHECKING
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

# Magic constants assumed/used by the official test suite for $ref tests
SUITE_REMOTE_BASE_URI = URL.parse("http://localhost:1234")


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
    ) -> tuple[Iterable[TestCase], Dialect, dict[str, Any]]:
        if not isinstance(value, str):
            return value

        # Convert dialect URIs or shortnames to test suite URIs
        value = Dialect.by_alias().get(value, value)
        value = URL_FOR_DIALECT.get(value, value)

        try:
            with suppress(TypeError):
                value = URL.parse(value)
        except RelativeURLWithoutBase:
            cases, dialect = self._cases_and_dialect(path=Path(value))
            run_metadata = {}
        else:
            from github3.exceptions import (  # type: ignore[reportMissingTypeStubs]
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
                cases, dialect = self._cases_and_dialect(path=contents / path)
                cases = list(cases)

            try:
                commit = repo.commit(ref)  # type: ignore[reportOptionalMemberAccess]
            except NotFoundError:
                commit_info = ref
            else:
                # TODO: Make this the tree URL maybe, but I see tree(...)
                #       doesn't come with an html_url
                commit_info = {"text": commit.sha[:7], "href": commit.html_url}  # type: ignore[reportOptionalMemberAccess]
            run_metadata: dict[str, Any] = {"Commit": commit_info}

        return cases, dialect, run_metadata

        self.fail(f"{value!r} does not contain JSON Schema Test Suite cases.")

    def _cases_and_dialect(self, path: Any):
        if path.name.endswith(".json"):
            paths, version_path = [path], path.parent
        else:
            paths, version_path = _glob(path, "*.json"), path

        remotes = version_path.parent.parent / "remotes"

        dialect = Dialect.by_short_name().get(version_path.name)
        if dialect is None:
            self.fail(f"{path} does not contain JSON Schema Test Suite cases.")

        cases = cases_from(paths=paths, remotes=remotes, dialect=dialect)

        return cases, dialect


_P = Path | zipfile.Path


def _remotes_in(path: Path, dialect: Dialect) -> Iterable[tuple[URL, Any]]:
    # This messy logic is because the test suite is terrible at indicating
    # what remotes are needed for what drafts, and mixes in schemas which
    # have no $schema and which are invalid under earlier versions, in with
    # other schemas which are needed for tests.
    #
    # FIXME: #40: for draft-next support

    for each in _rglob(path, "*.json"):
        schema = json.loads(each.read_text())

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
        if _stem(path) in {"refRemote", "dynamicRef", "vocabulary"}:
            registry = remotes_in(remotes, dialect=dialect)
        else:
            registry = {}

        for case in json.loads(path.read_text()):
            for test in case["tests"]:
                test["instance"] = test.pop("data")
            case.pop("specification", None)  # we do nothing with this now
            yield TestCase.from_dict(
                dialect=dialect,
                registry=registry,
                **case,
            )


def path_and_ref_from_gh_path(path: list[str]):
    subpath: list[str] = []
    while path[-1] != "tests":
        subpath.append(path.pop())
    subpath.append(path.pop())
    # remove tree/ or blob/
    return "/".join(reversed(subpath)).rstrip("/"), "/".join(path[1:])


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


def _stem(path: _P) -> str:  # Missing on < 3.11
    if hasattr(path, "stem"):
        return path.stem
    return Path(path.at).stem  # type: ignore[reportUnknownArgumentType, reportUnknownMemberType]
