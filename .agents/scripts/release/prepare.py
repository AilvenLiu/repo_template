#!/usr/bin/env python3
"""Prepare one-PR release candidates without checkout, stash, or staging PRs."""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Mapping, Sequence

STRICT_SEMVER_PATTERN = re.compile(
    r"^(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)$"
)
RELEASE_BRANCH_PREFIX = "refs/heads/release/v"
DEVELOP_SOURCE_LABEL = "Develop-Source-SHA"
RELEASE_METADATA_PARENT_LABEL = "Release-Metadata-Parent-SHA"

_DEVELOPMENT_ONLY_ROOTS = (
    b".ai",
    b".agents",
    b".claude",
    b".codex",
    b"agent_roadmaps",
)
_DEVELOPMENT_ONLY_FILES = (b"AGENTS.md", b"CLAUDE.md", b"CODEX.md")


class ReleasePreparationError(RuntimeError):
    """Raised when a release operation cannot preserve the branch contract."""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _run_git(
    repo: Path,
    *arguments: str,
    input_text: str | None = None,
    environment: Mapping[str, str] | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    merged_environment = os.environ.copy()
    merged_environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    if environment is not None:
        merged_environment.update(environment)
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            input=input_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=merged_environment,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired, UnicodeDecodeError) as error:
        raise ReleasePreparationError(
            f"git {' '.join(arguments)} failed: {error}"
        ) from error
    if check and process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise ReleasePreparationError(f"git {' '.join(arguments)} failed: {detail}")
    return process


def _run_git_bytes(
    repo: Path,
    arguments: Sequence[str],
    *,
    input_bytes: bytes | None = None,
    environment: Mapping[str, str] | None = None,
) -> bytes:
    merged_environment = os.environ.copy()
    merged_environment.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    if environment is not None:
        merged_environment.update(environment)
    try:
        process = subprocess.run(
            ["git", "-C", str(repo), *arguments],
            input=input_bytes,
            capture_output=True,
            env=merged_environment,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReleasePreparationError(
            f"git {' '.join(arguments)} failed: {error}"
        ) from error
    if process.returncode != 0:
        detail = process.stderr.decode("utf-8", errors="replace").strip()
        raise ReleasePreparationError(f"git {' '.join(arguments)} failed: {detail}")
    return process.stdout


def _git_output(repo: Path, *arguments: str) -> str:
    return _run_git(repo, *arguments).stdout.strip()


def _load_gate(repo: Path) -> ModuleType:
    path = repo / ".github" / "scripts" / "master-merge-gate.py"
    spec = importlib.util.spec_from_file_location("agent_release_master_gate", path)
    if spec is None or spec.loader is None:
        raise ReleasePreparationError(f"cannot load master merge gate: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _current_branch(repo: Path) -> str:
    return _git_output(repo, "branch", "--show-current")


def _require_clean_worktree(repo: Path) -> None:
    status = _git_output(repo, "status", "--porcelain=v1", "--untracked-files=normal")
    if status:
        raise ReleasePreparationError(
            "release preparation requires a clean worktree; commit or remove "
            "unrelated changes instead of stashing them"
        )


def _resolve_commit(repo: Path, ref: str) -> str:
    process = _run_git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    if process.returncode != 0:
        raise ReleasePreparationError(f"ref does not resolve to a commit: {ref}")
    return process.stdout.strip()


def _optional_commit(repo: Path, ref: str) -> str | None:
    process = _run_git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}", check=False)
    return process.stdout.strip() if process.returncode == 0 else None


def _require_current_develop(repo: Path) -> str:
    branch = _current_branch(repo)
    if branch != "develop":
        raise ReleasePreparationError(
            "the lightweight release-version exception runs only on develop"
        )
    head = _resolve_commit(repo, "HEAD")
    remote = _optional_commit(repo, "refs/remotes/origin/develop")
    if remote is not None and remote != head:
        raise ReleasePreparationError(
            "local develop must equal the fetched origin/develop before a "
            "release-version commit; fetch and reconcile normally"
        )
    return head


def _version_tuple(value: str) -> tuple[int, int, int]:
    if STRICT_SEMVER_PATTERN.fullmatch(value) is None:
        raise ReleasePreparationError(
            "release version must be <major>.<minor>.<patch> without a suffix"
        )
    return tuple(int(component) for component in value.split("."))  # type: ignore[return-value]


def _replace_pyproject_version(text: str, version: str, gate: ModuleType) -> str:
    entry = gate._pyproject_version_entry(text)
    if entry is None:
        raise ReleasePreparationError(
            "pyproject.toml must declare one unambiguous canonical version"
        )
    target, _ = entry

    current_table = ""
    replacements = 0
    output: list[str] = []
    table_pattern = re.compile(r"^\s*\[([^]]+)]\s*(?:#.*)?$")
    version_pattern = re.compile(
        r"^(\s*version\s*=\s*)(?P<quote>[\"'])(?:[^\"']*)(?P=quote)(\s*(?:#.*)?)$"
    )
    for line in text.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body) :]
        table_match = table_pattern.fullmatch(body)
        if table_match is not None:
            current_table = table_match.group(1).strip()
        version_match = version_pattern.fullmatch(body)
        if current_table == target and version_match is not None:
            replacements += 1
            quote_character = version_match.group("quote")
            body = (
                f"{version_match.group(1)}{quote_character}{version}"
                f"{quote_character}{version_match.group(3)}"
            )
        output.append(body + ending)
    if replacements != 1:
        raise ReleasePreparationError(
            "pyproject.toml must contain exactly one authoritative version assignment"
        )
    updated = "".join(output)
    if gate.parse_pyproject_version(updated) != version:
        raise ReleasePreparationError("could not verify updated pyproject.toml version")
    return updated


