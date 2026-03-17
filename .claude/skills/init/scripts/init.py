#!/usr/bin/env python3
"""
Session Initialization Script

Detects project type, loads and prints full constraint bodies so the agent
actually receives them, creates session state, and warns about protected
branches and active roadmaps.

Usage:
    python3 .claude/skills/init/scripts/init.py [--verbose]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Bootstrap: make the common package importable
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[4]
_COMMON_DIR = _REPO_ROOT / ".claude" / "skills" / "common"
if str(_COMMON_DIR) not in sys.path:
    sys.path.insert(0, str(_COMMON_DIR))

from project_type import ProjectType, detect  # noqa: E402
from capability_audit import run_audit, print_audit_report, AuditResult  # noqa: E402


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CONSTRAINTS_DIR = _REPO_ROOT / ".ai" / "constraints"
SESSION_STATE = _REPO_ROOT / ".claude" / "session_state.json"
PROTECTED_BRANCHES = {"master", "main", "develop"}
PROTECTED_PREFIXES = ("release/", "hotfix/")


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def git_current_branch() -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True, text=True, cwd=_REPO_ROOT,
        )
        return r.stdout.strip() if r.returncode == 0 else None
    except FileNotFoundError:
        return None


def git_modified_files() -> List[str]:
    try:
        r = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, cwd=_REPO_ROOT,
        )
        if r.returncode != 0:
            # Maybe no commits yet — try diff of index
            r = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, cwd=_REPO_ROOT,
            )
        return [f for f in r.stdout.strip().splitlines() if f]
    except FileNotFoundError:
        return []


# ---------------------------------------------------------------------------
# Roadmap detection
# ---------------------------------------------------------------------------

def find_active_roadmap() -> Optional[Path]:
    roadmaps_dir = _REPO_ROOT / "agent_roadmaps"
    if not roadmaps_dir.is_dir():
        return None
    for child in roadmaps_dir.iterdir():
        if child.is_dir() and (child / "roadmap.yml").exists():
            yml = child / "roadmap.yml"
            try:
                content = yml.read_text()
                if "status: active" in content or "status: in_progress" in content:
                    return child
            except Exception:
                continue
    return None


# ---------------------------------------------------------------------------
# Constraint loading
# ---------------------------------------------------------------------------

# Always-loaded constraints per project type
_ALWAYS_COMMON = [
    "common/git-workflow",
    "common/session-discipline",
    "common/mcp-integration",
    "common/ascii-only",
]

_ALWAYS_PYTHON = [
    "python/dependencies",
    "python/forbidden-practices",
    "python/security",
    "python/error-handling",
]

_ALWAYS_CPP = [
    "cpp/dependencies",
    "cpp/forbidden-practices",
    "cpp/error-handling",
    "cpp/static-analysis",
]

# File-extension triggers for conditional constraints
_PYTHON_TRIGGERS = {
    ".py": ["python/formatting", "python/type-checking"],
}
_PYTHON_TEST_TRIGGER = ["python/testing"]

_CPP_TRIGGERS = {
    ".cpp": ["cpp/formatting", "cpp/memory-safety"],
    ".hpp": ["cpp/formatting", "cpp/memory-safety"],
    ".cu":  ["cpp/cuda"],
    ".cuh": ["cpp/cuda"],
}
_CPP_CMAKE_TRIGGER = ["cpp/cmake"]
_CPP_TEST_TRIGGER = ["cpp/testing"]


def resolve_constraints(
    project_type: ProjectType,
    modified_files: List[str],
    has_roadmap: bool,
) -> List[str]:
    """Return ordered list of constraint keys to load."""
    keys: List[str] = list(_ALWAYS_COMMON)

    if has_roadmap:
        keys.append("common/roadmap-awareness")

    if project_type == ProjectType.PYTHON:
        keys.extend(_ALWAYS_PYTHON)
        exts_seen = {Path(f).suffix for f in modified_files}
        for ext, extra in _PYTHON_TRIGGERS.items():
            if ext in exts_seen:
                keys.extend(extra)
        if any("test" in f.lower() for f in modified_files):
            keys.extend(_PYTHON_TEST_TRIGGER)
    elif project_type == ProjectType.CPP:
        keys.extend(_ALWAYS_CPP)
        exts_seen = {Path(f).suffix for f in modified_files}
        for ext, extra in _CPP_TRIGGERS.items():
            if ext in exts_seen:
                keys.extend(extra)
        if any("cmake" in f.lower() for f in modified_files):
            keys.extend(_CPP_CMAKE_TRIGGER)
        if any("test" in f.lower() for f in modified_files):
            keys.extend(_CPP_TEST_TRIGGER)

    # Deduplicate while preserving order
    seen: set = set()
    unique: List[str] = []
    for k in keys:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique


def load_constraint(key: str) -> Optional[str]:
    """Read a constraint file and return its body, or None."""
    path = CONSTRAINTS_DIR / (key + ".md")
    if path.exists():
        try:
            return path.read_text()
        except Exception:
            return None
    return None


# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------

def write_session_state(
    project_type: ProjectType,
    branch: Optional[str],
    loaded_constraints: List[str],
    roadmap_dir: Optional[Path],
    audit_result: Optional[AuditResult] = None,
) -> None:
    state: Dict[str, Any] = {
        "initialized": True,
        "timestamp": datetime.now().isoformat(),
        "project_type": project_type.value,
        "branch": branch,
        "loaded_constraints": loaded_constraints,
        "active_roadmap": str(roadmap_dir) if roadmap_dir else None,
    }
    if audit_result is not None:
        state["capability_audit"] = audit_result.to_dict()
    SESSION_STATE.parent.mkdir(parents=True, exist_ok=True)
    SESSION_STATE.write_text(json.dumps(state, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Session initialization")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    sep = "=" * 70

    print(sep)
    print("SESSION INITIALIZATION")
    print(sep)
    print()

    # 1. Detect project type
    ptype = detect(_REPO_ROOT)
    if ptype == ProjectType.UNKNOWN:
        print("[WARN] Could not detect project type — defaulting to python")
        print("       To fix: create .ai/project.yml with 'project_type: python' or 'project_type: cpp'")
        print("       Or add project indicators (requirements.txt, CMakeLists.txt, etc.)")
        ptype = ProjectType.PYTHON

    # Check if detection was from config or heuristic
    yml_path = _REPO_ROOT / ".ai" / "project.yml"
    if yml_path.exists():
        print(f"[OK] Project type: {ptype.value.upper()} (from .ai/project.yml)")
    else:
        print(f"[OK] Project type: {ptype.value.upper()} (heuristic)")
        print("       Note: Create .ai/project.yml for deterministic detection")

    # 2. Roadmap
    roadmap_dir = find_active_roadmap()
    if roadmap_dir:
        print(f"[OK] Active roadmap: {roadmap_dir.name}")
    else:
        print("[--] No active roadmap")

    # 3. Git
    branch = git_current_branch()
    if branch:
        is_protected = (
            branch in PROTECTED_BRANCHES
            or any(branch.startswith(p) for p in PROTECTED_PREFIXES)
        )
        marker = "[WARN]" if is_protected else "[OK]"
        print(f"{marker} Branch: {branch}")
        if is_protected:
            print("       ^^^ Protected branch — create a feature branch before committing!")
    else:
        print("[--] Not in a git repository (or no commits yet)")

    modified = git_modified_files()
    if modified:
        print(f"[OK] {len(modified)} modified file(s)")
    print()

    # 4. Run capability audit
    print(sep)
    print("CAPABILITY AUDIT")
    print(sep)
    print()
    print("Checking required plugins, skills, and integrations...")
    print()

    audit_result = run_audit(_REPO_ROOT, is_claude=True, verbose=args.verbose)
    print_audit_report(audit_result)

    # 5. Resolve and load constraints
    keys = resolve_constraints(ptype, modified, roadmap_dir is not None)

    print(sep)
    print("LOADED CONSTRAINTS")
    print(sep)
    print()

    loaded: List[str] = []
    for key in keys:
        body = load_constraint(key)
        if body is None:
            print(f"[MISS] {key}  (file not found)")
            continue
        loaded.append(key)
        # Print the FULL body so the agent actually ingests it
        print(f"[CONSTRAINT] {key}")
        print(body)
        print()

    # 6. Write session state
    write_session_state(ptype, branch, loaded, roadmap_dir, audit_result)

    print(sep)
    print(f"Total constraints loaded: {len(loaded)}")
    print(sep)
    print()

    # 6.5. Fail loudly if audit failed (after writing state)
    if not audit_result.passed:
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 15 + "⚠️  CAPABILITY AUDIT FAILED  ⚠️" + " " * 16 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("The session is BLOCKED. Mutation operations are disabled.")
        print()
        print("REQUIRED ACTION:")
        print("  1. Review the audit failures above")
        print("  2. Install missing plugins, skills, or integrations")
        print("  3. Re-run /init to pass the audit")
        print()
        print("Read-only operations (Read, Glob, Grep) remain available for exploration.")
        print()
        sys.exit(1)

    # 6.6. Warn loudly if no constraints loaded
    if len(loaded) == 0:
        print("╔" + "═" * 68 + "╗")
        print("║" + " " * 20 + "⚠️  WARNING: NO CONSTRAINTS LOADED  ⚠️" + " " * 9 + "║")
        print("╚" + "═" * 68 + "╝")
        print()
        print("This session will operate WITHOUT coding standards enforcement.")
        print("This usually means .ai/constraints/ is missing or empty.")
        print()
        print("RECOMMENDED:")
        print("  1. Verify .ai/constraints/ exists and contains .md files")
        print("  2. If this is a new repo, copy constraints from repo_template")
        print("  3. Re-run /init after fixing")
        print()
        print(sep)
        print()

    # 7. Next steps
    print("NEXT STEPS:")
    if roadmap_dir:
        print("1. Read roadmap files in authority order:")
        print(f"   {roadmap_dir}/INVARIANTS.md")
        print(f"   {roadmap_dir}/prompt.md")
        print(f"   {roadmap_dir}/roadmap.yml")
        print("2. Proceed with your work following the loaded constraints")
    else:
        print("1. Proceed with your work following the loaded constraints above")

    # Suggest verification if detection was heuristic
    if not yml_path.exists():
        print()
        print("RECOMMENDATION:")
        print("  Project type was detected heuristically. To verify:")
        print("  - Check that the loaded constraints match your project")
        print("  - Run /check-constraints to validate compliance")
        print("  - Create .ai/project.yml for deterministic detection")
    print()


if __name__ == "__main__":
    main()
