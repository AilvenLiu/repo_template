#!/usr/bin/env python3
"""Tests for roadmap-phase residue detection in forbidden_patterns."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))

from forbidden_patterns import scan  # type: ignore[import-not-found]  # noqa: E402
from project_type import ProjectType  # type: ignore[import-not-found]  # noqa: E402


def test_detects_roadmap_phase_label_outside_agent_roadmaps(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "Current branch: roadmap/phase-2-rollout\n", encoding="utf-8"
    )
    findings = scan(tmp_path, ProjectType.PYTHON)
    categories = {finding.category for finding in findings}
    assert "roadmap-phase-label" in categories


def test_detects_bare_numbered_phase_label_outside_agent_roadmaps(
    tmp_path: Path,
) -> None:
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "ARCHITECTURE.md").write_text(
        "The continuous loop lives in loop/ (phase-10).\n", encoding="utf-8"
    )
    findings = scan(tmp_path, ProjectType.PYTHON)
    categories = {finding.category for finding in findings}
    assert "roadmap-phase-label" in categories


def test_ignores_temporary_roadmap_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "agent_roadmaps" / "phase-0-baseline"
    workspace.mkdir(parents=True)
    (workspace / "ROADMAP.md").write_text("roadmap/phase-0-baseline\n", encoding="utf-8")
    findings = scan(tmp_path, ProjectType.PYTHON)
    categories = {finding.category for finding in findings}
    assert "roadmap-phase-label" not in categories
