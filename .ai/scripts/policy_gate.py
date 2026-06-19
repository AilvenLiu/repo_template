#!/usr/bin/env python3
"""Shared policy gate for mutation, bash, commit, and dependency operations."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

try:
    from .constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from .paths import resolve_repo_root
    from .project_profile import Language, detect as detect_profile
    from .project_type import ProjectType, detect
    from .session_state import read_state
except ImportError:
    from constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from paths import resolve_repo_root
    from project_profile import Language, detect as detect_profile
    from project_type import ProjectType, detect
    from session_state import read_state


def _repo_root() -> Path:
    return resolve_repo_root(Path(__file__).resolve())


def _load_context(raw: str) -> Dict[str, str]:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def _current_branch(repo_root: Path) -> str:
    try:
        process = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
    except FileNotFoundError:
        return ""

    if process.returncode != 0:
        return ""
    return process.stdout.strip()


def _is_protected_branch(branch: str) -> bool:
    return branch in PROTECTED_BRANCHES or any(
        branch.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def _is_init_command(command: str) -> bool:
    command = command.strip()
    if re.search(r"[;&|<>$`\\]", command):
        return False

    patterns = [
        r"^\.ai/bin/agent-init(\s+--platform\s+(claude|codex))?(\s+--verbose)?\s*$",
    ]
    return any(re.match(pattern, command) for pattern in patterns)


def _session_gate(repo_root: Path) -> Tuple[bool, str]:
    state = read_state(repo_root)
    if state is None:
        return False, "BLOCKED: Session not initialized. Run /init or .ai/bin/agent-init first."

    if not state.get("initialized", False):
        return False, "BLOCKED: Session initialization incomplete. Re-run init."

    audit = state.get("capability_audit")
    if isinstance(audit, dict) and not audit.get("passed", True):
        return (
            False,
            "BLOCKED: Capability audit failed. Install missing capabilities and rerun init.",
        )

    return True, ""


def _check_bash_command(command: str, project_type: ProjectType, repo_root: Path) -> Tuple[bool, str]:
    branch = _current_branch(repo_root)

    if re.search(r"^\s*git\s+commit", command):
        if branch and _is_protected_branch(branch):
            return False, f"BLOCKED: git commit on protected branch '{branch}'."

    if re.search(r"git\s+push\s+.*(--force|-f\b)", command):
        return False, "BLOCKED: git push --force requires explicit user confirmation."

    if re.search(r"git\s+reset\s+--hard", command):
        return False, "BLOCKED: git reset --hard requires explicit user confirmation."

    if project_type == ProjectType.PYTHON:
        # Block pip install in all forms: pip, pip3, pip3.10, .venv/bin/pip*, python -m pip
        _pip_pattern = re.compile(
            r"""(?x)
            ^\s*(?:
                pip[0-9.]*                        |  # pip, pip3, pip3.10
                python[0-9.]*\s+-m\s+pip          |  # python -m pip, python3.10 -m pip
                \.venv/bin/pip[0-9.]*             |  # .venv/bin/pip, .venv/bin/pip3
                \.venv/bin/python[0-9.]*\s+-m\s+pip  # .venv/bin/python -m pip
            )\s+install
            """
        )
        if _pip_pattern.search(command) and "poetry run" not in command:
            return False, "BLOCKED: Direct pip install is forbidden. Use dependency workflow."

        # Block direct python execution in all forms: python, python3, python3.10,
        # .venv/bin/python, .venv/bin/python3.10
        _py_pattern = re.compile(
            r"""(?x)
            ^\s*(?:
                python[0-9.]*          |  # python, python3, python3.10, python3.11
                \.venv/bin/python[0-9.]*  # .venv/bin/python, .venv/bin/python3
            )\s+
            """
        )
        if _py_pattern.search(command):
            if re.search(r"\.claude/skills/|\.claude/hooks/|\.ai/scripts/", command):
                return True, ""
            if "poetry run" in command:
                return True, ""
            if re.search(r"(?:python[0-9.]*|\.venv/bin/python[0-9.]*)\s+(-V|--version)", command):
                return True, ""
            return False, "BLOCKED: Direct python/python3 execution is forbidden for app workflows. Use poetry run."

    if re.search(r"^\s*(sudo\s+)?(apt|apt-get)\s+install", command):
        if re.search(r"lib[a-z]+-dev|libboost|libopencv|libeigen|libfmt|libspdlog|libgtest", command):
            return False, "BLOCKED: System package manager install for C++ libs is forbidden."

    if re.search(r"^\s*brew\s+install", command):
        if not re.search(r"brew\s+install\s+(cmake|python|llvm|clang-format|cppcheck|ninja|pkg-config|git)", command):
            return False, "BLOCKED: brew install for non-toolchain package is forbidden for dependency flow."

    if re.search(r"rm\s+-rf\s+", command):
        if re.search(r"rm\s+-rf\s+\./?(src|lib|include|tests?|\.claude|\.codex|agent_roadmaps)", command):
            return False, "BLOCKED: rm -rf on protected project directories requires confirmation."

    return True, ""


def gate_mutate(repo_root: Path, context: Dict[str, str]) -> Tuple[bool, str]:
    ok, message = _session_gate(repo_root)
    if not ok:
        return False, message

    file_path = str(context.get("file_path", ""))
    if not file_path:
        return True, ""

    profile = detect_profile(repo_root)
    if profile is not None and profile.has_language(Language.CPP):
        path = Path(file_path)
        if path.name == "setup.py":
            return (
                False,
                "BLOCKED: setup.py edits in C++/CUDA or hybrid projects risk moving native build ownership out of CMake. Use CMake/scikit-build-core bridge policy or document an ADR exception.",
            )

    return True, ""


def gate_bash(repo_root: Path, context: Dict[str, str]) -> Tuple[bool, str]:
    command = str(context.get("command", ""))
    if not command:
        return False, "BLOCKED: Missing bash command context."

    state = read_state(repo_root)
    if state is None:
        if _is_init_command(command):
            return True, ""
        return False, "BLOCKED: Session not initialized. Only init command is allowed pre-init."

    ok, message = _session_gate(repo_root)
    if not ok:
        return False, message

    project_type = detect(repo_root)
    return _check_bash_command(command, project_type, repo_root)


def gate_commit(repo_root: Path, context: Dict[str, str]) -> Tuple[bool, str]:
    ok, message = _session_gate(repo_root)
    if not ok:
        return False, message

    branch = context.get("branch") or _current_branch(repo_root)
    if branch and _is_protected_branch(branch):
        return False, f"BLOCKED: commit on protected branch '{branch}'."

    commit_message = str(context.get("message", ""))
    forbidden_markers = ["Co-Authored-By:", "Generated with", "AI assistance", "noreply@anthropic.com"]
    if any(marker.lower() in commit_message.lower() for marker in forbidden_markers):
        return False, "BLOCKED: commit message contains forbidden AI attribution."

    return True, ""


def gate_dependency(repo_root: Path, context: Dict[str, str]) -> Tuple[bool, str]:
    ok, message = _session_gate(repo_root)
    if not ok:
        return False, message

    project_type = detect(repo_root)
    command = str(context.get("command", ""))

    if project_type == ProjectType.PYTHON and command:
        if re.search(r"\bpip\s+install\b", command):
            return False, "BLOCKED: use dependency wrapper, not direct pip install."

    if project_type == ProjectType.CPP and command:
        if re.search(r"\b(apt|apt-get|brew|yum|dnf)\s+install\b", command):
            return False, "BLOCKED: use the CMake/CPM workflow, not system package manager."

    return True, ""


def _build_context(args: argparse.Namespace) -> Dict[str, str]:
    context = _load_context(args.context)

    if args.context_file:
        file_context = _load_context(Path(args.context_file).read_text())
        context.update(file_context)

    if args.command is not None:
        context["command"] = args.command
    if args.message is not None:
        context["message"] = args.message
    if args.branch is not None:
        context["branch"] = args.branch

    return context


def main() -> None:
    parser = argparse.ArgumentParser(description="Shared policy gate")
    parser.add_argument("--op", choices=["mutate", "bash", "commit", "dependency"], required=True)
    parser.add_argument("--context", default="{}", help="JSON context payload")
    parser.add_argument("--context-file", help="Path to JSON context payload")
    parser.add_argument("--command", help="Command context (alternative to JSON)")
    parser.add_argument("--message", help="Commit message context (alternative to JSON)")
    parser.add_argument("--branch", help="Branch context (alternative to JSON)")
    parser.add_argument("--json", action="store_true", help="Emit JSON response")
    args = parser.parse_args()

    repo_root = _repo_root()
    context = _build_context(args)

    if args.op == "mutate":
        allowed, message = gate_mutate(repo_root, context)
    elif args.op == "bash":
        allowed, message = gate_bash(repo_root, context)
    elif args.op == "commit":
        allowed, message = gate_commit(repo_root, context)
    else:
        allowed, message = gate_dependency(repo_root, context)

    response = {"allowed": allowed, "message": message}

    if args.json:
        print(json.dumps(response))
    elif not allowed and message:
        print(message, file=sys.stderr)

    sys.exit(0 if allowed else 1)


if __name__ == "__main__":
    main()
