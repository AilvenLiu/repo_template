#!/usr/bin/env python3
"""Utilities for pre-commit validation skill."""

import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class ProjectType(Enum):
    """Project type enumeration."""
    PYTHON = "python"
    CPP_CUDA = "cpp_cuda"
    UNKNOWN = "unknown"


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

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()

    def detect_project_type(self) -> ProjectType:
        """Detect project type based on files present."""
        # Check for Python indicators
        python_indicators = [
            "setup.py",
            "pyproject.toml",
            "requirements.txt",
            "CLAUDE.md",
        ]

        cpp_indicators = [
            "CMakeLists.txt",
            "conanfile.txt",
            "conanfile.py",
            "CLAUDE.md",
        ]

        # Check for Python
        for indicator in python_indicators:
            if (self.repo_root / indicator).exists():
                return ProjectType.PYTHON

        # Check for C++/CUDA
        for indicator in cpp_indicators:
            if (self.repo_root / indicator).exists():
                return ProjectType.CPP_CUDA

        return ProjectType.UNKNOWN

    def run_command(
        self, cmd: List[str], cwd: Optional[Path] = None
    ) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                cwd=cwd or self.repo_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 5 minutes"
        except FileNotFoundError:
            return 1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return 1, "", str(e)

    def check_tool_available(self, tool: str) -> bool:
        """Check if a tool is available in PATH."""
        returncode, _, _ = self.run_command(["which", tool])
        return returncode == 0

    def find_python_files(self) -> List[Path]:
        """Find all Python files in the repository."""
        python_files = []
        for pattern in ["**/*.py"]:
            python_files.extend(self.repo_root.glob(pattern))

        # Filter out common exclusions
        exclusions = {".venv", "venv", "__pycache__", ".git", "build", "dist"}
        filtered = []
        for file in python_files:
            if not any(excl in file.parts for excl in exclusions):
                filtered.append(file)

        return filtered

    def find_cpp_files(self) -> List[Path]:
        """Find all C++/CUDA files in the repository."""
        cpp_files = []
        for pattern in ["**/*.cpp", "**/*.hpp", "**/*.cu", "**/*.cuh", "**/*.h"]:
            cpp_files.extend(self.repo_root.glob(pattern))

        # Filter out common exclusions
        exclusions = {".git", "build", "cmake-build-*"}
        filtered = []
        for file in cpp_files:
            if not any(excl in file.parts for excl in exclusions):
                filtered.append(file)

        return filtered
