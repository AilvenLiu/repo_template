#!/usr/bin/env python3
"""Claude compatibility wrapper for shared capability audit implementation."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[3]
_SHARED_PATH = _REPO_ROOT / ".ai" / "tools" / "capability_audit.py"
_SPEC = importlib.util.spec_from_file_location("shared_capability_audit", _SHARED_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"Failed to load shared capability audit from {_SHARED_PATH}")
_SHARED = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _SHARED
_SPEC.loader.exec_module(_SHARED)

AuditEntry = _SHARED.AuditEntry
AuditResult = _SHARED.AuditResult
print_audit_report = _SHARED.print_audit_report


def run_audit(repo_root: Path, is_claude: bool = True, verbose: bool = False) -> AuditResult:
    platform = "claude" if is_claude else "codex"
    return _SHARED.run_audit(repo_root=repo_root, platform=platform, verbose=verbose)


def main() -> None:
    parser = argparse.ArgumentParser(description="Capability audit")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument(
        "--agent",
        choices=["claude", "other"],
        default="claude",
        help="Compatibility flag: claude => platform claude; other => platform codex",
    )
    args = parser.parse_args()

    platform = "claude" if args.agent == "claude" else "codex"
    result = _SHARED.run_audit(
        repo_root=_REPO_ROOT,
        platform=platform,
        verbose=args.verbose and not args.json,
    )

    if args.json:
        print(json.dumps(result.to_dict(), indent=2))
    elif not args.verbose:
        print_audit_report(result)

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
