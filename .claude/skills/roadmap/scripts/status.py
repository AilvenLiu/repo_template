#!/usr/bin/env python3
"""Display detailed status of active roadmap."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def display_status() -> None:
    """Display detailed status of active roadmap."""
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Find active roadmap
    active = manager.find_active_roadmap()
    if not active:
        print("No active roadmap found")
        print("Use '/roadmap create <name>' to create a new roadmap")
        sys.exit(1)

    # Parse roadmap.yml for detailed information
    roadmap_yml = active["roadmap_dir"] / "roadmap.yml"
    data = manager.parse_roadmap_yml(roadmap_yml)

    # Display header
    roadmap_info = data.get("roadmap", {})
    status_info = data.get("status", {})
    current_focus = data.get("current_focus", {})

    print(f"Roadmap: {roadmap_info.get('name', 'unknown')}")
    print(f"Description: {roadmap_info.get('description', 'N/A')}")
    print(f"Status: {'active' if status_info.get('active') else 'inactive'} | ", end="")
    if status_info.get('blocked'):
        print("BLOCKED", end="")
    elif status_info.get('completed'):
        print("COMPLETED", end="")
    else:
        print(f"Current Focus: {current_focus.get('phase', 'N/A')} / {current_focus.get('task', 'N/A')}", end="")
    print()
    print()

    # Display phases and tasks
    phases = data.get("phases", [])
    total_tasks = 0
    completed_tasks = 0

    print("Phases:")
    for phase in phases:
        phase_id = phase.get("id", "unknown")
        phase_title = phase.get("title", "Untitled")
        phase_status = phase.get("status", "pending")
        tasks = phase.get("tasks", [])

        # Count tasks
        phase_total = len(tasks)
        phase_completed = sum(1 for t in tasks if t.get("status") == "completed")
        total_tasks += phase_total
        completed_tasks += phase_completed

        # Phase status symbol
        if phase_status == "completed":
            symbol = "[DONE]"
        elif phase_status == "active":
            symbol = "[ACTIVE]"
        elif phase_status == "blocked":
            symbol = "[BLOCKED]"
        else:
            symbol = "[PENDING]"

        print(f"  {symbol} {phase_id}: {phase_title} ({phase_completed}/{phase_total} tasks completed)")

        # Display tasks
        for task in tasks:
            task_id = task.get("id", "unknown")
            task_title = task.get("title", "Untitled")
            task_status = task.get("status", "pending")

            # Task status symbol
            if task_status == "completed":
                task_symbol = "[DONE]"
            elif task_status == "active":
                task_symbol = "[ACTIVE]"
            elif task_status == "blocked":
                task_symbol = "[BLOCKED]"
            else:
                task_symbol = "[PENDING]"

            # Highlight current task
            is_current = (phase_id == current_focus.get("phase") and
                         task_id == current_focus.get("task"))
            current_marker = " (CURRENT)" if is_current else ""

            print(f"      {task_symbol} {task_id}: {task_title}{current_marker}")

            # Show notes if present
            notes = task.get("notes")
            if notes:
                print(f"          Notes: {notes}")

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
