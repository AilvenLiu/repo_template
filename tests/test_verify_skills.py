#!/usr/bin/env python3
"""Verification tests for the cross-platform repo skill checker."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "create-project" / "scripts"))

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


def _run_verify(project_root: Path, platform: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", ".ai/scripts/common/verify_skills.py", "--platform", platform],
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


def test_verify_skills_fails_when_required_ai_skill_body_is_missing(
    tmp_path: Path,
) -> None:
    target = tmp_path / "python_project"
    create_project(ROOT, target, "python")

    broken = target / ".ai" / "skills" / "build" / "SKILL.md"
    broken.unlink()

    result = _run_verify(target, "codex")

    assert result.returncode != 0
    assert "Missing vendor-neutral skill body" in result.stdout
