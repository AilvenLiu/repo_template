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

    active_phases = manager.find_active_phases()

    if len(active_phases) > 1:
        print("Active Roadmap Status:")
        print("[!] Invalid roadmap state: multiple active phases detected")
        for phase in active_phases:
            print(f"    - {phase['name']} ({phase['path']})")
        print()
        print("Fix roadmap.yml files so only one phase has status.active: true")
        sys.exit(2)

    if not active_phases:
        print("Active Roadmap Status:")
        print("[ ] No active roadmap")
        sys.exit(1)

    active = active_phases[0]
    unresolved = active.get("unresolved_phase_dependencies", [])

    print("Active Roadmap Status:")
    print("[x] Active roadmap found")
    print(f"    Name: {active['display_name']}")
    print(f"    Path: {active['path']}")
    print(f"    Phase folder: {active['name']}")
    print(f"    Current task: {active.get('current_task') or 'none'}")
    print(f"    Expected branch: {active['expected_branch']}")

    if unresolved:
        print(f"    Unresolved phase dependencies: {', '.join(unresolved)}")
        print("    State: BLOCKED by unmet dependencies")
        print()
        print("Dependency-safe operation requires resolving these phases first.")
        sys.exit(2)
    else:
        print("    Phase dependencies: satisfied")

    print()
    print("Next Steps:")
    print(f"- Read {active['path']}/INVARIANTS.md, ROADMAP.md, roadmap.yml")
    print(f"- Review latest session handoff in {active['path']}/sessions/")
    print("- Continue only on the current focus task")


if __name__ == "__main__":
    main()
