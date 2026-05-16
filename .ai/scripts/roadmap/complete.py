#!/usr/bin/env python3
"""Mark active step as completed and print dependency-safe next steps."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from check_session import check_session_initialized

from utils import RoadmapManager


def complete_roadmap() -> None:
    check_session_initialized("roadmap")

    manager = RoadmapManager(Path.cwd())
    active_steps = manager.find_active_roadmaps()

    if not active_steps:
        print("ERROR: No active roadmap found")
        sys.exit(1)

    if len(active_steps) > 1:
        print("ERROR: Multiple active steps found")
        for step in active_steps:
            print(f"  - {step['name']}")
        print("Fix roadmap.yml so only one step has status.active: true")
        sys.exit(2)

    active = active_steps[0]
    roadmap_dir = active["roadmap_dir"]
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    tasks = data.get("tasks", [])
    if not isinstance(tasks, list):
        print("ERROR: Invalid tasks section in roadmap.yml")
        sys.exit(1)

    incomplete = [
        f"{task.get('id', 'unknown')} ({task.get('status', 'unknown')})"
        for task in tasks
        if isinstance(task, dict) and task.get("status") != "completed"
    ]

    if incomplete:
        print("ERROR: Cannot complete step because not all tasks are completed:")
        for item in incomplete:
            print(f"  - {item}")
        print()
        print("Use '/roadmap update complete-task' until all tasks are completed.")
        sys.exit(1)

    data["status"]["active"] = False
    data["status"]["blocked"] = False
    data["status"]["completed_at"] = date.today().isoformat()
    data["focus"]["current_task"] = None

    manager.update_roadmap_yml(roadmap_yml, data)

    # Recompute step list to identify dependency-ready next steps.
    all_steps = manager.find_all_steps()
    ready_next = [
        step
        for step in all_steps
        if step["status"] == "pending" and step.get("ready", False)
    ]

    step_folder = roadmap_dir.name
    branch = RoadmapManager.derive_branch_name(step_folder)

    if manager.all_roadmaps_completed():
        manager.restore_placeholder_workspace()
        print("Roadmap Completed")
        print("=" * 50)
        print(f"Final step folder: {step_folder}")
        print(f"Branch: {branch}")
        print(f"Tasks completed: {len(tasks)}/{len(tasks)}")
        print()
        print("Temporary roadmap workspace deleted and placeholder README restored.")
        print("Next steps:")
        print(f"1. Create PR/MR from {branch} into the base branch")
        print("2. Merge the PR/MR")
        print("3. Continue from the base branch without roadmap-specific files")
        return

    print("Step Completed")
    print("=" * 50)
    print(f"Step folder: {step_folder}")
    print(f"Branch: {branch}")
    print(f"Tasks completed: {len(tasks)}/{len(tasks)}")
    print()
    print("Next steps:")
    print(f"1. Create PR/MR from {branch} into the base branch")
    print("2. Merge the PR/MR")
    print("3. Switch to base branch and pull latest")
    if ready_next:
        print("4. Activate one dependency-ready next step:")
        for step in ready_next:
            print(f"   - {step['name']}")
    else:
        print("4. No dependency-ready pending step found (check depends_on_steps)")


if __name__ == "__main__":
    complete_roadmap()
