#!/usr/bin/env python3
"""Validate the semantic release version contract in generated dummy projects.

Each test generates a real project for every supported profile and exercises the
artefacts that project actually receives. That covers both platform entrypoints
(``AGENTS.md`` for Codex and ``CLAUDE.md`` for Claude Code) and all three
language profiles, rather than asserting against the template sources alone.
"""

import importlib.util
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
_CMAKE = "cmake_minimum_required(VERSION 3.24)\nproject(demo VERSION {version} LANGUAGES CXX)\n"


def _manifests(profile: str, version: str) -> dict[str, str]:
    """Return the authoritative manifest set one profile would ship."""
    if profile == "python":
        return {"pyproject.toml": _PYPROJECT.format(version=version)}
    if profile == "cpp":
        return {"CMakeLists.txt": _CMAKE.format(version=version)}
    return {
        "CMakeLists.txt": _CMAKE.format(version=version),
        "pyproject.toml": _PYPROJECT.format(version=version),
    }


@pytest.fixture(scope="module")
def generated(tmp_path_factory) -> dict[str, Path]:
    """Generate one dummy project per profile exactly once."""
    template_root = Path(__file__).parent.parent
    roots: dict[str, Path] = {}
    for profile in PROFILES:
        target = tmp_path_factory.mktemp(f"release_contract_{profile}") / "project"
        create_project(template_root, target, profile)
        roots[profile] = target
    return roots


def _gate(project_root: Path) -> ModuleType:
    """Load the master merge gate that the generated project actually received."""
    script = project_root / ".github" / "scripts" / "master-merge-gate.py"
    assert script.exists(), f"generated project is missing {script}"
    spec = importlib.util.spec_from_file_location(f"gate_{project_root.parent.name}", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("profile", PROFILES)
@pytest.mark.parametrize("platform", sorted(PLATFORM_ENTRYPOINTS))
def test_both_platform_entrypoints_state_the_version_contract(
    generated, profile: str, platform: str
) -> None:
    """Codex and Claude Code entrypoints must carry the identical contract."""
    entrypoint = generated[profile] / PLATFORM_ENTRYPOINTS[platform]
    text = entrypoint.read_text()
    assert "release/v<MAJOR>.<MINOR>.<PATCH>" in text
    assert "hotfix/v<MAJOR>.<MINOR>.<PATCH>" in text
    assert "release-v<MAJOR>.<MINOR>.<PATCH>" in text


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_contributing_documents_naming_and_ordering(
    generated, profile: str
) -> None:
    """The contributor guide must name every artefact and the bump ordering."""
    text = (generated[profile] / "CONTRIBUTING.md").read_text()
    assert "`release/v<MAJOR>.<MINOR>.<PATCH>`" in text
    assert "`chore/release-v<MAJOR>.<MINOR>.<PATCH>`" in text
    assert "`hotfix/v<MAJOR>.<MINOR>.<PATCH>`" in text
    assert "`release-v<MAJOR>.<MINOR>.<PATCH>`" in text
    assert "before" in text and "source commit" in text
    expected_manifest = "pyproject.toml" if profile == "python" else "CMakeLists.txt"
    assert expected_manifest in text
    if profile == "hybrid":
        assert "identical version" in text


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_constraint_and_skill_carry_the_contract(
    generated, profile: str
) -> None:
    """The synced constraint and skill must both define the version contract."""
    policy = (
        generated[profile]
        / ".agents"
        / "constraints"
        / "common"
        / "master-merge-policy.md"
    ).read_text()
    assert "## 8. Release version identity" in policy
    assert "release/v<major>.<minor>.<patch>" in policy
    assert "release-v<major>.<minor>.<patch>" in policy
    assert "Bump before you cut" in policy

    skill = (
        generated[profile] / ".agents" / "skills" / "branch-governance" / "SKILL.md"
    ).read_text()
    assert "release/v$VERSION" in skill
    assert "release-v$VERSION" in skill


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_gate_accepts_only_semantic_release_branches(
    generated, profile: str
) -> None:
    """Branch naming is enforced by the gate the project actually ships."""
    gate = _gate(generated[profile])

    def violations(head_ref: str) -> list[str]:
        return gate.validate_master_pull_request(
            base_ref="master",
            head_ref=head_ref,
            base_repository="example/project",
            head_repository="example/project",
            source_tree_paths=[],
        )

    assert not violations("release/v1.2.3")
    assert not violations("hotfix/v1.2.4")
    assert not violations("release/v0.1.0")
    for rejected in (
        "release/2026.07.22",
        "release/1.2.3",
        "release/v1.2",
        "release/v1.2.3-rc1",
        "release/v01.2.3",
        "hotfix/payment-timeout",
        "develop",
    ):
        assert violations(rejected), f"{profile}: expected rejection for {rejected}"


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_gate_binds_branch_version_to_the_profile_manifest(
    generated, profile: str
) -> None:
    """The branch name must match the authoritative manifest for this profile."""
    gate = _gate(generated[profile])

    assert not gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests=_manifests(profile, "1.2.3"),
        master_manifests={},
    )
    assert gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests=_manifests(profile, "1.2.4"),
        master_manifests={},
    )
    assert gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests={},
        master_manifests={},
    )


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_gate_rejects_unpromotable_version_strings(
    generated, profile: str
) -> None:
    """A promoted version carries no pre-release or build suffix."""
    gate = _gate(generated[profile])
    for rejected in ("1.2.3-dev", "1.2.3-rc1", "1.2.3+build7", "01.2.3"):
        assert gate.validate_release_version(
            head_ref="release/v1.2.3",
            source_manifests=_manifests(profile, rejected),
            master_manifests={},
        ), f"{profile}: expected rejection for {rejected}"


def test_generated_hybrid_gate_requires_manifest_agreement(generated) -> None:
    """CMake is authoritative for hybrid and pyproject must mirror it exactly."""
    gate = _gate(generated["hybrid"])
    assert not gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests={
            "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
            "pyproject.toml": _PYPROJECT.format(version="1.2.3"),
        },
        master_manifests={},
    )
    assert gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests={
            "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
            "pyproject.toml": _PYPROJECT.format(version="1.2.4"),
        },
        master_manifests={},
    )


@pytest.mark.parametrize("profile", PROFILES)
def test_generated_gate_enforces_version_monotonicity(generated, profile: str) -> None:
    """A candidate must strictly exceed the version already on master."""
    gate = _gate(generated[profile])
    source = _manifests(profile, "1.2.3")

    assert not gate.validate_release_version(
        head_ref="release/v1.2.3",
        source_manifests=source,
        master_manifests=_manifests(profile, "1.2.2"),
    )
    for blocked in ("1.2.3", "1.3.0", "2.0.0"):
        assert gate.validate_release_version(
            head_ref="release/v1.2.3",
            source_manifests=source,
            master_manifests=_manifests(profile, blocked),
        ), f"{profile}: expected rejection against master {blocked}"
