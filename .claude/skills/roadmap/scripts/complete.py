#!/usr/bin/env python3
"""Mark roadmap as completed and deactivate."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def complete_roadmap() -> None:
    """Mark roadmap as completed and deactivate."""
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Find active roadmap
    active = manager.find_active_roadmap()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)

    roadmap_dir = active["roadmap_dir"]
    roadmap_yml = roadmap_dir / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    # Verify all phases and tasks are completed
    phases = data.get("phases", [])
    incomplete_items = []

    for phase in phases:
        phase_id = phase.get("id")
        phase_status = phase.get("status", "pending")

        if phase_status != "completed":
            incomplete_items.append(f"Phase {phase_id} is {phase_status}")

        tasks = phase.get("tasks", [])
        for task in tasks:
            task_id = task.get("id")
            task_status = task.get("status", "pending")

            if task_status != "completed":
                incomplete_items.append(f"Task {phase_id}/{task_id} is {task_status}")

    if incomplete_items:
        print("ERROR: Cannot complete roadmap - incomplete items found:")
        for item in incomplete_items:
            print(f"  - {item}")
        print()
        print("Use '/roadmap update complete-task' to complete tasks")
        sys.exit(1)

    # Mark roadmap as completed
    updates = {
        "status": {
            "active": False,
            "blocked": False,
            "completed": True,
        },
        "current_focus": {},
    }

    manager.update_roadmap_yml(roadmap_yml, updates)

    # Generate completion summary
    total_phases = len(phases)
    total_tasks = sum(len(phase.get("tasks", [])) for phase in phases)

    print("Roadmap Completed!")
    print("=" * 50)
    print(f"Roadmap: {active['name']}")
    print(f"Total Phases: {total_phases}")
    print(f"Total Tasks: {total_tasks}")
    print()
    print("The roadmap has been marked as completed and deactivated.")
    print("You can now create a new roadmap if needed.")


def main():
    """Main entry point for complete command."""
    complete_roadmap()


if __name__ == "__main__":
    main()
