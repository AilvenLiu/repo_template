#!/usr/bin/env python3
"""Shared project-type detection for Claude and Codex adapters."""

from enum import Enum
from pathlib import Path
from typing import Optional

_IGNORE_DIRS = frozenset(
    {
        ".claude",
        ".codex",
        ".ai",
        ".git",
        ".github",
        ".vscode",
        ".idea",
        "agent_roadmaps",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "cmake-build-debug",
        "cmake-build-release",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


class ProjectType(Enum):
    PYTHON = "python"
    CPP = "cpp"
    UNKNOWN = "unknown"


def _read_project_yml(repo_root: Path) -> Optional[str]:
    yml = repo_root / ".ai" / "project.yml"
    if not yml.exists():
        return None

    try:
        for line in yml.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("project_type:"):
                value = stripped.split(":", 1)[1].strip()
                if value in ("python", "cpp"):
                    return value
    except Exception:
        return None

    return None


def _heuristic(repo_root: Path) -> Optional[str]:
    python_score = 0
    cpp_score = 0

    for entry in repo_root.iterdir():
        if entry.name in _IGNORE_DIRS:
            continue

        if entry.is_file():
            name = entry.name
            if name in (
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                "poetry.lock",
                "Pipfile",
            ):
                python_score += 3
            elif name.endswith(".py"):
                python_score += 1
            elif name in (
                "CMakeLists.txt",
                "conanfile.txt",
                "conanfile.py",
                "vcpkg.json",
                "Makefile",
            ):
                cpp_score += 3
            elif name.endswith((".cpp", ".hpp", ".cu", ".cuh", ".h")):
                cpp_score += 1

        elif entry.is_dir():
            try:
                children = list(entry.iterdir())
            except PermissionError:
                continue

            for child in children:
                if not child.is_file():
                    continue
                if child.suffix == ".py":
                    python_score += 1
                elif child.suffix in (".cpp", ".hpp", ".cu", ".cuh", ".h"):
                    cpp_score += 1

    if python_score == 0 and cpp_score == 0:
        return None

    return "python" if python_score >= cpp_score else "cpp"


def detect(repo_root: Optional[Path] = None) -> ProjectType:
    root = repo_root or Path.cwd()

    configured = _read_project_yml(root)
    if configured:
        return ProjectType(configured)

    guessed = _heuristic(root)
    if guessed:
        return ProjectType(guessed)

    return ProjectType.UNKNOWN
