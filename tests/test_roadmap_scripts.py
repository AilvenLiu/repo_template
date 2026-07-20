#!/usr/bin/env python3
"""Tests for dependency-aware roadmap script behavior."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest
import yaml  # type: ignore[import-untyped]

SCRIPTS_DIR = Path(__file__).parent.parent / ".agents" / "scripts" / "roadmap"
sys.path.insert(0, str(SCRIPTS_DIR))
sys.path.insert(0, str(Path(__file__).parent.parent / ".agents" / "scripts" / "common"))


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


roadmap_utils = _load_module("roadmap_scripts_utils", SCRIPTS_DIR / "utils.py")
sys.modules["utils"] = roadmap_utils
update_module = _load_module("roadmap_scripts_update", SCRIPTS_DIR / "update.py")

complete_task = update_module.complete_task
set_focus = update_module.set_focus
RoadmapManager = roadmap_utils.RoadmapManager


def _write_roadmap(path: Path, *, active: bool = True) -> None:
    data = {
        "phase": 0,
        "name": "Alpha",
        "status": {
            "active": active,
            "blocked": False,
            "started_at": "2026-04-17" if active else None,
            "completed_at": None,
        },
        "depends_on_phases": [],
        "tasks": [
            {
                "id": "task-0-1",
                "title": "Initial setup",
                "description": "Prepare baseline configuration.",
                "status": "active" if active else "completed",
                "effort": "low",
                "key_files": ["src/setup.py"],
                "depends_on": [],
            },
            {
                "id": "task-0-2",
                "title": "Final integration",
                "description": "Integrate final output after dependency chain.",
                "status": "pending",
                "effort": "medium",
                "key_files": ["src/integration.py"],
                "depends_on": ["task-0-4"],
            },
            {
                "id": "task-0-3",
                "title": "Core implementation",
                "description": "Implement core behavior after setup.",
                "status": "pending",
                "effort": "medium",
                "key_files": ["src/core.py"],
                "depends_on": ["task-0-1"],
            },
            {
                "id": "task-0-4",
                "title": "Validation stage",
                "description": "Validate outputs before integration.",
                "status": "pending",
                "effort": "low",
                "key_files": ["tests/test_core.py"],
                "depends_on": ["task-0-3"],
            },
        ],
        "focus": {
            "current_task": "task-0-1" if active else None,
            "notes": "Test fixture",
        },
    }
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def _load(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_complete_task_advances_to_dependency_ready_task(tmp_path: Path) -> None:
    repo = tmp_path
    step_dir = repo / "agent_roadmaps" / "phase-0-alpha"
    step_dir.mkdir(parents=True)
    roadmap_file = step_dir / "roadmap.yml"
    _write_roadmap(roadmap_file, active=True)

    manager = RoadmapManager(repo)
    complete_task(manager, step_dir)

    updated = _load(roadmap_file)
    tasks = {task["id"]: task for task in updated["tasks"]}

    assert tasks["task-0-1"]["status"] == "completed"
    assert tasks["task-0-3"]["status"] == "active"
    assert updated["focus"]["current_task"] == "task-0-3"


def test_set_focus_rejects_unmet_dependencies(tmp_path: Path) -> None:
    repo = tmp_path
    step_dir = repo / "agent_roadmaps" / "phase-0-alpha"
    step_dir.mkdir(parents=True)
    roadmap_file = step_dir / "roadmap.yml"
    _write_roadmap(roadmap_file, active=True)

    manager = RoadmapManager(repo)

    with pytest.raises(SystemExit):
        set_focus(manager, step_dir, "task-0-2")

    updated = _load(roadmap_file)
    assert updated["focus"]["current_task"] == "task-0-1"


def test_phase_dependency_readiness_is_reported(tmp_path: Path) -> None:
    repo = tmp_path

    phase0_dir = repo / "agent_roadmaps" / "phase-0-base"
    phase0_dir.mkdir(parents=True)
    _write_roadmap(phase0_dir / "roadmap.yml", active=False)

    phase1_dir = repo / "agent_roadmaps" / "phase-1-followup"
    phase1_dir.mkdir(parents=True)

    followup = _load(phase0_dir / "roadmap.yml")
    followup["phase"] = 1
    followup["name"] = "Followup"
    followup["status"] = {
        "active": True,
        "blocked": False,
        "started_at": "2026-04-17",
        "completed_at": None,
    }
    followup["depends_on_phases"] = ["phase-0-base"]
    followup["tasks"][0]["status"] = "active"
    followup["focus"]["current_task"] = "task-0-1"
    (phase1_dir / "roadmap.yml").write_text(
        yaml.safe_dump(followup, sort_keys=False), encoding="utf-8"
    )

    manager = RoadmapManager(repo)
    phases = manager.find_all_phases()
    phase1 = next(item for item in phases if item["name"] == "phase-1-followup")

    assert phase1["ready"] is False
    assert phase1["unresolved_phase_dependencies"] == ["phase-0-base"]
