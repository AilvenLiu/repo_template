#!/usr/bin/env python3
"""Validate the promotion-efficiency provisions in generated dummy projects.

Each test generates a real project for every supported profile and exercises
the artefacts that project actually receives, covering both platform
entrypoints (``AGENTS.md`` for Codex and ``CLAUDE.md`` for Claude Code) and all
three language profiles. The rehearsal test drives the shipped gate end-to-end
against the generated project's own two-phase git history.
"""

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

PROFILES = ("python", "cpp", "hybrid")
PLATFORM_ENTRYPOINTS = {"codex": "AGENTS.md", "claude": "CLAUDE.md"}

_PYPROJECT = '[project]\nname = "demo"\nversion = "{version}"\n'
_CMAKE = (
    "cmake_minimum_required(VERSION 3.24)\n"
    "project(demo VERSION {version} LANGUAGES CXX)\n"
)


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> dict[str, Path]:
    """Generate one dummy project per profile exactly once."""
    template_root = Path(__file__).parent.parent
    roots: dict[str, Path] = {}
    for profile in PROFILES:
        target = tmp_path_factory.mktemp(f"promotion_efficiency_{profile}") / "project"
        create_project(template_root, target, profile)
        roots[profile] = target
    return roots


def _gate(project_root: Path) -> ModuleType:
    """Load the master merge gate that the generated project actually received."""
    script = project_root / ".github" / "scripts" / "master-merge-gate.py"
    assert script.exists(), f"generated project is missing {script}"
    spec = importlib.util.spec_from_file_location(
        f"gate_{project_root.parent.name}", script
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_policy_defines_the_efficiency_provisions(
    generated, profile: str
) -> None:
    """The synced policy must carry every section 9 provision."""
    policy = (
        generated[profile]
        / ".agents"
        / "constraints"
        / "common"
        / "master-merge-policy.md"
    ).read_text()
    assert "## 9. Promotion efficiency" in policy
    assert "### 9.1 Validation provenance" in policy
    assert "### 9.2 Required validation per promotion step" in policy
    assert "### 9.3 Release cadence" in policy
    assert "### 9.4 Pre-flight rehearsal" in policy
    assert "### 9.5 Single-PR deterministic projection" in policy
    assert "Version-only direct update on `develop`" in policy
    assert "NEVER applies to a `hotfix/*`" in policy


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_skill_workflow_and_adr_expose_the_mechanisms(
    generated, profile: str
) -> None:
    """Skill, gate workflow, and ADR must ship the concrete mechanisms."""
    root = generated[profile]
    skill = (root / ".agents" / "skills" / "branch-governance" / "SKILL.md").read_text()
    assert ".agents/bin/agent-release bump" in skill
    assert ".agents/bin/agent-release prepare" in skill
    assert "validation or accepted provenance" in skill
    assert "sole ordinary release PR" in skill
    assert "Fetch `origin` immediately" in skill
    assert "direct-push bypass" in skill
    assert "metadata guard" in skill

    workflow = (root / ".github" / "workflows" / "master-merge-gate.yml").read_text()
    assert "REQUIRED_SOURCE_CHECKS" in workflow

    adr = root / ".agents" / "adr" / "0005-single-pr-release-promotion.md"
    assert adr.exists()
    assert "Amends" in adr.read_text()

    cicd = (
        root / ".agents" / "constraints" / "common" / "github-actions-cicd.md"
    ).read_text()
    assert "REQUIRED_SOURCE_CHECKS" in cicd
    assert "validation provenance" in cicd.lower()

    release_guidance = (
        root
        / ".agents"
        / "skills"
        / "service-cicd"
        / "references"
        / "release-promotion.md"
    ).read_text()
    assert "false evidence" in release_guidance


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_contributing_documents_the_cheap_promotion_path(
    generated, profile: str
) -> None:
    """The contributor guide must teach the efficient promotion habits."""
    text = (generated[profile] / "CONTRIBUTING.md").read_text()
    assert ".agents/bin/agent-release bump" in text
    assert ".agents/bin/agent-release prepare" in text
    assert "sole" in text
    assert "Release-Metadata-Parent-SHA" in text
    assert "fetch `origin` immediately" in text
    assert "chore/release-v" not in text


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("platform", sorted(PLATFORM_ENTRYPOINTS))
def test_both_platform_entrypoints_still_bind_the_governance(
    generated, profile: str, platform: str
) -> None:
    """The efficiency provisions must not have detached either entrypoint."""
    entrypoint = generated[profile] / PLATFORM_ENTRYPOINTS[platform]
    text = entrypoint.read_text()
    assert "master-merge-gate" in text
    assert "release/v<MAJOR>.<MINOR>.<PATCH>" in text
    assert "except through the bounded" in text


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_gate_ships_provenance_and_metadata_proof(
    generated, profile: str
) -> None:
    """The gate and wrapper each project receives expose the one-PR mechanisms."""
    root = generated[profile]
    gate = _gate(root)
    assert hasattr(gate, "validate_source_validation_provenance")
    assert hasattr(gate, "validate_release_metadata_only")
    assert hasattr(gate, "rehearse")
    assert not hasattr(gate, "validate_staging_pull_request")
    wrapper = root / ".agents" / "bin" / "agent-release"
    assert wrapper.is_file()
    assert wrapper.stat().st_mode & 0o111

    sha = "c" * 40
    payload = {
        "total_count": 1,
        "workflow_runs": [
            {
                "name": "validation",
                "status": "completed",
                "conclusion": "success",
                "event": "push",
                "head_branch": "develop",
                "head_sha": sha,
            }
        ],
    }
    assert not gate.validate_source_validation_provenance(
        workflow_runs_payload=payload,
        required_workflows=["validation"],
        expected_head_sha=sha,
    )
    assert gate.validate_source_validation_provenance(
        workflow_runs_payload=payload,
        required_workflows=["missing-workflow"],
        expected_head_sha=sha,
    )
    workflow = (
        generated[profile] / ".github" / "workflows" / "master-merge-gate.yml"
    ).read_text()
    assert "release/**" not in workflow


def _git(repo: Path, *args: str) -> str:
    process = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return process.stdout.strip()


def _default_branch(repo: Path) -> str:
    for candidate in ("master", "main"):
        probe = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--verify", candidate],
            capture_output=True,
            text=True,
        )
        if probe.returncode == 0:
            return candidate
    raise AssertionError("generated project has no master or main branch")


