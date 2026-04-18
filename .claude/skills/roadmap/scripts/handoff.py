#!/usr/bin/env python3
"""Generate session handoff file for active roadmap phase."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "common"))
from check_session import check_session_initialized

from utils import RoadmapManager


def _get_single_active_phase(manager: RoadmapManager):
    active = manager.find_active_roadmaps()
    if not active:
        print("ERROR: No active roadmap found")
        sys.exit(1)
    if len(active) > 1:
        print("ERROR: Multiple active phases found")
        for phase in active:
            print(f"  - {phase['name']}")
        print("Fix roadmap.yml so only one phase has status.active: true")
        sys.exit(2)
    return active[0]


def generate_handoff(work_completed: str, decisions: str, blockers: str, next_steps: str) -> None:
    check_session_initialized("roadmap")

    manager = RoadmapManager(Path.cwd())
    active = _get_single_active_phase(manager)

    roadmap_dir = active["roadmap_dir"]
    sessions_dir = roadmap_dir / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d-%H-%M")
    filename = f"session-{timestamp}.md"
    handoff_path = sessions_dir / filename

    data = manager.parse_roadmap_yml(roadmap_dir / "roadmap.yml")

    phase_folder = roadmap_dir.name
    expected_branch = active.get("expected_branch", f"roadmap/{phase_folder}")
    current_task = data.get("focus", {}).get("current_task")
    phase_dependencies = data.get("depends_on_phases", [])

    content = f"""# Session Handoff: {now.strftime('%Y-%m-%d %H:%M')}\n\n## Focus\n- Phase folder: {phase_folder}\n- Branch: {expected_branch}\n- Current task: {current_task}\n- Phase dependencies: {phase_dependencies}\n\n## Work Completed\n{work_completed}\n\n## Decisions Made\n{decisions}\n\n## Open Issues / Blockers\n{blockers}\n\n## Next Session Handoff\n{next_steps}\n"""

    try:
        handoff_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"ERROR: Failed to create handoff file: {exc}")
        sys.exit(1)

    print(f"Session handoff created: {handoff_path.relative_to(Path.cwd())}")
    print(f"  Phase: {phase_folder}")
    print(f"  Branch: {expected_branch}")


def main() -> None:
    print("Session Handoff Generator")
    print("=" * 50)
    print()

    print("Work Completed:")
    print("(Describe what was accomplished in this session)")
    work_completed = input("> ")
    print()

    print("Decisions Made:")
    print("(List key decisions or architectural choices)")
    decisions = input("> ")
    print()

    print("Open Issues / Blockers:")
    print("(Describe blockers or unresolved issues)")
    blockers = input("> ")
    print()

    print("Next Session Handoff:")
    print("(Guidance for the next session)")
    next_steps = input("> ")
    print()

    generate_handoff(work_completed, decisions, blockers, next_steps)


if __name__ == "__main__":
    main()
