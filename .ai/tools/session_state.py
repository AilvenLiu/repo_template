#!/usr/bin/env python3
"""Shared session-state read/write helpers for all agent adapters."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

STATE_RELATIVE_PATHS = (
    Path(".ai/session_state.json"),
    Path(".claude/session_state.json"),
)


def read_state(repo_root: Path) -> Optional[Dict[str, Any]]:
    """Read the newest available session state, if present."""
    for rel_path in STATE_RELATIVE_PATHS:
        candidate = repo_root / rel_path
        if not candidate.exists():
            continue
        try:
            return json.loads(candidate.read_text())
        except json.JSONDecodeError:
            return None
    return None


def write_state(repo_root: Path, state: Dict[str, Any]) -> None:
    """Write session state to both canonical and Claude-compat locations."""
    state = dict(state)
    state.setdefault("timestamp", datetime.now().isoformat())

    payload = json.dumps(state, indent=2) + "\n"
    for rel_path in STATE_RELATIVE_PATHS:
        target = repo_root / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(payload)
