#!/usr/bin/env python3
"""End-to-end tests for project generation and Codex parity assets."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

# Add import roots
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create-project" / "scripts"))

from capability_audit import run_audit
from capability_audit import _entry_enabled_for_repo
from init import create_project


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


def _assert_common_generated_assets(target: Path, project_type: str) -> None:
    ai_skill_dirs = {path.name for path in (target / ".ai" / "skills").iterdir() if path.is_dir()}
    claude_skill_dirs = {path.name for path in (target / ".claude" / "skills").iterdir() if path.is_dir()}

    assert (target / ".ai" / "capabilities.yml").exists()
    assert (target / ".ai" / "constraints" / "common" / "karpathy-guidelines.md").exists()
    assert (target / ".ai" / "project.yml").exists()
    assert (target / ".ai" / "scripts" / "session_init.py").exists()
    # .codex/ has been deleted; codex consumes AGENTS.md + .ai/skills/ instead.
    assert not (target / ".codex").exists()
    # Canonical skill bodies live under .ai/skills/<name>/SKILL.md.
    assert (target / ".ai" / "skills" / "build" / "SKILL.md").exists()
    assert (target / ".ai" / "skills" / "init" / "SKILL.md").exists()
    assert (target / ".ai" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
    assert (target / ".ai" / "skills" / "navigate" / "SKILL.md").exists()
    # Claude stubs (frontmatter for slash-command discovery) must exist for each.
    assert (target / ".claude" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
    assert (target / "bin" / "agent-build").exists()
    manifest = yaml.safe_load((Path(__file__).parent.parent / ".ai" / "capabilities.yml").read_text())
    expected_skills = {
        entry["id"]
        for entry in manifest.get("common_requirements", {}).get("project_skills", [])
        if entry.get("required")
        and not entry.get("template_only")
        and _entry_enabled_for_repo(entry, False, target)
    }
    if project_type in {"python", "hybrid"}:
        assert (target / ".ai" / "skills" / "python-env-setup" / "SKILL.md").exists()
        assert (target / ".claude" / "skills" / "python-env-setup" / "SKILL.md").exists()
        assert (target / "bin" / "agent-python-env-setup").exists()
    else:
        assert not (target / ".ai" / "skills" / "python-env-setup").exists()
        assert not (target / ".claude" / "skills" / "python-env-setup").exists()
        assert not (target / ".claude" / "docs" / "python-env-quick-reference.md").exists()
        assert not (target / "bin" / "agent-python-env-setup").exists()
        assert (target / "conanfile.txt").exists()
    if project_type == "hybrid":
        assert (target / "pyproject.toml").exists()
        assert (target / "CMakeLists.txt").exists()
    assert expected_skills <= ai_skill_dirs
    # Claude has the same skills + the 'common' utility folder.
    assert expected_skills <= (claude_skill_dirs - {"common"})
    assert (target / "bin" / "agent-init").exists()
    assert (target / "bin" / "agent-precommit").exists()
    assert (target / "bin" / "agent-check-constraints").exists()
    assert (target / "bin" / "agent-roadmap").exists()
    assert (target / "bin" / "_agent_common.sh").exists()
    assert not (target / "CODEX.md").exists()
    assert not (target / "CODEX_PYTHON.md").exists()
    assert not (target / "CODEX_CPP.md").exists()
    assert not any(target.rglob("__pycache__"))
    assert not any(target.rglob("*.pyc"))


def _assert_template_only_removed(target: Path) -> None:
    """Generated projects must NOT contain the legacy suffix names or the
    nested templates/ overlay tree.
    """
    assert not (target / "AGENTS_PYTHON.md").exists()
    assert not (target / "AGENTS_CPP.md").exists()
    assert not (target / "CLAUDE_PYTHON.md").exists()
    assert not (target / "CLAUDE_CPP.md").exists()
    assert not (target / "CONTRIBUTING_PYTHON.md").exists()
    assert not (target / "CONTRIBUTING_CPP.md").exists()
    assert not (target / "templates").exists(), (
        "Generated project must not contain the templates/ overlay tree"
    )
    assert not (target / ".claude" / "skills" / "create-project").exists()


def test_e2e_python_project_generation_and_codex_init(template_root):
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_project"
        create_project(template_root, target, "python")

        _assert_common_generated_assets(target, "python")
        _assert_template_only_removed(target)

        assert (target / "AGENTS.md").exists()
        assert (target / "CLAUDE.md").exists()

        audit = run_audit(target, platform="codex")
        assert audit.passed

        result = subprocess.run(
            ["bash", "bin/agent-init", "--platform", "codex"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        assert (target / ".ai" / "session_state.json").exists()

        subprocess.run(
            ["git", "checkout", "-b", "chore/e2e-python"],
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        )
        constraints = subprocess.run(
            ["bash", "bin/agent-check-constraints"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert constraints.returncode == 0, constraints.stdout + "\n" + constraints.stderr


def test_e2e_cpp_project_generation_and_codex_init(template_root):
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_cpp_project"
        create_project(template_root, target, "cpp")

        _assert_common_generated_assets(target, "cpp")
        _assert_template_only_removed(target)

        assert (target / "CMakeLists.txt").exists()

        audit = run_audit(target, platform="codex")
        assert audit.passed

        result = subprocess.run(
            ["bash", "bin/agent-init", "--platform", "codex"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        assert (target / ".ai" / "session_state.json").exists()

        subprocess.run(
            ["git", "checkout", "-b", "chore/e2e-cpp"],
            cwd=target,
            capture_output=True,
            text=True,
            check=True,
        )
        constraints = subprocess.run(
            ["bash", "bin/agent-check-constraints"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert constraints.returncode == 0, constraints.stdout + "\n" + constraints.stderr


def test_e2e_hybrid_project_generation_and_codex_init(template_root):
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_hybrid_project"
        create_project(template_root, target, "hybrid")

        _assert_common_generated_assets(target, "hybrid")
        _assert_template_only_removed(target)

        audit = run_audit(target, platform="codex")
        assert audit.passed

        result = subprocess.run(
            ["bash", "bin/agent-init", "--platform", "codex"],
            cwd=target,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr
        state = json.loads((target / ".ai" / "session_state.json").read_text())
        loaded = set(state["loaded_constraints"])
        assert "hybrid/ffi-boundary" in loaded
        assert "hybrid/python-cpp-build" in loaded
        assert "hybrid/system-deps" in loaded
