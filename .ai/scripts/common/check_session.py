#!/usr/bin/env python3
"""
Session state checker utility.
All skills should import and call this before execution.
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta


def check_session_initialized(skill_name: str) -> dict:
    """
    Verify session was initialized with /init.

    Args:
        skill_name: Name of the skill being executed

    Returns:
        Session state dict if initialized

    Raises:
        SystemExit: If session not initialized or capability audit failed
    """
    candidate_files = [
        Path(".ai/session_state.json"),
        Path(".claude/session_state.json"),
    ]
    state_file = next((p for p in candidate_files if p.exists()), candidate_files[0])

    if not any(p.exists() for p in candidate_files):
        print("=" * 70)
        print("ERROR: Session not initialized")
        print("=" * 70)
        print()
        print(f"The '{skill_name}' skill requires session initialization.")
        print()
        print("REQUIRED ACTION:")
        print("  Run /init before using any skills")
        print()
        print("WHY THIS MATTERS:")
        print("  - Loads project-specific constraints")
        print("  - Detects project type (Python vs C++/CUDA)")
        print("  - Checks for active roadmaps")
        print("  - Validates git branch status")
        print("  - Audits required capabilities")
        print()
        print("=" * 70)
        sys.exit(1)

    try:
        with open(state_file) as f:
            state = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Corrupted session state file: {state_file}")
        print("REQUIRED: Run /init to reinitialize")
        sys.exit(1)

    if not state.get('initialized'):
        print("ERROR: Session initialization incomplete")
        print("REQUIRED: Run /init to complete initialization")
        sys.exit(1)

    # Check capability audit result
    audit = state.get('capability_audit')
    if audit is not None and not audit.get('passed', True):
        print("=" * 70)
        print("ERROR: Capability audit failed")
        print("=" * 70)
        print()
        print(f"The '{skill_name}' skill cannot run because the session capability")
        print("audit failed during /init.")
        print()
        print("REQUIRED ACTION:")
        print("  1. Review the audit failures from /init output")
        print("  2. Install missing plugins, skills, or integrations")
        print("  3. Re-run /init to pass the audit")
        print()
        print("AUDIT SUMMARY:")
        entries = audit.get('entries', [])
        failed = [e for e in entries if e.get('required') and not e.get('available')]
        for e in failed:
            print(f"  [FAIL] {e.get('id', 'unknown')}")
            msg = e.get('message', '')
            if msg:
                for line in msg.strip().splitlines()[:2]:  # first 2 lines only
                    print(f"         {line}")
        print()
        print("=" * 70)
        sys.exit(1)

    # Check if session is stale (>24 hours old)
    try:
        timestamp = datetime.fromisoformat(state['timestamp'])
        age = datetime.now() - timestamp
        if age > timedelta(hours=24):
            print("WARNING: Session state is stale (>24 hours old)")
            print("RECOMMENDED: Run /init to refresh constraints")
            print()
    except (KeyError, ValueError):
        pass

    return state


def get_project_type() -> str:
    """Get project type from session state."""
    candidate_files = [
        Path(".ai/session_state.json"),
        Path(".claude/session_state.json"),
    ]
    state_file = next((p for p in candidate_files if p.exists()), candidate_files[0])

    if not any(p.exists() for p in candidate_files):
        return 'unknown'

    try:
        with open(state_file) as f:
            state = json.load(f)
            return state.get('project_type', 'unknown')
    except (json.JSONDecodeError, IOError):
        return 'unknown'


if __name__ == '__main__':
    # Allow running as standalone check
    try:
        state = check_session_initialized('manual-check')
        print("✓ Session initialized")
        print(f"  Project type: {state.get('project_type')}")
        print(f"  Initialized: {state.get('timestamp')}")
        print(f"  Constraints loaded: {len(state.get('loaded_constraints', []))}")
    except SystemExit:
        sys.exit(1)
