#!/usr/bin/env python3
"""Validate the source branch tree of a master-bound pull request.

This is a **presence-based** gate, not a diff-based gate. It enumerates every
file in the source branch's tree via the Git Trees API
(GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1) and rejects the PR
if any development-stage path exists in that tree - even if the file was
introduced in an earlier commit and this PR's diff is empty for that path.

For release branches, the gate also reads the immutable develop source SHA
from the PR body and rejects any tree difference other than a forbidden-path
deletion. Emergency hotfix PRs must record their reduced validation trade-off.
When the REQUIRED_SOURCE_CHECKS environment variable names Actions workflows,
the gate additionally requires each of them to have a successful push run on
develop at the recorded develop source SHA (validation provenance,
master-merge-policy.md section 9.1).

For pull requests targeting a protected release/v<x.y.z> branch, the gate
enforces the staging contract instead: the source must be the matching
chore/release-v<x.y.z> branch and the tree may differ from the release base
only by forbidden-path deletions (master-merge-policy.md section 9.2).

The script also offers --rehearse: a read-only, network-free local pre-flight
that derives the release names from the authoritative manifest, runs the same
pure validation, and simulates the deletion-only projection before any release
ref is cut (master-merge-policy.md section 9.4).

The gate script is self-contained (stdlib only) because it lives in
.github/scripts/ and must not depend on .agents/ packages.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, TypeAlias
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


MASTER_BRANCH = "master"
ALLOWED_HEAD_PREFIXES = ("release/", "hotfix/")
DEVELOP_SOURCE_LABEL = "Develop-Source-SHA"
HOTFIX_TRADEOFF_LABEL = "Hotfix-Validation-Tradeoff"
FULL_SHA_PATTERN = re.compile(r"[0-9a-fA-F]{40}")
SEMVER_COMPONENT = r"(?:0|[1-9][0-9]*)"
RELEASE_BRANCH_PATTERN = re.compile(
    rf"^(?:release|hotfix)/v({SEMVER_COMPONENT})\.({SEMVER_COMPONENT})\.({SEMVER_COMPONENT})$"
)
RELEASE_TAG_PATTERN = re.compile(
    rf"^release-v({SEMVER_COMPONENT})\.({SEMVER_COMPONENT})\.({SEMVER_COMPONENT})$"
)
DEVELOPMENT_ONLY_ROOTS = (
    ".ai",
    ".agents",
    ".claude",
    ".codex",
    "agent_roadmaps",
)
DEVELOPMENT_ONLY_FILES = ("AGENTS.md", "CLAUDE.md", "CODEX.md")
TreeEntry: TypeAlias = tuple[str, str, str]
TreeSnapshot: TypeAlias = dict[str, TreeEntry]


def branch_version(branch: str) -> tuple[int, int, int] | None:
    """Return the semantic version a master source branch name declares."""
    match = RELEASE_BRANCH_PATTERN.fullmatch(branch)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def tag_version(tag: str) -> tuple[int, int, int] | None:
    """Return the semantic version a release tag name declares.

    Exported as the canonical parser for the post-merge tagging step. This gate
    runs at pull-request time and therefore cannot itself enforce that the tag
    was applied; release automation and the operator procedure own that step.
    """
    match = RELEASE_TAG_PATTERN.fullmatch(tag)
    if match is None:
        return None
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def format_version(version: tuple[int, int, int]) -> str:
    """Return the canonical dotted text for one semantic version."""
    return ".".join(str(component) for component in version)


def is_allowed_master_source(branch: str) -> bool:
    """Return whether a branch is an allowed same-repository master PR source."""
    return branch_version(branch) is not None


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
            "master accepts only release/v<major>.<minor>.<patch> or "
            "hotfix/v<major>.<minor>.<patch> as pull-request sources"
        )

    for path in sorted(set(source_tree_paths)):
        if is_development_only_path(path):
            violations.append(
                f"development-stage path is forbidden in a master PR: {path}"
            )

    return violations


def validate_release_projection(
    *,
    develop_tree: Mapping[str, TreeEntry],
    release_tree: Mapping[str, TreeEntry],
) -> list[str]:
    """Return violations when a release tree is not a deletion-only projection."""
    violations: list[str] = []

    for path in sorted(release_tree.keys() - develop_tree.keys()):
        violations.append(f"release tree addition is forbidden: {path}")

    for path in sorted(release_tree.keys() & develop_tree.keys()):
        develop_mode, develop_type, develop_sha = develop_tree[path]
        release_mode, release_type, release_sha = release_tree[path]
        if develop_mode != release_mode:
            violations.append(f"release tree mode change is forbidden: {path}")
        elif develop_type != release_type or develop_sha != release_sha:
            violations.append(f"release tree modification is forbidden: {path}")

    for path in sorted(develop_tree.keys() - release_tree.keys()):
        if not is_development_only_path(path):
            violations.append(f"release tree non-policy deletion is forbidden: {path}")

    return violations


CMAKE_MANIFEST = "CMakeLists.txt"
PYPROJECT_MANIFEST = "pyproject.toml"
STRICT_SEMVER_PATTERN = re.compile(
    rf"^{SEMVER_COMPONENT}\.{SEMVER_COMPONENT}\.{SEMVER_COMPONENT}$"
)


def _literal_version_scan(text: str) -> str | None:
    """Return the first quoted version assignment in manifest text."""
    match = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"', text)
    return match.group(1) if match else None


def _table_version(table: object) -> str | None:
    """Return a string version from one decoded TOML table."""
    if not isinstance(table, dict):
        return None
    version = table.get("version")
    return version if isinstance(version, str) else None


def parse_pyproject_version(text: str) -> str | None:
    """Return the version declared by pyproject.toml text.

    tomllib is stdlib from 3.11 only, so the literal scan is a real fallback
    rather than dead code: an older interpreter or a malformed manifest must
    still yield a version to compare instead of silently skipping the check.
    """
    try:
        import tomllib  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        return _literal_version_scan(text)

    try:
        decoded: object = tomllib.loads(text)
    except ValueError:
        return _literal_version_scan(text)

    if not isinstance(decoded, dict):
        return None
    project_version = _table_version(decoded.get("project"))
    if project_version is not None:
        return project_version
    tool = decoded.get("tool")
    if isinstance(tool, dict):
        return _table_version(tool.get("poetry"))
    return None


def parse_cmake_version(text: str) -> str | None:
    """Return the VERSION of the first CMake project() command."""
    without_comments = re.sub(r"(?m)#.*$", "", text)
    match = re.search(r"(?is)\bproject\s*\((.*?)\)", without_comments)
    if match is None:
        return None
    version_match = re.search(r"(?i)\bVERSION\s+([0-9][0-9A-Za-z.+-]*)", match.group(1))
    return version_match.group(1) if version_match else None


def _authoritative_version(
    manifests: Mapping[str, str],
) -> tuple[str | None, str | None]:
    """Return the authoritative version and its manifest path for one tree.

    CMake wins whenever it is present, covering both the cpp and hybrid
    profiles, because CMake owns the native build graph under C++ First.
    """
    if CMAKE_MANIFEST in manifests:
        return parse_cmake_version(manifests[CMAKE_MANIFEST]), CMAKE_MANIFEST
    if PYPROJECT_MANIFEST in manifests:
        return parse_pyproject_version(
            manifests[PYPROJECT_MANIFEST]
        ), PYPROJECT_MANIFEST
    return None, None


def validate_release_version(
    *,
    head_ref: str,
    source_manifests: Mapping[str, str],
    master_manifests: Mapping[str, str],
) -> list[str]:
    """Return violations for the release version identity of a master PR."""
    declared = branch_version(head_ref)
    if declared is None:
        return []

    violations: list[str] = []
    source_version, manifest_path = _authoritative_version(source_manifests)
    if manifest_path is None:
        violations.append(
            "source tree declares no authoritative version manifest "
            f"({CMAKE_MANIFEST} or {PYPROJECT_MANIFEST})"
        )
        return violations
    if source_version is None:
        violations.append(f"no version is declared in {manifest_path}")
        return violations
    if STRICT_SEMVER_PATTERN.fullmatch(source_version) is None:
        violations.append(
            f"{manifest_path} version must be <major>.<minor>.<patch> without a "
            f"pre-release or build suffix: {source_version}"
        )
        return violations

    if manifest_path == CMAKE_MANIFEST and PYPROJECT_MANIFEST in source_manifests:
        mirrored = parse_pyproject_version(source_manifests[PYPROJECT_MANIFEST])
        if mirrored != source_version:
            violations.append(
                f"{PYPROJECT_MANIFEST} version {mirrored} must equal the "
                f"authoritative {CMAKE_MANIFEST} version {source_version}"
            )

    if format_version(declared) != source_version:
        violations.append(
            f"branch name declares version {format_version(declared)} but "
            f"{manifest_path} at the recorded source SHA declares {source_version}"
        )
        return violations

    master_version, _ = _authoritative_version(master_manifests)
    if master_version is not None and STRICT_SEMVER_PATTERN.fullmatch(master_version):
        current = tuple(int(part) for part in master_version.split("."))
        if declared <= current:
            violations.append(
                f"candidate version {source_version} must be strictly greater "
                f"than the version currently on master ({master_version})"
            )

    return violations


SOURCE_BRANCH = "develop"


def validate_staging_pull_request(
    *,
    base_ref: str,
    head_ref: str,
    base_repository: str,
    head_repository: str,
) -> list[str]:
    """Return violations for a pull request targeting a protected release branch.

    A release branch accepts only its own deletion-only staging branch,
    chore/release-v<x.y.z> for the identical version, from the same repository
    (master-merge-policy.md sections 4 and 9.2). The tree comparison itself is
    performed by validate_release_projection against the release branch base.
    """
    version = branch_version(base_ref)
    if version is None or not base_ref.startswith("release/"):
        return []

    violations: list[str] = []
    if not base_repository or base_repository != head_repository:
        violations.append(
            "a release branch accepts pull requests only from branches in the "
            "same repository"
        )
    expected = f"chore/release-v{format_version(version)}"
    if head_ref != expected:
        violations.append(
            "a release branch accepts only its deletion-only staging branch "
            f"{expected} as a pull-request source"
        )
    return violations


def validate_source_validation_provenance(
    *,
    workflow_runs_payload: Any,
    required_workflows: Sequence[str],
    expected_head_sha: str,
) -> list[str]:
    """Return violations when required workflows did not succeed at the SHA.

    Validation provenance (master-merge-policy.md section 9.1): because the
    release tree is identity-proved against the recorded develop source SHA,
    a successful authoritative validation at that SHA is evidence for the
    release PR. Evidence is read from the Actions workflow-runs listing, not
    the Checks API, because a workflow run's name, event, head branch, and
    head SHA are recorded by the forge and cannot be minted through the
    check-runs API by a same-repository branch workflow. A run counts only
    when it is a completed, successful `push` run of the develop branch at
    exactly the expected SHA. The function fails closed on a malformed or
    incomplete listing.
    """
    if not required_workflows:
        return []
    malformed = "workflow-run listing for the recorded source SHA is malformed"
    if not isinstance(workflow_runs_payload, dict):
        return [malformed]
    runs = workflow_runs_payload.get("workflow_runs")
    if not isinstance(runs, list):
        return [malformed]
    total_count = workflow_runs_payload.get("total_count")
    if isinstance(total_count, int) and total_count > len(runs):
        return [
            "workflow-run listing for the recorded source SHA is incomplete; "
            "refusing to validate provenance on a partial listing"
        ]

    successful: set[str] = set()
    for run in runs:
        if not isinstance(run, dict):
            continue
        name = run.get("name")
        if (
            isinstance(name, str)
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and run.get("event") == "push"
            and run.get("head_branch") == SOURCE_BRANCH
            and run.get("head_sha") == expected_head_sha
        ):
            successful.add(name)

    return [
        "required validation workflow has no successful push run on "
        f"{SOURCE_BRANCH} at the recorded develop source SHA: {name}"
        for name in required_workflows
        if name not in successful
    ]


def _required_source_checks() -> list[str]:
    """Return the workflow names REQUIRED_SOURCE_CHECKS demands at the SHA.

    Values are GitHub Actions workflow names, comma-separated; a workflow
    whose name contains a comma cannot be expressed and must be renamed.
    """
    raw = os.environ.get("REQUIRED_SOURCE_CHECKS", "")
    return [name.strip() for name in raw.split(",") if name.strip()]


def _body_field(body: Any, label: str) -> str | None:
    """Return one unambiguous, non-empty PR body field value."""
    if not isinstance(body, str):
        return None

    prefix = f"{label}:"
    values = [
        line[len(prefix) :].strip()
        for line in body.splitlines()
        if line.startswith(prefix)
    ]
    if len(values) != 1 or not values[0]:
        return None
    return values[0]


def _develop_source_sha(body: Any) -> str | None:
    """Return the full develop source SHA recorded in a release PR body."""
    value = _body_field(body, DEVELOP_SOURCE_LABEL)
    if value is None or FULL_SHA_PATTERN.fullmatch(value) is None:
        return None
    return value.lower()


def _require_string(mapping: dict[str, Any], key: str, label: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"event payload is missing {label}")
    return value


def _repository_name(value: Any, label: str) -> str:
    if not isinstance(value, dict):
        raise ValueError(f"event payload is missing {label}")
    return _require_string(value, "full_name", label)


def _request_json(url: str, token: str, failure_label: str) -> dict[str, Any]:
    """Return one GitHub REST response as a JSON object."""
    request = Request(
        url,
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
        raise RuntimeError(f"could not {failure_label}: {error}") from error

    if not isinstance(response_data, dict):
        raise RuntimeError(
            f"could not {failure_label}: API returned an unexpected response"
        )
    return response_data


def _fetch_tree(repository: str, commit_sha: str, token: str) -> TreeSnapshot:
    """Enumerate every leaf entry in a commit tree via the Git Trees API.

    Uses GET /repos/{owner}/{repo}/git/trees/{sha}?recursive=1 to retrieve
    the full recursive tree for the given commit SHA.

    Returns path-to-identity mappings for blobs and submodule commits. The
    identity contains mode, type, and object SHA so additions, content changes,
    type changes, and executable-bit changes are all detectable.
    Raises RuntimeError if the tree is truncated (>100K entries) or the API
    call fails.
    """
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    encoded_sha = quote(commit_sha, safe="")
    response_data = _request_json(
        f"{api_url}/repos/{encoded_repository}/git/trees/{encoded_sha}?recursive=1",
        token,
        "read commit tree",
    )

    if response_data.get("truncated", False):
        raise RuntimeError(
            "source branch tree is too large (truncated by API); "
            "refusing to validate on an incomplete tree"
        )

    tree = response_data.get("tree")
    if not isinstance(tree, list):
        raise RuntimeError("Git Trees API response missing 'tree' array")

    entries: TreeSnapshot = {}
    for entry in tree:
        if not isinstance(entry, dict):
            raise RuntimeError("Git Trees API returned an invalid tree entry")
        entry_path = entry.get("path")
        if not isinstance(entry_path, str) or not entry_path:
            raise RuntimeError("Git Trees API returned an entry without a path")
        entry_type = entry.get("type")
        if entry_type == "tree":
            continue
        if entry_type not in {"blob", "commit"}:
            raise RuntimeError("Git Trees API returned an unsupported tree entry type")
        entry_mode = entry.get("mode")
        entry_sha = entry.get("sha")
        if (
            not isinstance(entry_mode, str)
            or not isinstance(entry_type, str)
            or not isinstance(entry_sha, str)
        ):
            raise RuntimeError("Git Trees API returned an incomplete tree entry")
        entries[entry_path] = (entry_mode, entry_type, entry_sha)

    return entries


def _is_ancestor(
    repository: str,
    ancestor: str,
    descendant: str,
    token: str,
) -> bool:
    """Return whether one commit is an ancestor of another GitHub revision."""
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    encoded_ancestor = quote(ancestor, safe="")
    encoded_descendant = quote(descendant, safe="")
    response_data = _request_json(
        f"{api_url}/repos/{encoded_repository}/compare/"
        f"{encoded_ancestor}...{encoded_descendant}",
        token,
        "compare commit ancestry",
    )
    behind_by = response_data.get("behind_by")
    if not isinstance(behind_by, int):
        raise RuntimeError("compare API response missing integer 'behind_by'")
    return behind_by == 0


def _fetch_manifest_texts(
    repository: str, tree: TreeSnapshot, token: str
) -> dict[str, str]:
    """Read the version manifests that exist in one tree snapshot."""
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    manifests: dict[str, str] = {}
    for path in (CMAKE_MANIFEST, PYPROJECT_MANIFEST):
        entry = tree.get(path)
        if entry is None or entry[1] != "blob":
            continue
        blob = _request_json(
            f"{api_url}/repos/{encoded_repository}/git/blobs/{quote(entry[2], safe='')}",
            token,
            f"read {path}",
        )
        content = blob.get("content")
        if not isinstance(content, str) or blob.get("encoding") != "base64":
            continue
        try:
            manifests[path] = base64.b64decode(content).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
    return manifests


def _fetch_workflow_runs(
    repository: str, commit_sha: str, token: str
) -> dict[str, Any]:
    """Read the workflow runs for one commit via the read-only Actions API."""
    api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    encoded_repository = quote(repository, safe="/")
    encoded_sha = quote(commit_sha, safe="")
    return _request_json(
        f"{api_url}/repos/{encoded_repository}/actions/runs"
        f"?head_sha={encoded_sha}&per_page=100",
        token,
        "read source SHA workflow runs",
    )


def _master_manifests(
    base: dict[str, Any], base_repository: str, head_ref: str, token: str
) -> dict[str, str]:
    """Read the version manifests currently on master for the monotonicity check."""
    if branch_version(head_ref) is None:
        return {}
    base_sha = base.get("sha")
    if not isinstance(base_sha, str) or not base_sha:
        return {}
    return _fetch_manifest_texts(
        base_repository, _fetch_tree(base_repository, base_sha, token), token
    )


def _validate_staging_event(
    base: dict[str, Any], head: dict[str, Any], token: str
) -> list[str]:
    """Validate a pull request targeting a protected release branch.

    The deletion-only projection check for the staging PR: the head tree may
    differ from the release branch base tree only by deletions of forbidden
    paths (master-merge-policy.md section 9.2).
    """
    base_ref = _require_string(base, "ref", "pull-request base ref")
    base_repository = _repository_name(base.get("repo"), "pull-request base repository")
    head_repository = _repository_name(head.get("repo"), "pull-request head repository")
    head_ref = _require_string(head, "ref", "pull-request head ref")
    head_sha = _require_string(head, "sha", "pull-request head SHA")

    violations = validate_staging_pull_request(
        base_ref=base_ref,
        head_ref=head_ref,
        base_repository=base_repository,
        head_repository=head_repository,
    )
    if base_repository == head_repository:
        base_sha = _require_string(base, "sha", "pull-request base SHA")
        violations.extend(
            validate_release_projection(
                develop_tree=_fetch_tree(base_repository, base_sha, token),
                release_tree=_fetch_tree(head_repository, head_sha, token),
            )
        )
    return violations


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
        if base_ref.startswith("release/") and branch_version(base_ref) is not None:
            return _validate_staging_event(base, head, token)
        return []

    base_repository = _repository_name(base.get("repo"), "pull-request base repository")
    head_repository = _repository_name(head.get("repo"), "pull-request head repository")
    head_ref = _require_string(head, "ref", "pull-request head ref")
    head_sha = _require_string(head, "sha", "pull-request head SHA")

    # Fetch the tree from the head repository — the head SHA lives there.
    # If the PR is cross-repo, validate_master_pull_request still rejects it
    # via the repository ownership check below.
    source_tree = _fetch_tree(head_repository, head_sha, token)
    violations = validate_master_pull_request(
        base_ref=base_ref,
        head_ref=head_ref,
        base_repository=base_repository,
        head_repository=head_repository,
        source_tree_paths=source_tree,
    )

    body = pull_request.get("body")
    if head_ref.startswith("release/") and base_repository == head_repository:
        develop_source_sha = _develop_source_sha(body)
        if develop_source_sha is None:
            violations.append(
                f"release PR body must contain exactly one "
                f"'{DEVELOP_SOURCE_LABEL}: <full 40-character SHA>' field"
            )
        else:
            if not _is_ancestor(base_repository, develop_source_sha, "develop", token):
                violations.append(
                    "recorded develop source SHA is not reachable from develop"
                )
            if not _is_ancestor(base_repository, develop_source_sha, head_sha, token):
                violations.append(
                    "release branch does not descend from the recorded develop source SHA"
                )
            develop_tree = _fetch_tree(base_repository, develop_source_sha, token)
            violations.extend(
                validate_release_projection(
                    develop_tree=develop_tree,
                    release_tree=source_tree,
                )
            )
            required_workflows = _required_source_checks()
            if required_workflows:
                violations.extend(
                    validate_source_validation_provenance(
                        workflow_runs_payload=_fetch_workflow_runs(
                            base_repository, develop_source_sha, token
                        ),
                        required_workflows=required_workflows,
                        expected_head_sha=develop_source_sha,
                    )
                )
            violations.extend(
                validate_release_version(
                    head_ref=head_ref,
                    source_manifests=_fetch_manifest_texts(
                        base_repository, develop_tree, token
                    ),
                    master_manifests=_master_manifests(
                        base, base_repository, head_ref, token
                    ),
                )
            )

    if head_ref.startswith("hotfix/"):
        if _body_field(body, HOTFIX_TRADEOFF_LABEL) is None:
            violations.append(
                f"hotfix PR body must contain exactly one non-empty "
                f"'{HOTFIX_TRADEOFF_LABEL}: <checks run and omissions>' field"
            )
        if base_repository == head_repository:
            violations.extend(
                validate_release_version(
                    head_ref=head_ref,
                    source_manifests=_fetch_manifest_texts(
                        head_repository, source_tree, token
                    ),
                    master_manifests=_master_manifests(
                        base, base_repository, head_ref, token
                    ),
                )
            )

    return violations


def _git_output(repo: Path, *args: str) -> str:
    """Return one local git command's stdout, raising RuntimeError on failure."""
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            encoding="utf-8",
            errors="strict",
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as error:
        raise RuntimeError(f"git {' '.join(args)} failed: {error}") from error
    if process.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {process.stderr.strip()}")
    return process.stdout


