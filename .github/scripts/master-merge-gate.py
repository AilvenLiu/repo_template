#!/usr/bin/env python3
"""Validate the source branch tree of a master-bound pull request.

This is a **presence-based** gate, not a diff-based gate. It enumerates every
file in the source branch's tree via the Git Trees API
(GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1) and rejects the PR
if any development-stage path exists in that tree — even if the file was
introduced in an earlier commit and this PR's diff is empty for that path.

The gate script is self-contained (stdlib only) because it lives in
.github/scripts/ and must not depend on .agents/ packages.
"""

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
    source_tree_paths: Iterable[str],
) -> list[str]:
    """Return violations for a master-bound pull request.

    Unlike the old diff-based gate, this checks the **source branch tree**
    for forbidden paths. A path that exists in the source tree (even if it
    was committed before this PR's diff range) is flagged as a violation.
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
            "master accepts only develop, release/<name>, or hotfix/<name> as "
            "pull-request sources"
        )

    for path in sorted(set(source_tree_paths)):
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


def _fetch_source_tree(
    repository: str, head_sha: str, token: str
) -> Sequence[str]:
    """Enumerate every file path in the source branch tree via the Git Trees API.

    Uses GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1 to retrieve
    the full recursive tree for the given commit SHA.

    Returns a list of file paths (not tree entries such as directories).
    Raises RuntimeError if the tree is truncated (>100K entries) or the API
    call fails.
    """
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    encoded_sha = quote(head_sha, safe="")

    request = Request(
        f"{api_url}/repos/{encoded_repository}/git/trees/{encoded_sha}?recursive=1",
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
        raise RuntimeError(f"could not read source tree: {error}") from error

    if not isinstance(response_data, dict):
        raise RuntimeError("Git Trees API returned an unexpected response")

    if response_data.get("truncated", False):
        raise RuntimeError(
            "source branch tree is too large (truncated by API); "
            "refusing to validate on an incomplete tree"
        )

    tree = response_data.get("tree")
    if not isinstance(tree, list):
        raise RuntimeError("Git Trees API response missing 'tree' array")

    paths: list[str] = []
    for entry in tree:
        if not isinstance(entry, dict):
            raise RuntimeError("Git Trees API returned an invalid tree entry")
        entry_path = entry.get("path")
        if not isinstance(entry_path, str) or not entry_path:
            raise RuntimeError("Git Trees API returned an entry without a path")
        entry_type = entry.get("type")
        # Only include blob entries (files), not trees (directories)
        if entry_type == "blob":
            paths.append(entry_path)

    return paths


def validate_event(event: dict[str, Any], token: str) -> list[str]:
    """Validate a GitHub pull-request event payload using the Git Trees API."""
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

    base_repository = _repository_name(base.get("repo"), "pull-request base repository")
    head_repository = _repository_name(head.get("repo"), "pull-request head repository")
    head_ref = _require_string(head, "ref", "pull-request head ref")
    head_sha = _require_string(head, "sha", "pull-request head SHA")

    # Fetch the tree from the head repository — the head SHA lives there.
    # If the PR is cross-repo, validate_master_pull_request still rejects it
    # via the repository ownership check below.
    source_tree_paths = _fetch_source_tree(head_repository, head_sha, token)
    return validate_master_pull_request(
        base_ref=base_ref,
        head_ref=head_ref,
        base_repository=base_repository,
        head_repository=head_repository,
        source_tree_paths=source_tree_paths,
    )


def main() -> int:
    """Run the master merge gate for a GitHub pull-request event."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", type=Path, required=True)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "BLOCKED: GITHUB_TOKEN is required to enumerate the source tree.",
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
