#!/usr/bin/env python3
"""Display detailed status of active roadmap."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'common'))
from check_session import check_session_initialized

# Check session initialization
session_state = check_session_initialized('roadmap')

from utils import RoadmapManager


def display_status() -> None:
    """Display cross-phase overview and detailed status of active phase."""
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Get all phases for the overview
    all_phases = manager.find_all_phases()
    if not all_phases:
        print("No phase directories found in agent_roadmaps/")
        print("Use '/roadmap create <name>' to create a new roadmap")
        sys.exit(1)

    # Find the active phase
    active = manager.find_active_roadmap()

    # Display cross-phase overview
    print("Phase Series Overview:")
    for phase in all_phases:
        phase_status = phase["status"]
        phase_name = phase["name"]

        # Count tasks for this phase
        roadmap_yml = phase["roadmap_dir"] / "roadmap.yml"
        try:
            data = manager.parse_roadmap_yml(roadmap_yml)
            tasks = []
            for p in data.get("phases", []):
                tasks.extend(p.get("tasks", []))
            total = len(tasks)
            completed = sum(1 for t in tasks if t.get("status") == "completed")
            task_summary = f"({completed}/{total} tasks completed)"
        except Exception:
            task_summary = "(unreadable)"

        if phase_status == "completed":
            symbol = "[DONE]"
        elif phase_status == "active":
            symbol = "[ACTIVE]"
        elif phase_status == "blocked":
            symbol = "[BLOCKED]"
        else:
            symbol = "[PENDING]"

        print(f"  {symbol:<10} {phase_name} {task_summary}")

    print()

    # If no active phase, stop here
    if not active:
        print("No active phase found.")
        print("Use '/roadmap create <name>' to create a new roadmap")
        sys.exit(0)

    # Parse roadmap.yml of the active phase for detailed task info
    roadmap_yml = active["roadmap_dir"] / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    roadmap_info = data.get("roadmap", {})
    status_info = data.get("status", {})
    current_focus = data.get("current_focus", {})

    # Determine the phase folder name from the active roadmap_dir
    active_phase_folder = active["roadmap_dir"].name

    print(f"Active Phase: {active_phase_folder}")
    print(f"Branch: {active['expected_branch']}")

    # Show current task description if available
    current_phase_id = current_focus.get("phase", "N/A")
    current_task_id = current_focus.get("task", "N/A")
    current_task_title = ""
    for phase in data.get("phases", []):
        if phase.get("id") == current_phase_id:
            for task in phase.get("tasks", []):
                if task.get("id") == current_task_id:
                    current_task_title = task.get("title", "")
                    break
            break

    if current_task_title:
        print(f"Current Task: {current_task_id} - {current_task_title}")
    else:
        print(f"Current Task: {current_task_id}")

    print()

    # Display tasks from the active phase only
    phases = data.get("phases", [])
    total_tasks = 0
    completed_tasks = 0

    for phase in phases:
        phase_id = phase.get("id", "unknown")
        tasks = phase.get("tasks", [])

        for task in tasks:
            task_id = task.get("id", "unknown")
            task_title = task.get("title", "Untitled")
            task_status = task.get("status", "pending")

            total_tasks += 1
            if task_status == "completed":
                completed_tasks += 1

            if task_status == "completed":
                task_symbol = "[DONE]"
            elif task_status == "active":
                task_symbol = "[ACTIVE]"
            elif task_status == "blocked":
                task_symbol = "[BLOCKED]"
            else:
                task_symbol = "[PENDING]"

            is_current = (phase_id == current_phase_id and task_id == current_task_id)
            current_marker = " (CURRENT)" if is_current else ""

            print(f"  {task_symbol:<10} {task_id}: {task_title}{current_marker}")

            notes = task.get("notes")
            if notes:
                print(f"              Notes: {notes}")

    # Display progress summary
    print()
    if total_tasks > 0:
        progress_pct = (completed_tasks / total_tasks) * 100
        print(f"Progress: {completed_tasks}/{total_tasks} tasks completed ({progress_pct:.1f}%)")
    else:
        print("Progress: No tasks defined")


def main():
    """Main entry point for status command."""
    display_status()


if __name__ == "__main__":
    main()
