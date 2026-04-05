#!/usr/bin/env python3
"""Check for active roadmaps at session start."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'common'))
from check_session import check_session_initialized

# Check session initialization
check_session_initialized('roadmap')

from utils import RoadmapManager


def main():
    """Check for active roadmaps and display status."""
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    active = manager.find_active_roadmap()

    if active:
        print("Active Roadmap Status:")
        print("[x] Active roadmap found")
        print(f"    Name: {active['name']}")
        print(f"    Path: {active['path']}")
        print(f"    Current Phase: {active['current_phase']}")
        print(f"    Current Task: {active['current_task']}")
        print(f"    Status: {active['status']}")
        print(f"    Expected branch: {active['expected_branch']}")
        print()
        print("Next Steps:")
        print(f"- Read {active['path']}/INVARIANTS.md, ROADMAP.md, roadmap.yml")
        print(f"- Review latest session handoff in {active['path']}/sessions/")
        print("- Continue work on current task")
        sys.exit(0)  # Active roadmap found
    else:
        print("Active Roadmap Status:")
        print("[ ] No active roadmap")
        sys.exit(1)  # No active roadmap


if __name__ == "__main__":
    main()
