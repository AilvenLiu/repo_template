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
        SystemExit: If session not initialized
    """
    state_file = Path('.claude/session_state.json')

    if not state_file.exists():
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
    state_file = Path('.claude/session_state.json')
    if not state_file.exists():
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
