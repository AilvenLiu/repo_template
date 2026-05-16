#!/usr/bin/env python3
"""Display roadmap status with dependency resolution details."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from check_session import check_session_initialized

# Check session initialization
check_session_initialized("roadmap")

from utils import RoadmapManager  # noqa: E402


def _step_symbol(status: str) -> str:
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

    all_steps = manager.find_all_steps()
    if not all_steps:
        print("No step directories found in agent_roadmaps/")
        print("Use '/roadmap create <name>' to create a new roadmap")
        sys.exit(1)

    print("Step Series Overview:")
    for step in all_steps:
        symbol = _step_symbol(step["status"])
        deps = step.get("depends_on_steps", [])
        unresolved = step.get("unresolved_step_dependencies", [])
        if deps:
            if unresolved:
                dep_text = f"deps: {', '.join(deps)} (waiting: {', '.join(unresolved)})"
            else:
                dep_text = f"deps: {', '.join(deps)} (satisfied)"
        else:
            dep_text = "deps: none"

        task_summary = f"{step['tasks_completed']}/{step['tasks_total']} tasks"
        print(f"  {symbol:<10} {step['name']}  {task_summary}  {dep_text}")

    print()

    active = [step for step in all_steps if step["status"] == "active"]
    if len(active) > 1:
        print("ERROR: Multiple active steps detected. Resolve roadmap.yml state first.")
        sys.exit(2)

    if not active:
        print("No active step found.")
        print("Activate one step after dependencies are satisfied.")
        sys.exit(0)

    active_step = active[0]
    active_dir = active_step["roadmap_dir"]
    data = manager.parse_roadmap_yml(active_dir / "roadmap.yml")

    print(f"Active Step: {active_step['name']}")
    print(f"Name: {data.get('name', active_step['display_name'])}")
    print(f"Branch: {active_step['expected_branch']}")
    print(f"Started: {data.get('status', {}).get('started_at')}")
    print(f"Blocked: {data.get('status', {}).get('blocked')}")

    step_deps = data.get("depends_on_steps", [])
    if step_deps:
        unresolved = active_step.get("unresolved_step_dependencies", [])
        if unresolved:
            print(f"Step Dependencies: waiting on {', '.join(unresolved)}")
        else:
            print(f"Step Dependencies: satisfied ({', '.join(step_deps)})")
    else:
        print("Step Dependencies: none")

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
    total = active_step["tasks_total"]
    completed = active_step["tasks_completed"]
    pct = (completed / total * 100.0) if total else 0.0
    print(f"Progress: {completed}/{total} tasks completed ({pct:.1f}%)")


if __name__ == "__main__":
    display_status()
