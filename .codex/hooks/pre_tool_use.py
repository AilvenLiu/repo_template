#!/usr/bin/env python3
"""Thin Codex PreToolUse adapter for the shared repository policy gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / ".agents" / "scripts"))

import policy_gate  # type: ignore[import-not-found]  # noqa: E402


def _load_input() -> dict[str, Any]:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def main() -> int:
    payload = _load_input()
    tool_name = str(payload.get("tool_name", ""))
    raw_input = payload.get("tool_input", {})
    tool_input = raw_input if isinstance(raw_input, dict) else {}

    if tool_name == "Bash":
        allowed, message = policy_gate.gate_bash(
            REPO_ROOT,
            {"command": str(tool_input.get("command", ""))},
        )
    elif tool_name in {"apply_patch", "Edit", "Write", "MultiEdit"}:
        allowed, message = policy_gate.gate_mutate(
            REPO_ROOT,
            {"file_path": str(tool_input.get("file_path", ""))},
        )
    else:
        return 0

    if allowed:
        return 0

    print(
        message or "BLOCKED: Repository policy denied this tool call.", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
