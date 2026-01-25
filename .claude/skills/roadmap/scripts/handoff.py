#!/usr/bin/env python3
"""Generate session handoff file."""

import sys
from pathlib import Path
from datetime import datetime

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def generate_handoff(work_completed: str, decisions: str, blockers: str, next_steps: str) -> None:
    """Generate session handoff file.

    Args:
        work_completed: Description of work completed
        decisions: Decisions made during session
        blockers: Open issues or blockers
        next_steps: Guidance for next session
    """
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Find active roadmap
    active = manager.find_active_roadmap()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)

    roadmap_dir = active["roadmap_dir"]
    sessions_dir = roadmap_dir / "sessions"

    # Generate filename: YYYY-MM-DD-claude-<index>.md
    today = datetime.now().strftime("%Y-%m-%d")
    existing_files = list(sessions_dir.glob(f"{today}-claude-*.md"))
    index = len(existing_files) + 1
    filename = f"{today}-claude-{index}.md"
    handoff_path = sessions_dir / filename

    # Generate handoff content
    content = f"""# Session Handoff: {today} (Session {index})

## Focus
Phase: {active['current_phase']}
Task: {active['current_task']}

## Work Completed
{work_completed}

## Decisions Made
{decisions}

## Blockers / Open Issues
{blockers}

## Next Steps
{next_steps}
"""

    # Write handoff file
    try:
        with open(handoff_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Session handoff created: {handoff_path.relative_to(repo_root)}")
    except Exception as e:
        print(f"ERROR: Failed to create handoff file: {e}")
        sys.exit(1)


def main():
    """Main entry point for handoff command."""
    print("Session Handoff Generator")
    print("=" * 50)
    print()

    # Prompt for information
    print("Work Completed:")
    print("(Describe what was accomplished in this session)")
    work_completed = input("> ")
    print()

    print("Decisions Made:")
    print("(List key decisions or architectural choices)")
    decisions = input("> ")
    print()

    print("Blockers / Open Issues:")
    print("(Describe any blockers or unresolved issues)")
    blockers = input("> ")
    print()

    print("Next Steps:")
    print("(Guidance for the next session)")
    next_steps = input("> ")
    print()

    generate_handoff(work_completed, decisions, blockers, next_steps)


if __name__ == "__main__":
    main()