def _replace_cmake_version(text: str, version: str, gate: ModuleType) -> str:
    comment_masked = re.sub(r"(?m)#.*$", lambda match: " " * len(match.group(0)), text)
    project_match = re.search(r"(?is)\bproject\s*\((.*?)\)", comment_masked)
    if project_match is None:
        raise ReleasePreparationError("CMakeLists.txt declares no project() command")
    inner_start, inner_end = project_match.span(1)
    masked_inner = comment_masked[inner_start:inner_end]
    version_pattern = re.compile(r"(?i)(\bVERSION\s+)([0-9][0-9A-Za-z.+-]*)")
    matches = list(version_pattern.finditer(masked_inner))
    if len(matches) != 1:
        raise ReleasePreparationError(
            "CMakeLists.txt project() must contain exactly one VERSION"
        )
    value_start, value_end = matches[0].span(2)
    absolute_start = inner_start + value_start
    absolute_end = inner_start + value_end
    updated = text[:absolute_start] + version + text[absolute_end:]
    if gate.parse_cmake_version(updated) != version:
        raise ReleasePreparationError("could not verify updated CMake version")
    return updated


def _manifest_paths(repo: Path) -> tuple[str, ...]:
    cmake = repo / "CMakeLists.txt"
    pyproject = repo / "pyproject.toml"
    if cmake.is_file():
        return (
            ("CMakeLists.txt", "pyproject.toml")
            if pyproject.is_file()
            else ("CMakeLists.txt",)
        )
    if pyproject.is_file():
        return ("pyproject.toml",)
    raise ReleasePreparationError(
        "project declares neither CMakeLists.txt nor pyproject.toml"
    )


