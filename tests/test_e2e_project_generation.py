#!/usr/bin/env python3
"""End-to-end tests for project generation and Codex parity assets."""

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Add import roots
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "tools"))
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create-project" / "scripts"))

from capability_audit import run_audit
from init import create_project


@pytest.fixture
def template_root():
    return Path(__file__).parent.parent


def _assert_common_generated_assets(target: Path, project_type: str) -> None:
    codex_skill_dirs = {path.name for path in (target / ".codex" / "skills").iterdir() if path.is_dir()}

    assert (target / ".ai" / "capabilities.yml").exists()
    assert (target / ".ai" / "constraints" / "common" / "karpathy-guidelines.md").exists()
    assert (target / ".ai" / "project.yml").exists()
    assert (target / ".ai" / "tools" / "session_init.py").exists()
    assert (target / ".claude" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
    assert (target / ".codex" / "skills" / "build" / "SKILL.md").exists()
    assert (target / ".codex" / "skills" / "init" / "SKILL.md").exists()
    assert (target / ".codex" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
    assert (target / ".codex" / "skills" / "navigate" / "SKILL.md").exists()
    assert (target / "bin" / "agent-build").exists()
    expected_codex_skills = {
        "build",
        "check-constraints",
        "context7",
        "dependency",
        "init",
        "karpathy-guidelines",
        "navigate",
        "pre-commit",
        "roadmap",
    }
    if project_type == "python":
        assert (target / ".claude" / "skills" / "python-env-setup" / "SKILL.md").exists()
        expected_codex_skills.add("python-env-setup")
        assert (target / ".codex" / "skills" / "python-env-setup" / "SKILL.md").exists()
        assert (target / "bin" / "agent-python-env-setup").exists()
    else:
        assert not (target / ".claude" / "skills" / "python-env-setup").exists()
        assert not (target / ".claude" / "docs" / "python-env-quick-reference.md").exists()
        assert not (target / ".codex" / "skills" / "python-env-setup").exists()
        assert not (target / "bin" / "agent-python-env-setup").exists()
    assert codex_skill_dirs == expected_codex_skills
    assert (target / "bin" / "agent-init").exists()
    assert (target / "bin" / "agent-precommit").exists()
    assert (target / "bin" / "agent-check-constraints").exists()
    assert (target / "bin" / "_agent_common.sh").exists()
    assert (target / "CODEX.md").exists()
    assert not any(target.rglob("__pycache__"))
    assert not any(target.rglob("*.pyc"))


def _assert_template_only_removed(target: Path) -> None:
    assert not (target / "AGENTS_PYTHON.md").exists()
    assert not (target / "AGENTS_CPP.md").exists()
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
