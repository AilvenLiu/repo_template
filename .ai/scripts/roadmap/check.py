#!/usr/bin/env python3
"""Check roadmap state at session start."""

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


def main() -> None:
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    active_steps = manager.find_active_roadmaps()

    if len(active_steps) > 1:
        print("Active Roadmap Status:")
        print("[!] Invalid roadmap state: multiple active steps detected")
        for step in active_steps:
            print(f"    - {step['name']} ({step['path']})")
        print()
        print("Fix roadmap.yml files so only one step has status.active: true")
        sys.exit(2)

    if not active_steps:
        print("Active Roadmap Status:")
        print("[ ] No active roadmap")
        sys.exit(1)

    active = active_steps[0]
    unresolved = active.get("unresolved_step_dependencies", [])

    print("Active Roadmap Status:")
    print("[x] Active roadmap found")
    print(f"    Name: {active['display_name']}")
    print(f"    Path: {active['path']}")
    print(f"    Step folder: {active['name']}")
    print(f"    Current task: {active.get('current_task') or 'none'}")
    print(f"    Expected branch: {active['expected_branch']}")

    if unresolved:
        print(f"    Unresolved step dependencies: {', '.join(unresolved)}")
        print("    State: BLOCKED by unmet dependencies")
        print()
        print("Dependency-safe operation requires resolving these steps first.")
        sys.exit(2)
    else:
        print("    Step dependencies: satisfied")

    print()
    print("Next Steps:")
    print(f"- Read {active['path']}/INVARIANTS.md, ROADMAP.md, roadmap.yml")
    print(f"- Review latest session handoff in {active['path']}/sessions/")
    print("- Continue only on the current focus task")


if __name__ == "__main__":
    main()