def _resolve_ref(repo: Path, ref: str) -> str | None:
    """Resolve a ref to a commit SHA, falling back to its origin remote ref."""
    for candidate in (ref, f"origin/{ref}"):
        try:
            return _git_output(
                repo, "rev-parse", "--verify", f"{candidate}^{{commit}}"
            ).strip()
        except RuntimeError:
            continue
    return None


def _local_tree_paths(repo: Path, commit: str) -> list[str]:
    """Enumerate every file path in one local commit tree."""
    output = _git_output(repo, "ls-tree", "-r", "--name-only", "-z", commit)
    return [path for path in output.split("\0") if path]


def _local_manifests(repo: Path, commit: str) -> dict[str, str]:
    """Read the version manifests that exist in one local commit tree."""
    manifests: dict[str, str] = {}
    for path in (CMAKE_MANIFEST, PYPROJECT_MANIFEST):
        try:
            manifests[path] = _git_output(repo, "show", f"{commit}:{path}")
        except RuntimeError:
            continue
    return manifests


def rehearse(
    repo: Path,
    source_ref: str,
    master_ref: str,
    *,
    allow_missing_master_ref: bool = False,
) -> int:
    """Rehearse a promotion locally: read-only, network-free pre-flight.

    Derives the version and every release name from the authoritative manifest
    at the candidate source SHA, runs the same pure validation the hosted gate
    runs (strict format, hybrid manifest agreement, monotonicity against the
    master ref), and simulates the deletion-only projection, reporting what it
    will remove. An unresolvable master ref is a hard failure, because a pass
    without the monotonicity comparison would be false assurance; pass
    --allow-missing-master-ref only for a first-release bootstrap where no
    master exists yet. Exit code 0 means the promotion names and version are
    safe to cut; any finding should be fixed on develop first.
    """
    source_sha = _resolve_ref(repo, source_ref)
    if source_sha is None:
        raise RuntimeError(
            f"source ref '{source_ref}' (and 'origin/{source_ref}') does not resolve"
        )
    source_manifests = _local_manifests(repo, source_sha)
    version, manifest_path = _authoritative_version(source_manifests)

    violations: list[str] = []
    deleted: list[str] = []
    if manifest_path is None:
        violations.append(
            "source tree declares no authoritative version manifest "
            f"({CMAKE_MANIFEST} or {PYPROJECT_MANIFEST})"
        )
    elif version is None:
        violations.append(f"no version is declared in {manifest_path}")
    elif STRICT_SEMVER_PATTERN.fullmatch(version) is None:
        violations.append(
            f"{manifest_path} version must be <major>.<minor>.<patch> without a "
            f"pre-release or build suffix: {version}"
        )
    else:
        master_sha = _resolve_ref(repo, master_ref)
        if master_sha is None:
            if not allow_missing_master_ref:
                raise RuntimeError(
                    f"master ref '{master_ref}' (and 'origin/{master_ref}') does "
                    "not resolve, so monotonicity cannot be verified; fetch the "
                    "ref, or pass --allow-missing-master-ref for a first-release "
                    "bootstrap"
                )
            print(
                f"WARNING: master ref '{master_ref}' not found; monotonicity "
                "NOT verified (first-release bootstrap).",
                file=sys.stderr,
            )
            master_manifests: dict[str, str] = {}
        else:
            master_manifests = _local_manifests(repo, master_sha)
        violations.extend(
            validate_release_version(
                head_ref=f"release/v{version}",
                source_manifests=source_manifests,
                master_manifests=master_manifests,
            )
        )

        deleted = sorted(
            path
            for path in _local_tree_paths(repo, source_sha)
            if is_development_only_path(path)
        )

    if violations:
        print(
            "REHEARSAL FAILED: fix these on develop before cutting refs:",
            file=sys.stderr,
        )
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1

    print(f"Rehearsal passed for source SHA {source_sha}.")
    print(f"  version:         {version} (from {manifest_path})")
    print(f"  release branch:  release/v{version}")
    print(f"  staging branch:  chore/release-v{version}")
    print(f"  master tag:      release-v{version}")
    print(f"  projection:      {len(deleted)} forbidden path(s) to delete")
    print("Master PR body field:")
    print(f"{DEVELOP_SOURCE_LABEL}: {source_sha}")
    return 0


def main() -> int:
    """Run the master merge gate for a GitHub pull-request event."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-path", type=Path)
    parser.add_argument(
        "--rehearse",
        action="store_true",
        help="run the local read-only promotion pre-flight instead of the hosted gate",
    )
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--source-ref", default="develop")
    parser.add_argument("--master-ref", default=MASTER_BRANCH)
    parser.add_argument(
        "--allow-missing-master-ref",
        action="store_true",
        help="permit a first-release bootstrap where no master ref exists yet; "
        "monotonicity is then explicitly reported as not verified",
    )
    args = parser.parse_args()

    if args.rehearse:
        try:
            return rehearse(
                args.repo,
                args.source_ref,
                args.master_ref,
                allow_missing_master_ref=args.allow_missing_master_ref,
            )
        except RuntimeError as error:
            print(f"REHEARSAL FAILED: {error}", file=sys.stderr)
            return 1

    if args.event_path is None:
        parser.error("--event-path is required unless --rehearse is given")

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
