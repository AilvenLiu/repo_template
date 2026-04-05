#!/usr/bin/env python3
"""Mark active phase as completed and emit branch transition instructions."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def complete_roadmap() -> None:
    """Mark the active phase as completed and print branch transition instructions."""
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Find active roadmap (active phase)
    active = manager.find_active_roadmap()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)

    roadmap_dir = active["roadmap_dir"]
    phase_folder = roadmap_dir.name
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    # Verify all tasks in the active phase are completed
    phases = data.get("phases", [])
    incomplete_items = []

    for phase in phases:
        phase_id = phase.get("id")
        tasks = phase.get("tasks", [])
        for task in tasks:
            task_id = task.get("id")
            task_status = task.get("status", "pending")
            if task_status != "completed":
                incomplete_items.append(f"Task {phase_id}/{task_id} is {task_status}")

    if incomplete_items:
        print("ERROR: Cannot complete phase - incomplete tasks found:")
        for item in incomplete_items:
            print(f"  - {item}")
        print()
        print("Use '/roadmap update complete-task' to complete tasks")
        sys.exit(1)

    # Mark phase as completed
    updates = {
        "status": {
            "active": False,
            "blocked": False,
            "completed": True,
        },
        "current_focus": {},
    }

    manager.update_roadmap_yml(roadmap_yml, updates)

    # Generate completion summary and branch transition instructions
    total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)
    current_branch = RoadmapManager.derive_branch_name(phase_folder)

    print("Phase Completed!")
    print("=" * 50)
    print(f"Phase: {phase_folder}")
    print(f"Total Tasks: {total_tasks}")
    print()
    print(f"Phase {phase_folder} completed!")
    print()
    print("Next steps:")
    print(f"1. Create PR/MR from {current_branch} to base branch")
    print("2. After merge, switch to base branch and pull latest")
    print("3. Activate next phase: set status.active: true in next phase's roadmap.yml")
    print("4. Create branch: git checkout -b roadmap/<next-phase-folder>")


def main():
    """Main entry point for complete command."""
    complete_roadmap()


if __name__ == "__main__":
    main()