def bump_version(repo: Path, version: str, gate: ModuleType) -> int:
    """Commit a narrowly proven version-only update directly on develop."""
    _require_clean_worktree(repo)
    parent_sha = _require_current_develop(repo)
    requested = _version_tuple(version)
    paths = _manifest_paths(repo)

    originals = {path: (repo / path).read_text(encoding="utf-8") for path in paths}
    current_version, _ = gate._authoritative_version(originals)
    if current_version is None or requested <= _version_tuple(current_version):
        raise ReleasePreparationError(
            f"release version {version} must be greater than current version "
            f"{current_version}"
        )

    updates: dict[str, str] = {}
    for path, text in originals.items():
        updates[path] = (
            _replace_cmake_version(text, version, gate)
            if path == "CMakeLists.txt"
            else _replace_pyproject_version(text, version, gate)
        )

    if len(paths) == 2 and gate.parse_cmake_version(
        updates["CMakeLists.txt"]
    ) != gate.parse_pyproject_version(updates["pyproject.toml"]):
        raise ReleasePreparationError("hybrid version manifests must agree")

    normalisation_violations: list[str] = []
    for path in paths:
        normaliser = (
            gate._normalise_cmake_release_version
            if path == "CMakeLists.txt"
            else gate._normalise_pyproject_release_version
        )
        if normaliser(originals[path]) != normaliser(updates[path]):
            normalisation_violations.append(path)
    if normalisation_violations:
        raise ReleasePreparationError(
            "version update changes content outside the authoritative field: "
            + ", ".join(normalisation_violations)
        )

    ref_updated = False
    try:
        for path, updated in updates.items():
            (repo / path).write_text(updated, encoding="utf-8")

        changed = {
            line
            for line in _git_output(repo, "diff", "--name-only", "--").splitlines()
            if line
        }
        if changed != set(paths):
            raise ReleasePreparationError(
                "version bump produced an unexpected changed-path set: "
                + ", ".join(sorted(changed))
            )
        _run_git(repo, "diff", "--check")
        _run_git(repo, "add", "--", *paths)
        _run_git(repo, "diff", "--cached", "--check")
        tree_sha = _git_output(repo, "write-tree")
        source_sha = _run_git(
            repo,
            "commit-tree",
            tree_sha,
            "-p",
            parent_sha,
            input_text=f"chore(release): bump version to {version}\n",
        ).stdout.strip()
        violations = _validate_local_metadata_commit(
            repo, gate, parent_sha=parent_sha, source_sha=source_sha
        )
        if violations:
            raise ReleasePreparationError(
                "candidate release metadata failed independent verification: "
                + "; ".join(violations)
            )
        _run_git(
            repo,
            "update-ref",
            "refs/heads/develop",
            source_sha,
            parent_sha,
        )
        ref_updated = True
    except (OSError, UnicodeError, ReleasePreparationError) as error:
        if not ref_updated:
            _run_git(repo, "reset", "--quiet", "HEAD", "--", *paths, check=False)
            for path, original in originals.items():
                (repo / path).write_text(original, encoding="utf-8")
        if isinstance(error, ReleasePreparationError):
            raise
        raise ReleasePreparationError(
            f"could not write release manifests: {error}"
        ) from error

    if _resolve_commit(repo, "HEAD") != source_sha:
        raise ReleasePreparationError(
            "release metadata compare-and-swap did not update checked-out develop"
        )
    _require_clean_worktree(repo)

    print(f"Committed release metadata {current_version} -> {version} on develop.")
    print(f"  parent SHA:  {parent_sha}")
    print(f"  source SHA:  {source_sha}")
    print("No build or test job was run by this bounded metadata operation.")
    print("Push normally (never force), then prepare the release candidate.")
    return 0


def _tree_snapshot(repo: Path, commit: str) -> dict[str, tuple[str, str, str]]:
    raw = _run_git_bytes(repo, ["ls-tree", "-r", "-z", commit])
    snapshot: dict[str, tuple[str, str, str]] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        metadata, path_bytes = record.split(b"\t", maxsplit=1)
        mode, object_type, object_sha = metadata.decode("ascii").split()
        snapshot[os.fsdecode(path_bytes)] = (mode, object_type, object_sha)
    return snapshot


def _manifests_at(repo: Path, commit: str) -> dict[str, str]:
    manifests: dict[str, str] = {}
    for path in ("CMakeLists.txt", "pyproject.toml"):
        exists = _run_git(repo, "cat-file", "-e", f"{commit}:{path}", check=False)
        if exists.returncode != 0:
            continue
        manifests[path] = _run_git(repo, "show", f"{commit}:{path}").stdout
    return manifests


def _parent_shas(repo: Path, commit: str) -> list[str]:
    fields = _git_output(repo, "rev-list", "--parents", "-n", "1", commit).split()
    return fields[1:]


def _validate_local_metadata_commit(
    repo: Path,
    gate: ModuleType,
    *,
    parent_sha: str,
    source_sha: str,
) -> list[str]:
    return gate.validate_release_metadata_only(
        parent_sha=parent_sha,
        source_parent_shas=_parent_shas(repo, source_sha),
        parent_tree=_tree_snapshot(repo, parent_sha),
        source_tree=_tree_snapshot(repo, source_sha),
        parent_manifests=_manifests_at(repo, parent_sha),
        source_manifests=_manifests_at(repo, source_sha),
    )