def _bump_develop_manifests(repo: Path, profile: str, version: str) -> None:
    if profile in ("cpp", "hybrid"):
        (repo / "CMakeLists.txt").write_text(_CMAKE.format(version=version))
    if profile in ("python", "hybrid"):
        (repo / "pyproject.toml").write_text(_PYPROJECT.format(version=version))
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "user.name=Test",
        "commit",
        "-m",
        "feat: bump version for first release train",
    )


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_project_rehearsal_end_to_end(
    generated, profile: str, tmp_path
) -> None:
    """--rehearse runs against a clone of the generated project's history.

    Cloning keeps the shared module fixture immutable and exercises the
    realistic develop-only clone, where the master baseline resolves through
    the origin remote-tracking ref.
    """
    source = generated[profile]
    assert _git(source, "branch", "--show-current") == "develop"
    repo = tmp_path / "clone"
    subprocess.run(
        ["git", "clone", "--quiet", str(source), str(repo)],
        capture_output=True,
        text=True,
        check=True,
    )
    assert _git(repo, "branch", "--show-current") == "develop"
    default_branch = _default_branch(source)

    _bump_develop_manifests(repo, profile, "0.2.0")
    result = subprocess.run(
        [
            sys.executable,
            str(repo / ".github" / "scripts" / "master-merge-gate.py"),
            "--rehearse",
            "--repo",
            str(repo),
            "--source-ref",
            "develop",
            "--master-ref",
            default_branch,
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "release/v0.2.0" in result.stdout
    assert "chore/release-v0.2.0" not in result.stdout
    assert "release-v0.2.0" in result.stdout
    assert "Develop-Source-SHA: " in result.stdout
    source_sha = _git(repo, "rev-parse", "develop")
    assert source_sha in result.stdout
