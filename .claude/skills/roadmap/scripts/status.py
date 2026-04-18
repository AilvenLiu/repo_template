#!/usr/bin/env python3
"""Display roadmap status with dependency resolution details."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from check_session import check_session_initialized

# Check session initialization
check_session_initialized("roadmap")

from utils import RoadmapManager


def _phase_symbol(status: str) -> str:
    mapping = {
        "active": "[ACTIVE]",
        "completed": "[DONE]",
        "blocked": "[BLOCKED]",
        "pending": "[PENDING]",
    }
    return mapping.get(status, "[UNKNOWN]")


def _task_symbol(status: str) -> str:
    mapping = {
        "active": "[ACTIVE]",
        "completed": "[DONE]",
        "blocked": "[BLOCKED]",
        "pending": "[PENDING]",
    }
    return mapping.get(status, "[UNKNOWN]")


def display_status() -> None:
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    all_phases = manager.find_all_phases()
    if not all_phases:
        print("No phase directories found in agent_roadmaps/")
        print("Use '/roadmap create <name>' to create a new roadmap")
        sys.exit(1)

    print("Phase Series Overview:")
    for phase in all_phases:
        symbol = _phase_symbol(phase["status"])
        deps = phase.get("depends_on_phases", [])
        unresolved = phase.get("unresolved_phase_dependencies", [])
        if deps:
            if unresolved:
                dep_text = f"deps: {', '.join(deps)} (waiting: {', '.join(unresolved)})"
            else:
                dep_text = f"deps: {', '.join(deps)} (satisfied)"
        else:
            dep_text = "deps: none"

        task_summary = f"{phase['tasks_completed']}/{phase['tasks_total']} tasks"
        print(f"  {symbol:<10} {phase['name']}  {task_summary}  {dep_text}")

    print()

    active = [phase for phase in all_phases if phase["status"] == "active"]
    if len(active) > 1:
        print("ERROR: Multiple active phases detected. Resolve roadmap.yml state first.")
        sys.exit(2)

    if not active:
        print("No active phase found.")
        print("Activate one phase after dependencies are satisfied.")
        sys.exit(0)

    active_phase = active[0]
    active_dir = active_phase["roadmap_dir"]
    data = manager.parse_roadmap_yml(active_dir / "roadmap.yml")

    print(f"Active Phase: {active_phase['name']}")
    print(f"Name: {data.get('name', active_phase['display_name'])}")
    print(f"Branch: {active_phase['expected_branch']}")
    print(f"Started: {data.get('status', {}).get('started_at')}")
    print(f"Blocked: {data.get('status', {}).get('blocked')}")

    phase_deps = data.get("depends_on_phases", [])
    if phase_deps:
        unresolved = active_phase.get("unresolved_phase_dependencies", [])
        if unresolved:
            print(f"Phase Dependencies: waiting on {', '.join(unresolved)}")
        else:
            print(f"Phase Dependencies: satisfied ({', '.join(phase_deps)})")
    else:
        print("Phase Dependencies: none")

    current_task = data.get("focus", {}).get("current_task")
    print(f"Current Task: {current_task or 'none'}")
    print()

    completed_ids = {
        task.get("id")
        for task in data.get("tasks", [])
        if isinstance(task, dict) and task.get("status") == "completed"
    }

    print("Tasks:")
    for task in data.get("tasks", []):
        if not isinstance(task, dict):
            continue

        task_id = task.get("id", "unknown")
        status = task.get("status", "pending")
        symbol = _task_symbol(status)
        title = task.get("title", "Untitled")
        effort = task.get("effort", "unknown")
        deps = [dep for dep in task.get("depends_on", []) if isinstance(dep, str)]

        if deps:
            unmet = [dep for dep in deps if dep not in completed_ids]
            dep_state = "ready" if not unmet else f"waiting on {', '.join(unmet)}"
            dep_text = f"deps: {', '.join(deps)} ({dep_state})"
        else:
            dep_text = "deps: none"

        marker = " (CURRENT)" if task_id == current_task else ""
        print(f"  {symbol:<10} {task_id}: {title}{marker}")
        print(f"             effort: {effort} | {dep_text}")

    print()
    total = active_phase["tasks_total"]
    completed = active_phase["tasks_completed"]
    pct = (completed / total * 100.0) if total else 0.0
    print(f"Progress: {completed}/{total} tasks completed ({pct:.1f}%)")


if __name__ == "__main__":
    display_status()
