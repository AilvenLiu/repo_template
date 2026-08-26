#!/usr/bin/env python3
"""End-to-end tests for single-PR release preparation in generated projects."""

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent
        / ".agents"
        / "skills"
        / "create-project"
        / "scripts"
    ),
)

from init import create_project  # type: ignore[import-not-found]

ROOT = Path(__file__).parent.parent
PROFILES = ("python", "cpp", "hybrid")
_PYPROJECT = (
    '[project]\nname = "demo"\nversion = "0.1.0"  # authoritative release version\n'
)


def _run(
    repo: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    process = subprocess.run(
        [*arguments],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if check and process.returncode != 0:
        raise AssertionError(
            f"command failed ({process.returncode}): {' '.join(arguments)}\n"
            f"{process.stdout}\n{process.stderr}"
        )
    return process


def _git(repo: Path, *arguments: str) -> str:
    return _run(repo, "git", *arguments).stdout.strip()


def _load_gate(repo: Path) -> ModuleType:
    path = repo / ".github" / "scripts" / "master-merge-gate.py"
    spec = importlib.util.spec_from_file_location(
        f"release_e2e_gate_{repo.parent.name}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clone_generated_project(tmp_path: Path, profile: str) -> Path:
    seed = tmp_path / "seed"
    create_project(ROOT, seed, profile)

    remote = tmp_path / "remote.git"
    _run(tmp_path, "git", "clone", "--bare", "--quiet", str(seed), str(remote))
    repo = tmp_path / "work"
    _run(
        tmp_path,
        "git",
        "clone",
        "--quiet",
        "--branch",
        "develop",
        str(remote),
        str(repo),
    )
    _git(repo, "config", "user.name", "Release Test")
    _git(repo, "config", "user.email", "release-test@example.invalid")

    (repo / "docs" / "changelog").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "changelog" / "0.2.0.md").write_text("# 0.2.0\n", encoding="utf-8")
    if profile == "python":
        (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "feat: prepare reviewed release content")
    _git(repo, "push", "origin", "develop")

    _git(repo, "fetch", "--quiet", "origin")
    init = _run(
        repo,
        ".agents/bin/agent-init",
        "--platform",
        "codex",
        check=False,
    )
    assert init.returncode == 0, init.stdout + init.stderr
    assert not _git(repo, "status", "--porcelain=v1")
    return repo


def _tree(repo: Path, revision: str) -> dict[str, tuple[str, str, str]]:
    output = _run(
        repo,
        "git",
        "ls-tree",
        "-r",
        revision,
    ).stdout
    result: dict[str, tuple[str, str, str]] = {}
    for line in output.splitlines():
        metadata, path = line.split("\t", maxsplit=1)
        mode, object_type, object_sha = metadata.split()
        result[path] = (mode, object_type, object_sha)
    return result


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_release_wrapper_runs_single_candidate_flow_end_to_end(
    tmp_path: Path, profile: str
) -> None:
    repo = _clone_generated_project(tmp_path, profile)
    parent_sha = _git(repo, "rev-parse", "HEAD")

    bump = _run(
        repo,
        ".agents/bin/agent-release",
        "bump",
        "0.2.0",
        check=False,
    )
    assert bump.returncode == 0, bump.stdout + bump.stderr
    source_sha = _git(repo, "rev-parse", "HEAD")
    assert source_sha != parent_sha
    expected_manifests = (
        {"pyproject.toml"}
        if profile == "python"
        else {"CMakeLists.txt"}
        if profile == "cpp"
        else {"CMakeLists.txt", "pyproject.toml"}
    )
    changed = set(
        _git(
            repo,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            source_sha,
        ).splitlines()
    )
    assert changed == expected_manifests
    assert parent_sha in bump.stdout
    assert source_sha in bump.stdout
    assert "No build or test job was run" in bump.stdout
    assert not _git(repo, "status", "--porcelain=v1")

    _git(repo, "push", "origin", "develop")
    _git(repo, "fetch", "--quiet", "origin")
    prepared = _run(
        repo,
        ".agents/bin/agent-release",
        "prepare",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    release_ref = "refs/heads/release/v0.2.0"
    candidate_sha = _git(repo, "rev-parse", release_ref)

    assert _git(repo, "branch", "--show-current") == "develop"
    assert _git(repo, "rev-parse", "HEAD") == source_sha
    assert not _git(repo, "status", "--porcelain=v1")
    assert _git(repo, "rev-parse", f"{candidate_sha}^") == source_sha
    assert f"Develop-Source-SHA: {source_sha}" in prepared.stdout
    assert f"Release-Metadata-Parent-SHA: {parent_sha}" in prepared.stdout
    assert f"git push origin {candidate_sha}:{release_ref}" in prepared.stdout
    assert "chore/release" not in prepared.stdout

    gate = _load_gate(repo)
    source_tree = _tree(repo, source_sha)
    candidate_tree = _tree(repo, candidate_sha)
    assert candidate_tree == {
        path: identity
        for path, identity in source_tree.items()
        if not gate.is_development_only_path(path)
    }
    assert not gate.validate_release_projection(
        develop_tree=source_tree,
        release_tree=candidate_tree,
    )
    assert "docs/changelog/" in "\n".join(candidate_tree)
    assert not any(
        ref.startswith("chore/release")
        for ref in _git(
            repo,
            "for-each-ref",
            "--format=%(refname:short)",
            "refs/heads",
        ).splitlines()
    )

    repeated = _run(
        repo,
        ".agents/bin/agent-release",
        "prepare",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert "Reused immutable local release branch" in repeated.stdout
    assert _git(repo, "rev-parse", release_ref) == candidate_sha


@pytest.mark.parametrize("profile", PROFILES)
def test_prepare_refuses_to_move_a_divergent_existing_release_ref(
    tmp_path: Path, profile: str
) -> None:
    repo = _clone_generated_project(tmp_path, profile)
    bump = _run(repo, ".agents/bin/agent-release", "bump", "0.2.0", check=False)
    assert bump.returncode == 0, bump.stdout + bump.stderr
    _git(repo, "push", "origin", "develop")
    _git(repo, "fetch", "--quiet", "origin")

    release_ref = "refs/heads/release/v0.2.0"
    source_sha = _git(repo, "rev-parse", "HEAD")
    _git(repo, "update-ref", release_ref, source_sha)
    rejected = _run(
        repo,
        ".agents/bin/agent-release",
        "prepare",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert rejected.returncode == 1
    assert "refusing to move it" in rejected.stderr or "only parent" in rejected.stderr
    assert _git(repo, "rev-parse", release_ref) == source_sha


def test_release_commands_fail_before_mutation_on_dirty_or_wrong_source(
    tmp_path: Path,
) -> None:
    repo = _clone_generated_project(tmp_path, "cpp")
    original = _git(repo, "rev-parse", "HEAD")
    (repo / "unrelated.txt").write_text("dirty\n", encoding="utf-8")

    dirty = _run(
        repo,
        ".agents/bin/agent-release",
        "bump",
        "0.2.0",
        check=False,
    )
    assert dirty.returncode == 1
    assert "clean worktree" in dirty.stderr
    assert _git(repo, "rev-parse", "HEAD") == original
    (repo / "unrelated.txt").unlink()

    wrong_source = _run(
        repo,
        ".agents/bin/agent-release",
        "prepare",
        "--source-ref",
        "master",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert wrong_source.returncode == 1
    assert "only the develop source ref" in wrong_source.stderr
    assert _git(repo, "rev-parse", "HEAD") == original
    assert (
        _run(
            repo,
            "git",
            "rev-parse",
            "--verify",
            "refs/heads/release/v0.1.0",
            check=False,
        ).returncode
        != 0
    )


def test_remote_candidate_retry_recreates_only_the_matching_local_ref(
    tmp_path: Path,
) -> None:
    first = _clone_generated_project(tmp_path / "first", "cpp")
    bump = _run(first, ".agents/bin/agent-release", "bump", "0.2.0", check=False)
    assert bump.returncode == 0, bump.stdout + bump.stderr
    _git(first, "push", "origin", "develop")

    prepared = _run(
        first,
        ".agents/bin/agent-release",
        "prepare",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert prepared.returncode == 0, prepared.stdout + prepared.stderr
    release_ref = "refs/heads/release/v0.2.0"
    candidate_sha = _git(first, "rev-parse", release_ref)
    _git(first, "push", "origin", f"{release_ref}:{release_ref}")

    retry = tmp_path / "retry"
    _run(
        tmp_path,
        "git",
        "clone",
        "--quiet",
        "--branch",
        "develop",
        str(tmp_path / "first" / "remote.git"),
        str(retry),
    )
    _git(retry, "config", "user.name", "Release Test")
    _git(retry, "config", "user.email", "release-test@example.invalid")
    initialized = _run(
        retry,
        ".agents/bin/agent-init",
        "--platform",
        "codex",
        check=False,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr

    repeated = _run(
        retry,
        ".agents/bin/agent-release",
        "prepare",
        "--master-ref",
        "origin/master",
        check=False,
    )
    assert repeated.returncode == 0, repeated.stdout + repeated.stderr
    assert "Reused immutable local release branch" in repeated.stdout
    assert _git(retry, "rev-parse", release_ref) == candidate_sha


def test_failed_bump_commit_restores_manifest_index_and_worktree(
    tmp_path: Path,
) -> None:
    repo = _clone_generated_project(tmp_path, "cpp")
    original_head = _git(repo, "rev-parse", "HEAD")
    original_manifest = (repo / "CMakeLists.txt").read_bytes()
    _git(repo, "config", "user.name", "")
    _git(repo, "config", "user.email", "")

    failed = _run(
        repo,
        ".agents/bin/agent-release",
        "bump",
        "0.2.0",
        check=False,
    )
    assert failed.returncode != 0
    assert (
        "empty ident name" in failed.stderr
        or "Author identity unknown" in failed.stderr
    )
    assert _git(repo, "rev-parse", "HEAD") == original_head
    assert (repo / "CMakeLists.txt").read_bytes() == original_manifest
    assert _git(repo, "status", "--short") == ""


def test_failed_independent_proof_never_moves_develop(
    tmp_path: Path, monkeypatch
) -> None:
    repo = _clone_generated_project(tmp_path, "cpp")
    original_head = _git(repo, "rev-parse", "HEAD")
    original_manifest = (repo / "CMakeLists.txt").read_bytes()
    path = repo / ".agents" / "scripts" / "release" / "prepare.py"
    spec = importlib.util.spec_from_file_location("release_prepare_failure", path)
    assert spec is not None and spec.loader is not None
    release = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(release)
    monkeypatch.setattr(
        release,
        "_validate_local_metadata_commit",
        lambda *args, **kwargs: ["injected independent proof failure"],
    )

    with pytest.raises(
        release.ReleasePreparationError,
        match="injected independent proof failure",
    ):
        release.bump_version(repo, "0.2.0", _load_gate(repo))

    assert _git(repo, "rev-parse", "HEAD") == original_head
    assert (repo / "CMakeLists.txt").read_bytes() == original_manifest
    assert _git(repo, "status", "--short") == ""
