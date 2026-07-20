#!/usr/bin/env python3
"""Verification tests for the cross-platform repo skill checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "create-project" / "scripts"))

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


def _run_verify(project_root: Path, platform: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", ".agents/scripts/common/verify_skills.py", "--platform", platform],
        cwd=project_root,
        capture_output=True,
        text=True,
    )


def test_verify_skills_passes_for_generated_hybrid_project(tmp_path: Path) -> None:
    target = tmp_path / "hybrid_project"
    create_project(ROOT, target, "hybrid")

    result = _run_verify(target, "both")

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "Verification passed." in result.stdout


def test_verify_skills_respects_cpp_skill_filtering(tmp_path: Path) -> None:
    target = tmp_path / "cpp_project"
    create_project(ROOT, target, "cpp")

    result = _run_verify(target, "both")

    assert result.returncode == 0, result.stdout + "\n" + result.stderr
    assert "python-env-setup" not in result.stdout


def test_verify_skills_fails_when_required_agents_skill_body_is_missing(
    tmp_path: Path,
) -> None:
    target = tmp_path / "python_project"
    create_project(ROOT, target, "python")

    broken = target / ".agents" / "skills" / "build" / "SKILL.md"
    broken.unlink()

    result = _run_verify(target, "codex")

    assert result.returncode != 0
    assert "Missing canonical skill body" in result.stdout


def test_verify_skills_fails_when_canonical_frontmatter_is_missing(
    tmp_path: Path,
) -> None:
    target = tmp_path / "python_project"
    create_project(ROOT, target, "python")

    broken = target / ".agents" / "skills" / "build" / "SKILL.md"
    content = broken.read_text()
    broken.write_text(content.split("---", 2)[-1].lstrip())

    result = _run_verify(target, "codex")

    assert result.returncode != 0
    assert "Invalid canonical skill" in result.stdout
    assert "missing YAML frontmatter" in result.stdout


def test_verify_skills_fails_when_claude_stub_does_not_delegate(
    tmp_path: Path,
) -> None:
    target = tmp_path / "python_project"
    create_project(ROOT, target, "python")

    broken = target / ".claude" / "skills" / "build" / "SKILL.md"
    broken.write_text(
        broken.read_text().replace(".agents/skills/build/SKILL.md", "elsewhere.md")
    )

    result = _run_verify(target, "claude")

    assert result.returncode != 0
    assert "does not delegate" in result.stdout


def test_verify_skills_fails_when_entrypoint_omits_required_skill(
    tmp_path: Path,
) -> None:
    target = tmp_path / "python_project"
    create_project(ROOT, target, "python")
    agents = target / "AGENTS.md"
    agents.write_text(agents.read_text().replace("navigate", "code-search"))

    result = _run_verify(target, "codex")

    assert result.returncode != 0
    assert "AGENTS.md does not expose required skill: navigate" in result.stdout
