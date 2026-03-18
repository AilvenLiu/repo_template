#!/usr/bin/env python3
"""Shared project-type detection used by init, pre-commit, dependency, and hooks.

Detection order:
  1. .ai/project.yml  (authoritative — written by create-project)
  2. Heuristic scan    (fallback — ignores infra dirs)

Every skill that needs the project type should call ``detect()`` from here
instead of rolling its own logic.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

# Directories that must never influence the heuristic scan.
_IGNORE_DIRS = frozenset({
    ".claude", ".ai", ".git", ".github", ".vscode", ".idea",
    "agent_roadmaps", ".venv", "venv", "__pycache__",
    "build", "dist", "cmake-build-debug", "cmake-build-release",
    "node_modules", ".mypy_cache", ".pytest_cache", ".ruff_cache",
})


class ProjectType(Enum):
    PYTHON = "python"
    CPP = "cpp"
    UNKNOWN = "unknown"


def _read_project_yml(repo_root: Path) -> Optional[str]:
    """Read project_type from .ai/project.yml (source of truth)."""
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
        pass
    return None


def _heuristic(repo_root: Path) -> Optional[str]:
    """Walk top-level entries (ignoring infra dirs) for language markers.

    Returns:
        "python", "cpp", or None if no markers found

    Note: When scores are equal, defaults to Python. This can happen in
    mixed projects (e.g., C++ with Python build scripts). To override,
    create .ai/project.yml with the correct project_type.
    """
    python_score = 0
    cpp_score = 0

    for entry in repo_root.iterdir():
        if entry.name in _IGNORE_DIRS:
            continue

        if entry.is_file():
            name = entry.name
            if name in ("pyproject.toml", "setup.py", "setup.cfg",
                        "requirements.txt", "poetry.lock", "Pipfile"):
                python_score += 3
            elif name.endswith(".py"):
                python_score += 1
            elif name in ("CMakeLists.txt", "conanfile.txt", "conanfile.py",
                          "vcpkg.json", "Makefile"):
                cpp_score += 3
            elif name.endswith((".cpp", ".hpp", ".cu", ".cuh", ".h")):
                cpp_score += 1

        elif entry.is_dir():
            # Peek one level into non-ignored subdirs
            try:
                children = list(entry.iterdir())
            except PermissionError:
                continue
            for child in children:
                if child.is_file():
                    if child.suffix == ".py":
                        python_score += 1
                    elif child.suffix in (".cpp", ".hpp", ".cu", ".cuh", ".h"):
                        cpp_score += 1

    if python_score == 0 and cpp_score == 0:
        return None

    # Tie-breaker: favor Python when scores are equal
    # This handles mixed projects (e.g., C++ with conanfile.py)
    return "python" if python_score >= cpp_score else "cpp"


def detect(repo_root: Optional[Path] = None) -> ProjectType:
    """Detect project type.  Config file wins; heuristic is fallback."""
    root = repo_root or Path.cwd()

    # 1. Authoritative config
    from_yml = _read_project_yml(root)
    if from_yml:
        return ProjectType(from_yml)

    # 2. Heuristic
    from_heuristic = _heuristic(root)
    if from_heuristic:
        return ProjectType(from_heuristic)

    return ProjectType.UNKNOWN