def verify_metadata(
    repo: Path, gate: ModuleType, *, parent_sha: str, source_sha: str
) -> int:
    parent = _resolve_commit(repo, parent_sha)
    source = _resolve_commit(repo, source_sha)
    violations = _validate_local_metadata_commit(
        repo, gate, parent_sha=parent, source_sha=source
    )
    if violations:
        for violation in violations:
            print(f"- {violation}", file=sys.stderr)
        return 1
    print(f"Release metadata proof passed: {parent} -> {source}")
    return 0


def _is_development_only_path(path: bytes) -> bool:
    if path in _DEVELOPMENT_ONLY_FILES:
        return True
    if any(
        path == root or path.startswith(root + b"/") for root in _DEVELOPMENT_ONLY_ROOTS
    ):
        return True
    if path == b"docs" or path.startswith(b"docs/"):
        return not (path == b"docs/changelog" or path.startswith(b"docs/changelog/"))
    return False


def _projected_tree(repo: Path, source_sha: str) -> str:
    with tempfile.TemporaryDirectory(prefix="agent-release-index-") as temp_dir:
        index_path = Path(temp_dir) / "index"
        environment = {"GIT_INDEX_FILE": str(index_path)}
        _run_git(repo, "read-tree", f"{source_sha}^{{tree}}", environment=environment)
        tracked = _run_git_bytes(repo, ["ls-files", "-z"], environment=environment)
        removals = [
            path
            for path in tracked.split(b"\0")
            if path and _is_development_only_path(path)
        ]
        if removals:
            _run_git_bytes(
                repo,
                ["update-index", "--force-remove", "-z", "--stdin"],
                input_bytes=b"\0".join(removals) + b"\0",
                environment=environment,
            )
        return _run_git(repo, "write-tree", environment=environment).stdout.strip()


def _metadata_parent_if_valid(
    repo: Path, gate: ModuleType, source_sha: str
) -> str | None:
    parents = _parent_shas(repo, source_sha)
    if len(parents) != 1:
        return None
    parent = parents[0]
    violations = _validate_local_metadata_commit(
        repo, gate, parent_sha=parent, source_sha=source_sha
    )
    return None if violations else parent


def _validate_existing_candidate(
    repo: Path,
    gate: ModuleType,
    *,
    candidate_sha: str,
    source_sha: str,
    expected_tree_sha: str,
) -> None:
    if _parent_shas(repo, candidate_sha) != [source_sha]:
        raise ReleasePreparationError(
            "existing release ref does not have the recorded develop source "
            "as its only parent"
        )
    candidate_tree = _git_output(repo, "rev-parse", f"{candidate_sha}^{{tree}}")
    if candidate_tree != expected_tree_sha:
        raise ReleasePreparationError(
            "existing release ref has a different projected tree; refusing to move it"
        )
    violations = gate.validate_release_projection(
        develop_tree=_tree_snapshot(repo, source_sha),
        release_tree=_tree_snapshot(repo, candidate_sha),
    )
    if violations:
        raise ReleasePreparationError(
            "existing release ref violates projection policy: " + "; ".join(violations)
        )


