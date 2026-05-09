#!/usr/bin/env python3
"""Tests for constraint selection in session init."""

from pathlib import Path
import sys
import tempfile

import yaml

sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))

from project_type import ProjectType
from session_init import find_active_roadmap, resolve_constraints


def test_python_docs_and_tests_constraints_load_precisely() -> None:
    keys = resolve_constraints(
        ProjectType.PYTHON,
        ["README.md", "tests/test_api.py", "src/app.py"],
        has_roadmap=False,
    )

    assert "python/testing" in keys
    assert "python/documentation" in keys
    assert "python/formatting" in keys
    assert "python/type-checking" in keys


def test_cpp_docs_and_cmake_constraints_load_precisely() -> None:
    keys = resolve_constraints(
        ProjectType.CPP,
        ["docs/design.md", "cmake/toolchains/linux.cmake", "src/kernel.cu"],
        has_roadmap=False,
    )

    assert "cpp/documentation" in keys
    assert "cpp/cmake" in keys
    assert "cpp/cuda" in keys


def test_find_active_roadmap_detects_new_schema() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        roadmaps = repo / "agent_roadmaps"
        inactive = roadmaps / "phase-0-base"
        active = roadmaps / "phase-1-next"
        inactive.mkdir(parents=True)
        active.mkdir(parents=True)

        inactive_data = {
            "phase": 0,
            "name": "Base",
            "status": {"active": False, "blocked": False, "started_at": None, "completed_at": None},
            "depends_on_phases": [],
            "tasks": [],
            "focus": {"current_task": None, "notes": ""},
        }
        active_data = {
            "phase": 1,
            "name": "Next",
            "status": {"active": True, "blocked": False, "started_at": "2026-04-17", "completed_at": None},
            "depends_on_phases": ["phase-0-base"],
            "tasks": [],
            "focus": {"current_task": None, "notes": ""},
        }

        (inactive / "roadmap.yml").write_text(yaml.safe_dump(inactive_data, sort_keys=False), encoding="utf-8")
        (active / "roadmap.yml").write_text(yaml.safe_dump(active_data, sort_keys=False), encoding="utf-8")

        detected = find_active_roadmap(repo)
        assert detected is not None
        assert detected.name == "phase-1-next"
