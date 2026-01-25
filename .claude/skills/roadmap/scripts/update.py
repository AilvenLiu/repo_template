#!/usr/bin/env python3
"""Update roadmap state (task completion, phase transitions)."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def complete_task(manager: RoadmapManager, roadmap_dir: Path) -> None:
    """Mark current task as completed and advance to next."""
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    current_focus = data.get("current_focus", {})
    current_phase_id = current_focus.get("phase")
    current_task_id = current_focus.get("task")

    if not current_phase_id or not current_task_id:
        print("ERROR: No current task set in roadmap.yml")
        sys.exit(1)

    # Find current phase and task
    phases = data.get("phases", [])
    current_phase_idx = None
    current_task_idx = None

    for phase_idx, phase in enumerate(phases):
        if phase.get("id") == current_phase_id:
            current_phase_idx = phase_idx
            tasks = phase.get("tasks", [])
            for task_idx, task in enumerate(tasks):
                if task.get("id") == current_task_id:
                    current_task_idx = task_idx
                    break
            break

    if current_phase_idx is None or current_task_idx is None:
        print(f"ERROR: Current task {current_phase_id}/{current_task_id} not found")
        sys.exit(1)

    # Mark current task as completed
    phases[current_phase_idx]["tasks"][current_task_idx]["status"] = "completed"

    # Find next task
    next_task_idx = current_task_idx + 1
    tasks = phases[current_phase_idx].get("tasks", [])

    if next_task_idx < len(tasks):
        # Next task in same phase
        next_task = tasks[next_task_idx]
        next_task["status"] = "active"
        data["current_focus"] = {
            "phase": current_phase_id,
            "task": next_task.get("id"),
        }
        print(f"Task {current_task_id} completed")
        print(f"Advanced to next task: {next_task.get('id')} - {next_task.get('title')}")
    else:
        # Phase completed, check for next phase
        phases[current_phase_idx]["status"] = "completed"
        next_phase_idx = current_phase_idx + 1

        if next_phase_idx < len(phases):
            # Advance to next phase
            next_phase = phases[next_phase_idx]
            next_phase["status"] = "active"
            next_phase_tasks = next_phase.get("tasks", [])
            if next_phase_tasks:
                next_phase_tasks[0]["status"] = "active"
                data["current_focus"] = {
                    "phase": next_phase.get("id"),
                    "task": next_phase_tasks[0].get("id"),
                }
                print(f"Task {current_task_id} completed")
                print(f"Phase {current_phase_id} completed")
                print(f"Advanced to next phase: {next_phase.get('id')} - {next_phase.get('title')}")
            else:
                print(f"ERROR: Next phase {next_phase.get('id')} has no tasks")
                sys.exit(1)
        else:
            # All phases completed
            data["status"]["completed"] = True
            data["status"]["active"] = False
            data["current_focus"] = {}
            print(f"Task {current_task_id} completed")
            print(f"Phase {current_phase_id} completed")
            print("All phases completed! Roadmap is now complete.")

    # Update roadmap.yml
    manager.update_roadmap_yml(roadmap_yml, data)


def block_task(manager: RoadmapManager, roadmap_dir: Path, reason: str) -> None:
    """Mark current task as blocked with reason."""
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    current_focus = data.get("current_focus", {})
    current_phase_id = current_focus.get("phase")
    current_task_id = current_focus.get("task")

    if not current_phase_id or not current_task_id:
        print("ERROR: No current task set in roadmap.yml")
        sys.exit(1)

    # Find and update current task
    for phase in data.get("phases", []):
        if phase.get("id") == current_phase_id:
            for task in phase.get("tasks", []):
                if task.get("id") == current_task_id:
                    task["status"] = "blocked"
                    task["notes"] = reason
                    break
            break

    # Mark roadmap as blocked
    data["status"]["blocked"] = True

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Task {current_task_id} marked as blocked")
    print(f"Reason: {reason}")


def unblock_task(manager: RoadmapManager, roadmap_dir: Path) -> None:
    """Remove blocked status from current task."""
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    current_focus = data.get("current_focus", {})
    current_phase_id = current_focus.get("phase")
    current_task_id = current_focus.get("task")

    if not current_phase_id or not current_task_id:
        print("ERROR: No current task set in roadmap.yml")
        sys.exit(1)

    # Find and update current task
    for phase in data.get("phases", []):
        if phase.get("id") == current_phase_id:
            for task in phase.get("tasks", []):
                if task.get("id") == current_task_id:
                    task["status"] = "active"
                    break
            break

    # Unblock roadmap
    data["status"]["blocked"] = False

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Task {current_task_id} unblocked")


def set_focus(manager: RoadmapManager, roadmap_dir: Path, phase_id: str, task_id: str) -> None:
    """Manually change focus to specified phase and task."""
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    # Validate phase and task exist
    phases = data.get("phases", [])
    phase_found = False
    task_found = False

    for phase in phases:
        if phase.get("id") == phase_id:
            phase_found = True
            for task in phase.get("tasks", []):
                if task.get("id") == task_id:
                    task_found = True
                    break
            break

    if not phase_found:
        print(f"ERROR: Phase '{phase_id}' not found")
        sys.exit(1)

    if not task_found:
        print(f"ERROR: Task '{task_id}' not found in phase '{phase_id}'")
        sys.exit(1)

    # Update focus
    data["current_focus"] = {
        "phase": phase_id,
        "task": task_id,
    }

    manager.update_roadmap_yml(roadmap_yml, data)
    print(f"Focus changed to {phase_id}/{task_id}")


def main():
    """Main entry point for update command."""
    if len(sys.argv) < 2:
        print("Usage: update.py <action> [args]")
        print("Actions:")
        print("  complete-task          - Mark current task as completed, advance to next")
        print("  block-task <reason>    - Mark current task as blocked")
        print("  unblock-task           - Remove blocked status")
        print("  set-focus <phase> <task> - Manually change focus")
        sys.exit(1)

    action = sys.argv[1]

    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Find active roadmap
    active = manager.find_active_roadmap()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)

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
        if len(sys.argv) < 4:
            print("ERROR: set-focus requires <phase> <task>")
            sys.exit(1)
        phase_id = sys.argv[2]
        task_id = sys.argv[3]
        set_focus(manager, roadmap_dir, phase_id, task_id)
    else:
        print(f"ERROR: Unknown action '{action}'")
        sys.exit(1)


if __name__ == "__main__":
    main()
