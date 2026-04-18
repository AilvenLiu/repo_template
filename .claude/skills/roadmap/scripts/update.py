#!/usr/bin/env python3
"""Update dependency-aware roadmap state."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from check_session import check_session_initialized

from utils import RoadmapManager


def _get_single_active_phase(manager: RoadmapManager) -> Dict[str, object]:
    active = manager.find_active_roadmaps()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)
    if len(active) > 1:
        print("ERROR: Multiple active phases found")
        for phase in active:
            print(f"  - {phase['name']}")
        print("Fix roadmap.yml so exactly one phase has status.active: true")
        sys.exit(2)
    return active[0]


def _find_task(tasks: List[Dict[str, object]], task_id: str) -> Optional[Dict[str, object]]:
    for task in tasks:
        if isinstance(task, dict) and task.get("id") == task_id:
            return task
    return None


def _completed_task_ids(tasks: List[Dict[str, object]]) -> set:
    return {
        task.get("id")
        for task in tasks
        if isinstance(task, dict) and task.get("status") == "completed"
    }


def _dependencies_satisfied(task: Dict[str, object], completed_ids: set) -> bool:
    deps = task.get("depends_on", [])
    if not isinstance(deps, list):
        return False
    for dep in deps:
        if isinstance(dep, str) and dep not in completed_ids:
            return False
    return True


def _clear_other_active_tasks(tasks: List[Dict[str, object]], keep_task_id: Optional[str]) -> None:
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("status") == "active" and task.get("id") != keep_task_id:
            task["status"] = "pending"


def complete_task(manager: RoadmapManager, roadmap_dir: Path) -> None:
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list) or not tasks:
        print("ERROR: roadmap.yml has no tasks")
        sys.exit(1)

    current_task_id = data.get("focus", {}).get("current_task")
    if not isinstance(current_task_id, str):
        current_task_id = manager.get_active_task_id(data)

    if not isinstance(current_task_id, str):
        print("ERROR: No current task set in focus.current_task and no active task found")
        sys.exit(1)

    current_task = _find_task(tasks, current_task_id)
    if current_task is None:
        print(f"ERROR: Current task '{current_task_id}' not found in tasks")
        sys.exit(1)

    if current_task.get("status") not in {"active", "blocked"}:
        print(
            f"ERROR: Current task '{current_task_id}' has status '{current_task.get('status')}'. "
            "Use set-focus to activate a pending task first."
        )
        sys.exit(1)

    current_task["status"] = "completed"
    data["status"]["blocked"] = False

    completed_ids = _completed_task_ids(tasks)

    ready_pending: List[Dict[str, object]] = []
    remaining_non_completed: List[Dict[str, object]] = []
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = task.get("status")
        if status != "completed":
            remaining_non_completed.append(task)
        if status == "pending" and _dependencies_satisfied(task, completed_ids):
            ready_pending.append(task)

    if ready_pending:
        next_task = ready_pending[0]
        next_task_id = next_task.get("id")
        _clear_other_active_tasks(tasks, next_task_id if isinstance(next_task_id, str) else None)
        next_task["status"] = "active"
        data["focus"]["current_task"] = next_task_id
        data["status"]["active"] = True
        data["status"]["blocked"] = False
        data["status"]["completed_at"] = None

        manager.update_roadmap_yml(roadmap_yml, data)
        print(f"Task {current_task_id} completed")
        print(f"Advanced to next ready task: {next_task_id} - {next_task.get('title')}")
        return

    unfinished = [task for task in remaining_non_completed if task.get("status") != "completed"]
    if unfinished:
        _clear_other_active_tasks(tasks, None)
        data["focus"]["current_task"] = None
        data["status"]["active"] = True
        data["status"]["blocked"] = True
        data["status"]["completed_at"] = None

        blocked_tasks = [
            task for task in unfinished if task.get("status") in {"pending", "blocked"}
        ]

        manager.update_roadmap_yml(roadmap_yml, data)
        print(f"Task {current_task_id} completed")
        print("Phase now blocked: no ready task found.")
        if blocked_tasks:
            print("Unfinished tasks:")
            for task in blocked_tasks:
                task_id = task.get("id", "unknown")
                status = task.get("status", "unknown")
                deps = task.get("depends_on", [])
                print(f"  - {task_id} ({status}) depends_on={deps}")
        print("Use '/roadmap update set-focus <task-id>' only after dependencies are satisfied.")
        return

    _clear_other_active_tasks(tasks, None)
    data["focus"]["current_task"] = None
    data["status"]["active"] = False
    data["status"]["blocked"] = False
    data["status"]["completed_at"] = date.today().isoformat()

    manager.update_roadmap_yml(roadmap_yml, data)

    phase_folder = roadmap_dir.name
    phase_branch = RoadmapManager.derive_branch_name(phase_folder)
    print(f"Task {current_task_id} completed")
    print(f"Phase {phase_folder} completed")
    print()
    print("Next steps:")
    print(f"1. Create PR/MR from {phase_branch} to base branch")
    print("2. After merge, switch to base branch and pull latest")
    print("3. Activate a dependency-ready next phase")


def block_task(manager: RoadmapManager, roadmap_dir: Path, reason: str) -> None:
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list):
        print("ERROR: Invalid tasks section")
        sys.exit(1)

    task_id = data.get("focus", {}).get("current_task")
    if not isinstance(task_id, str):
        task_id = manager.get_active_task_id(data)

    if not isinstance(task_id, str):
        print("ERROR: No current task to block")
        sys.exit(1)

    task = _find_task(tasks, task_id)
    if task is None:
        print(f"ERROR: Task '{task_id}' not found")
        sys.exit(1)

    task["status"] = "blocked"
    task["notes"] = reason

    data["status"]["blocked"] = True
    data["status"]["active"] = True
    data["focus"]["current_task"] = None

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Task {task_id} marked as blocked")
    print(f"Reason: {reason}")


def unblock_task(manager: RoadmapManager, roadmap_dir: Path) -> None:
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list):
        print("ERROR: Invalid tasks section")
        sys.exit(1)

    completed_ids = _completed_task_ids(tasks)

    candidate: Optional[Dict[str, object]] = None
    focus_task = data.get("focus", {}).get("current_task")
    if isinstance(focus_task, str):
        task = _find_task(tasks, focus_task)
        if task and task.get("status") == "blocked" and _dependencies_satisfied(task, completed_ids):
            candidate = task

    if candidate is None:
        for task in tasks:
            if not isinstance(task, dict):
                continue
            if task.get("status") == "blocked" and _dependencies_satisfied(task, completed_ids):
                candidate = task
                break

    if candidate is None:
        print("ERROR: No blocked task can be unblocked (dependencies still unmet)")
        sys.exit(1)

    candidate_id = candidate.get("id")
    _clear_other_active_tasks(tasks, candidate_id if isinstance(candidate_id, str) else None)
    candidate["status"] = "active"

    data["status"]["blocked"] = False
    data["status"]["active"] = True
    data["focus"]["current_task"] = candidate_id

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Task {candidate_id} unblocked and activated")


def set_focus(manager: RoadmapManager, roadmap_dir: Path, task_id: str) -> None:
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)
    tasks = data.get("tasks", [])

    if not isinstance(tasks, list):
        print("ERROR: Invalid tasks section")
        sys.exit(1)

    target = _find_task(tasks, task_id)
    if target is None:
        print(f"ERROR: Task '{task_id}' not found")
        sys.exit(1)

    if target.get("status") == "completed":
        print(f"ERROR: Task '{task_id}' is already completed")
        sys.exit(1)

    completed_ids = _completed_task_ids(tasks)
    if not _dependencies_satisfied(target, completed_ids):
        unmet = [
            dep
            for dep in target.get("depends_on", [])
            if isinstance(dep, str) and dep not in completed_ids
        ]
        print(f"ERROR: Task '{task_id}' has unmet dependencies: {', '.join(unmet)}")
        sys.exit(1)

    _clear_other_active_tasks(tasks, task_id)
    target["status"] = "active"

    data["focus"]["current_task"] = task_id
    data["status"]["active"] = True
    data["status"]["blocked"] = False

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Focus changed to task {task_id}")


def main() -> None:
    check_session_initialized("roadmap")

    if len(sys.argv) < 2:
        print("Usage: update.py <action> [args]")
        print("Actions:")
        print("  complete-task          - Mark current task completed and advance by dependencies")
        print("  block-task <reason>    - Mark current task blocked")
        print("  unblock-task           - Unblock first dependency-ready blocked task")
        print("  set-focus <task-id>    - Focus a dependency-ready task")
        sys.exit(1)

    action = sys.argv[1]
    manager = RoadmapManager(Path.cwd())
    active = _get_single_active_phase(manager)
    roadmap_dir = active["roadmap_dir"]

    if action == "complete-task":
        complete_task(manager, roadmap_dir)
    elif action == "block-task":
        if len(sys.argv) < 3:
            print("ERROR: block-task requires a reason")
            sys.exit(1)
        reason = " ".join(sys.argv[2:])
        block_task(manager, roadmap_dir, reason)
    elif action == "unblock-task":
        unblock_task(manager, roadmap_dir)
    elif action == "set-focus":
        if len(sys.argv) < 3:
            print("ERROR: set-focus requires <task-id>")
            sys.exit(1)
        set_focus(manager, roadmap_dir, sys.argv[2])
    else:
        print(f"ERROR: Unknown action '{action}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
