#!/usr/bin/env python3
"""Utilities for pre-commit validation skill."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# Use shared detection from .ai/scripts/project_type.py
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from project_profile import (  # type: ignore[import-not-found]  # noqa: E402
    BuildSystem,
    ProjectProfile,
    detect as detect_project_profile,
)
from project_type import (  # type: ignore[import-not-found]  # noqa: E402
    ProjectType,
    detect as detect_project_type,
)


class ValidationResult:
    """Result of a validation operation."""

    def __init__(self, tool: str, passed: bool, output: str = "", error: str = ""):
        self.tool = tool
        self.passed = passed
        self.output = output
        self.error = error

    def __repr__(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.tool}"


class PreCommitManager:
    """Manager for pre-commit validation operations."""

    def __init__(self, repo_root: Path | None = None):
        self.repo_root = repo_root or Path.cwd()

    def detect_project_type(self) -> ProjectType:
        """Detect project type using shared module."""
        return detect_project_type(self.repo_root)

    def detect_project_profile(self) -> ProjectProfile:
        """Detect project profile using shared module."""
        profile = detect_project_profile(self.repo_root)
        if profile is None:
            raise ValueError("Unable to detect project profile")
        return profile

    def describe_project_type(self) -> str:
        """Return a user-facing project type label."""
        profile = self.detect_project_profile()
        if profile.is_hybrid():
            return "hybrid"
        return self.detect_project_type().value

    def python_environment_status(self, profile: ProjectProfile) -> tuple[bool, str]:
        """Check whether Python environment management is acceptable."""
        venv_paths = [".venv", "venv", ".virtualenv"]
        venv_exists = any((self.repo_root / venv).exists() for venv in venv_paths)
        poetry_lock = self.repo_root / "poetry.lock"
        pyproject = self.repo_root / "pyproject.toml"
        poetry_managed = pyproject.exists() and poetry_lock.exists()
        scikit_build_project = (
            profile.build_system in (BuildSystem.SCIKIT_BUILD, BuildSystem.SCIKIT_BUILD_CORE)
            and pyproject.exists()
        )

        if scikit_build_project:
            return True, "scikit-build-core project detected (pyproject.toml)"
        if poetry_managed:
            return True, "Poetry-managed environment detected (pyproject.toml + poetry.lock)"
        if venv_exists:
            venv_name = next(venv for venv in venv_paths if (self.repo_root / venv).exists())
            return True, f"Found virtual environment: {venv_name}"

        return (
            False,
            "No supported Python environment found.\n"
            "Use Poetry (`poetry install`) or the scikit-build-core bridge "
            "(`poetry run pip install -e . --no-build-isolation`), "
            "or create `.venv` before validating.",
        )

    def python_dependency_manifest_status(self, profile: ProjectProfile) -> tuple[bool, str]:
        """Check whether Python dependency declarations are present."""
        poetry_lock = self.repo_root / "poetry.lock"
        pyproject = self.repo_root / "pyproject.toml"
        requirements_file = self.repo_root / "requirements.txt"
        poetry_managed = pyproject.exists() and poetry_lock.exists()
        scikit_build_project = (
            profile.build_system in (BuildSystem.SCIKIT_BUILD, BuildSystem.SCIKIT_BUILD_CORE)
            and pyproject.exists()
        )

        if poetry_managed:
            return True, "Poetry lockfile exists"
        if scikit_build_project:
            return True, "pyproject.toml exists for scikit-build-core project"
        if requirements_file.exists():
            return True, "requirements.txt exists"

        return (
            False,
            "No dependency manifest found. Use Poetry (`poetry add` + `poetry lock`), "
            "a scikit-build-core `pyproject.toml`, or provide requirements.txt.",
        )

    def run_command(
        self,
        cmd: list[str],
        cwd: Path | None = None,
        timeout: int = 300,
    ) -> tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", f"Command timed out after {timeout // 60} minutes"
        except FileNotFoundError:
            return 1, "", f"Command not found: {cmd[0]}"
        except Exception as error:
            return 1, "", str(error)

    def check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available in PATH."""
        returncode, _, _ = self.run_command(["which", tool])
        return returncode == 0

    def find_python_files(self) -> list[Path]:
        """Find all Python files in the repository."""
        python_files: list[Path] = []
        for pattern in ["**/*.py"]:
            python_files.extend(self.repo_root.glob(pattern))

        # Filter out common exclusions
        exclusions = {
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".claude",
            ".codex",
            ".ai",
            "agent_roadmaps",
        }
        filtered: list[Path] = []
        for file in python_files:
            if not any(excl in file.parts for excl in exclusions):
                filtered.append(file)

        return sorted(filtered)

    def find_changed_python_files(self) -> list[Path]:
        """Find changed Python files.

        Fall back to all repository Python files only when Git inspection fails.
        When there are no changed Python files, return an empty list so non-Python
        commits do not fail on unrelated repository-wide Python debt.
        """
        changed_files: list[Path] = []

        git_commands = [
            ["git", "diff", "--name-only", "--diff-filter=ACMRTUXB", "HEAD", "--", "*.py"],
            ["git", "ls-files", "--others", "--exclude-standard", "--", "*.py"],
        ]

        for command in git_commands:
            returncode, stdout, _stderr = self.run_command(command)
            if returncode != 0:
                return self.find_python_files()

            for line in stdout.splitlines():
                if not line.strip():
                    continue

                path = self.repo_root / line.strip()
                if path.exists() and path.suffix == ".py":
                    changed_files.append(path)

        if not changed_files:
            return []

        exclusions = {
            ".venv",
            "venv",
            "__pycache__",
            ".git",
            "build",
            "dist",
            ".claude",
            ".codex",
            ".ai",
            "agent_roadmaps",
        }
        filtered: list[Path] = []
        seen: set[Path] = set()
        for file in sorted(changed_files):
            if file in seen:
                continue
            if any(excl in file.parts for excl in exclusions):
                continue
            filtered.append(file)
            seen.add(file)

        return filtered

    def find_mypy_targets(self) -> list[str]:
        """Find mypy targets scoped to changed Python files."""
        changed_python_files = self.find_changed_python_files()
        return [str(file.relative_to(self.repo_root)) for file in changed_python_files]

    def find_cpp_files(self) -> list[Path]:
        """Find all C++/CUDA files in the repository."""
        cpp_files: list[Path] = []
        for pattern in ["**/*.cpp", "**/*.hpp", "**/*.cu", "**/*.cuh", "**/*.h"]:
            cpp_files.extend(self.repo_root.glob(pattern))

        # Filter out common exclusions
        exclusions = {".git", "build", "cmake-build-*"}
        filtered: list[Path] = []
        for file in cpp_files:
            if not any(excl in file.parts for excl in exclusions):
                filtered.append(file)

        return filtered