def prepare_release(
    repo: Path,
    gate: ModuleType,
    *,
    source_ref: str,
    master_ref: str,
    allow_missing_master_ref: bool,
) -> int:
    """Create an immutable local release ref at its final sanitised commit."""
    _require_clean_worktree(repo)
    if source_ref != "develop":
        raise ReleasePreparationError(
            "normal release preparation accepts only the develop source ref"
        )
    if _current_branch(repo) != "develop":
        raise ReleasePreparationError(
            "prepare releases from a checked-out develop branch"
        )
    source_sha = _resolve_commit(repo, source_ref)
    if _resolve_commit(repo, "HEAD") != source_sha:
        raise ReleasePreparationError("checked-out develop must equal its branch ref")
    remote_source = _optional_commit(repo, f"refs/remotes/origin/{source_ref}")
    if remote_source is not None and remote_source != source_sha:
        raise ReleasePreparationError(
            f"local {source_ref} must equal its fetched origin ref before release"
        )

    rehearsal_result = gate.rehearse(
        repo,
        source_ref,
        master_ref,
        allow_missing_master_ref=allow_missing_master_ref,
    )
    if rehearsal_result != 0:
        return rehearsal_result

    manifests = _manifests_at(repo, source_sha)
    version, _ = gate._authoritative_version(manifests)
    if version is None or STRICT_SEMVER_PATTERN.fullmatch(version) is None:
        raise ReleasePreparationError("source declares no promotable version")
    release_ref = f"{RELEASE_BRANCH_PREFIX}{version}"
    release_branch = release_ref.removeprefix("refs/heads/")
    tree_sha = _projected_tree(repo, source_sha)

    projection_violations = gate.validate_release_projection(
        develop_tree=_tree_snapshot(repo, source_sha),
        release_tree=_tree_snapshot(repo, tree_sha),
    )
    if projection_violations:
        raise ReleasePreparationError(
            "generated tree violates projection policy: "
            + "; ".join(projection_violations)
        )

    local_existing = _optional_commit(repo, release_ref)
    remote_existing = _optional_commit(repo, f"refs/remotes/origin/{release_branch}")
    if (
        local_existing is not None
        and remote_existing is not None
        and local_existing != remote_existing
    ):
        raise ReleasePreparationError(
            "local and fetched remote release refs disagree; refusing to choose"
        )
    existing = local_existing or remote_existing
    reused = existing is not None
    if existing is not None:
        candidate_sha = existing
        _validate_existing_candidate(
            repo,
            gate,
            candidate_sha=candidate_sha,
            source_sha=source_sha,
            expected_tree_sha=tree_sha,
        )
        if local_existing is None:
            _run_git(repo, "update-ref", release_ref, candidate_sha, "")
    else:
        message = (
            f"chore(release): project v{version} for master\n\n"
            f"{DEVELOP_SOURCE_LABEL}: {source_sha}\n"
        )
        candidate_sha = _run_git(
            repo,
            "commit-tree",
            tree_sha,
            "-p",
            source_sha,
            input_text=message,
        ).stdout.strip()
        _run_git(repo, "update-ref", release_ref, candidate_sha, "")

    if (
        _current_branch(repo) != "develop"
        or _resolve_commit(repo, "HEAD") != source_sha
    ):
        raise ReleasePreparationError(
            "release preparation unexpectedly changed the checked-out branch or HEAD"
        )
    _require_clean_worktree(repo)

    metadata_parent = _metadata_parent_if_valid(repo, gate, source_sha)
    print(
        f"{'Reused' if reused else 'Created'} immutable local release branch "
        f"{release_branch}."
    )
    print(f"  develop source SHA: {source_sha}")
    print(f"  release commit SHA: {candidate_sha}")
    print(f"  projected tree SHA: {tree_sha}")
    print(
        "No checkout or stash was used. Never update, force-push, or recycle this ref."
    )
    print("Create the remote ref with this exact non-force mapping.")
    print("Hosted protection must reject every later update or deletion:")
    print(f"  git push origin {candidate_sha}:{release_ref}")
    print("Master PR body fields:")
    print(f"{DEVELOP_SOURCE_LABEL}: {source_sha}")
    if metadata_parent is not None:
        print(f"{RELEASE_METADATA_PARENT_LABEL}: {metadata_parent}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=_repo_root())
    subparsers = parser.add_subparsers(dest="command", required=True)

    bump = subparsers.add_parser(
        "bump", help="commit a strict version-only update directly on develop"
    )
    bump.add_argument("version")

    prepare = subparsers.add_parser(
        "prepare", help="create the final sanitised release branch without checkout"
    )
    prepare.add_argument("--source-ref", default="develop")
    prepare.add_argument("--master-ref", default="master")
    prepare.add_argument("--allow-missing-master-ref", action="store_true")

    verify = subparsers.add_parser(
        "verify-metadata", help="prove a commit changes only release version fields"
    )
    verify.add_argument("--parent", required=True)
    verify.add_argument("--source", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    repo = args.repo.resolve()
    gate = _load_gate(repo)
    try:
        if args.command == "bump":
            return bump_version(repo, args.version, gate)
        if args.command == "prepare":
            return prepare_release(
                repo,
                gate,
                source_ref=args.source_ref,
                master_ref=args.master_ref,
                allow_missing_master_ref=args.allow_missing_master_ref,
            )
        if args.command == "verify-metadata":
            return verify_metadata(
                repo, gate, parent_sha=args.parent, source_sha=args.source
            )
    except ReleasePreparationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
