#!/usr/bin/env python3
"""Validate the source branch and changed paths of a master-bound pull request."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Iterable, Sequence
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


MASTER_BRANCH = "master"
ALLOWED_HEAD_PREFIXES = ("release/", "hotfix/")
DEVELOPMENT_ONLY_ROOTS = (
    ".ai",
    ".agents",
    ".claude",
    ".codex",
    "agent_roadmaps",
)
DEVELOPMENT_ONLY_FILES = ("AGENTS.md", "CLAUDE.md", "CODEX.md")


def is_allowed_master_source(branch: str) -> bool:
    """Return whether a branch is an allowed same-repository master PR source."""
    if branch == "develop":
        return True
    return any(
        branch.startswith(prefix) and len(branch) > len(prefix)
        for prefix in ALLOWED_HEAD_PREFIXES
    )


def is_development_only_path(path: str) -> bool:
    """Return whether a path is prohibited in a PR whose base is master."""
    if path in DEVELOPMENT_ONLY_FILES:
        return True

    if any(
        path == root or path.startswith(f"{root}/") for root in DEVELOPMENT_ONLY_ROOTS
    ):
        return True

    if path == "docs" or path.startswith("docs/"):
        return not (path == "docs/changelog" or path.startswith("docs/changelog/"))

    return False


def validate_master_pull_request(
    *,
    base_ref: str,
    head_ref: str,
    base_repository: str,
    head_repository: str,
    changed_paths: Iterable[str],
) -> list[str]:
    """Return violations for a master-bound pull request.

    The caller should include both current and previous names for renamed files.
    A non-master target is outside this gate's scope and therefore has no findings.
    """
    if base_ref != MASTER_BRANCH:
        return []

    violations: list[str] = []
    if not base_repository or base_repository != head_repository:
        violations.append(
            "master accepts pull requests only from branches in the same repository"
        )

    if not is_allowed_master_source(head_ref):
        violations.append(
            "master accepts only develop, release/<name>, or hotfix/<name> as pull-request sources"
        )

    for path in sorted(set(changed_paths)):
        if is_development_only_path(path):
            violations.append(
                f"development-stage path is forbidden in a master PR: {path}"
            )

    return violations


def _require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"event payload is missing {label}")
    return value


def _repository_name(value: Any, label: str) -> str:
    if not isinstance(value, dict):
        raise ValueError(f"event payload is missing {label}")
    return _require_string(value, "full_name", label)


def _fetch_changed_paths(
    repository: str, pull_number: int, token: str
) -> Sequence[str]:
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    paths: list[str] = []

    for page in range(1, 101):
        request = Request(
            f"{api_url}/repos/{encoded_repository}/pulls/{pull_number}/files?per_page=100&page={page}",
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with urlopen(request, timeout=30) as response:  # noqa: S310
                response_data = json.load(response)
        except (HTTPError, URLError, OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"could not read pull-request files: {error}") from error

        if not isinstance(response_data, list):
            raise RuntimeError("pull-request files API returned an unexpected response")

        for item in response_data:
            if not isinstance(item, dict):
                raise RuntimeError(
                    "pull-request files API returned an invalid file entry"
                )
            paths.append(_require_string(item, "filename", "changed filename"))
            previous_name = item.get("previous_filename")
            if previous_name is not None:
                if not isinstance(previous_name, str) or not previous_name:
                    raise RuntimeError(
                        "pull-request files API returned an invalid previous filename"
                    )
                paths.append(previous_name)

        if len(response_data) < 100:
            return paths

    raise RuntimeError(
        "pull request has more than 10,000 changed files; refusing to truncate validation"
    )


def validate_event(event: dict[str, Any], token: str) -> list[str]:
    """Validate a GitHub pull-request event payload using the REST files API."""
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        raise ValueError("event payload is not a pull-request event")

    base = pull_request.get("base")
    head = pull_request.get("head")
    if not isinstance(base, dict) or not isinstance(head, dict):
        raise ValueError("event payload is missing pull-request base or head")

    base_ref = _require_string(base, "ref", "pull-request base ref")
    if base_ref != MASTER_BRANCH:
        return []

    head_ref = _require_string(head, "ref", "pull-request head ref")
    base_repository = _repository_name(base.get("repo"), "pull-request base repository")
    head_repository = _repository_name(head.get("repo"), "pull-request head repository")

    pull_number = event.get("number")
    if not isinstance(pull_number, int) or pull_number <= 0:
        raise ValueError("event payload is missing a valid pull-request number")

    changed_paths = _fetch_changed_paths(base_repository, pull_number, token)
    return validate_master_pull_request(
        base_ref=base_ref,
        head_ref=head_ref,
        base_repository=base_repository,
        head_repository=head_repository,
        changed_paths=changed_paths,
    )


def main() -> int:
    """Run the master merge gate for a GitHub pull-request event."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", type=Path, required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "BLOCKED: GITHUB_TOKEN is required to enumerate pull-request files.",
            file=sys.stderr,
        )
        return 1

    try:
        raw_event = json.loads(args.event_path.read_text(encoding="utf-8"))
        if not isinstance(raw_event, dict):
            raise ValueError("event payload is not a JSON object")
        violations = validate_event(raw_event, token)
    except (OSError, ValueError, RuntimeError) as error:
        print(
            f"BLOCKED: master merge gate could not validate this pull request: {error}",
            file=sys.stderr,
        )
        return 1

    if violations:
        print("BLOCKED: master merge policy violations:", file=sys.stderr)
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print("Master merge policy passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
