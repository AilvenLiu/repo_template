#!/usr/bin/env python3
"""Utilities for dependency management skill."""

import re
import subprocess
import sys
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple

# Use shared detection from .agents/scripts/project_profile.py
_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from project_profile import (  # noqa: E402
    ProjectProfile,
    detect as detect_project_profile,
    BuildSystem,
)
from project_type import ProjectType  # noqa: E402  # Keep for backward compat


class PythonProjectType(Enum):
    """Python project type enumeration."""

    POETRY = "poetry"
    TRIVIAL = "trivial"  # Manual venv with requirements.txt
    UNKNOWN = "unknown"


class DependencyManager:
    """Manager for dependency operations."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()

    def detect_project_profile(self) -> ProjectProfile:
        """Detect project profile using shared module."""
        return detect_project_profile(self.repo_root)

    def detect_project_type(self) -> ProjectType:
        """Detect project type using shared module (legacy compatibility)."""
        profile = self.detect_project_profile()
        # Map profile to legacy ProjectType for backward compatibility
        if profile.build_system == BuildSystem.POETRY:
            return ProjectType.PYTHON
        elif profile.build_system == BuildSystem.CMAKE:
            return ProjectType.CPP
        elif profile.build_system in (
            BuildSystem.SCIKIT_BUILD,
            BuildSystem.SCIKIT_BUILD_CORE,
        ):
            return ProjectType.PYTHON  # Hybrid, but Python-primary
        else:
            return ProjectType.UNKNOWN

    def check_python_version(
        self, min_version: Tuple[int, int] = (3, 10)
    ) -> Tuple[bool, str, Tuple[int, int]]:
        """Check if Python version meets minimum requirement.

        Args:
            min_version: Minimum required version as (major, minor) tuple

        Returns:
            Tuple of (meets_requirement, python_executable, current_version)
        """
        # Try python3.10, python3.11, python3.12, python3.13 first
        for minor in range(10, 14):
            python_cmd = f"python3.{minor}"
            returncode, stdout, _ = self.run_command([python_cmd, "--version"])
            if returncode == 0:
                # Parse version from output like "Python 3.10.5"
                version_match = re.search(r"Python (\d+)\.(\d+)", stdout)
                if version_match:
                    major = int(version_match.group(1))
                    minor_ver = int(version_match.group(2))
                    if (major, minor_ver) >= min_version:
                        return True, python_cmd, (major, minor_ver)

        # Try python3 (system default)
        returncode, stdout, _ = self.run_command(["python3", "--version"])
        if returncode == 0:
            version_match = re.search(r"Python (\d+)\.(\d+)", stdout)
            if version_match:
                major = int(version_match.group(1))
                minor_ver = int(version_match.group(2))
                if (major, minor_ver) >= min_version:
                    return True, "python3", (major, minor_ver)
                else:
                    return False, "python3", (major, minor_ver)

        # No suitable Python found
        return False, "", (0, 0)

    def detect_python_project_type(self) -> PythonProjectType:
        """Detect Python project type (Poetry vs trivial)."""
        pyproject = self.repo_root / "pyproject.toml"

        if pyproject.exists():
            content = pyproject.read_text()
            # Check if it's a Poetry project
            if "[tool.poetry]" in content:
                return PythonProjectType.POETRY
            # Check for poetry-core in build-system
            if "poetry-core" in content or "poetry.core" in content:
                return PythonProjectType.POETRY

        # Check for requirements.txt only (trivial project)
        if (self.repo_root / "requirements.txt").exists():
            return PythonProjectType.TRIVIAL

        return PythonProjectType.UNKNOWN

    def is_poetry_available(self) -> bool:
        """Check if Poetry is installed and available."""
        returncode, _, _ = self.run_command(["poetry", "--version"])
        return returncode == 0

    def configure_poetry_in_project(self) -> Tuple[bool, str]:
        """Configure Poetry to use in-project virtual environments.

        This ensures Poetry creates .venv inside the project directory
        instead of in a centralized cache location.

        Returns:
            (success, message)
        """
        # First, try to set local configuration (creates poetry.toml in project)
        cmd = ["poetry", "config", "virtualenvs.in-project", "true", "--local"]
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            # Verify poetry.toml was created
            poetry_toml = self.repo_root / "poetry.toml"
            if poetry_toml.exists():
                return True, "Poetry configured to use in-project virtualenvs (local)"
            else:
                return True, "Poetry configured to use in-project virtualenvs"
        else:
            # Try without --local flag (global config)
            cmd = ["poetry", "config", "virtualenvs.in-project", "true"]
            returncode, stdout, stderr = self.run_command(cmd)
            if returncode == 0:
                return True, "Poetry configured globally to use in-project virtualenvs"
            else:
                return False, stderr

    def check_poetry_venv_location(self) -> Tuple[bool, Optional[Path]]:
        """Check if Poetry has an existing virtual environment and where it's located.

        Returns:
            (is_in_project, venv_path)
            - is_in_project: True if venv is in project directory, False if external
            - venv_path: Path to the venv, or None if no venv exists
        """
        # Check for in-project venv
        in_project_venv = self.repo_root / ".venv"
        if in_project_venv.exists() and (in_project_venv / "bin" / "python").exists():
            return True, in_project_venv

        # Check if Poetry knows about an external venv
        returncode, stdout, _ = self.run_command(["poetry", "env", "info", "--path"])
        if returncode == 0 and stdout.strip():
            external_venv = Path(stdout.strip())
            if external_venv.exists():
                # Check if it's actually outside the project
                try:
                    external_venv.relative_to(self.repo_root)
                    # It's inside the project (but not .venv)
                    return True, external_venv
                except ValueError:
                    # It's outside the project
                    return False, external_venv

        return True, None  # No venv exists yet

    def remove_external_poetry_venv(self) -> Tuple[bool, str]:
        """Remove Poetry's external virtual environment if it exists.

        This is needed when switching from external to in-project venvs.

        Returns:
            (success, message)
        """
        is_in_project, venv_path = self.check_poetry_venv_location()

        if venv_path is None:
            return True, "No existing virtual environment found"

        if is_in_project:
            return True, "Virtual environment is already in project"

        # External venv exists, remove it
        returncode, stdout, stderr = self.run_command(
            ["poetry", "env", "remove", "--all"]
        )
        if returncode == 0:
            return True, f"Removed external virtual environment at {venv_path}"
        else:
            return False, f"Failed to remove external venv: {stderr}"

    def get_poetry_python_version(self) -> Optional[Tuple[int, int]]:
        """Get the Python version that Poetry is using.

        Returns:
            Tuple of (major, minor) version or None if cannot determine
        """
        returncode, stdout, _ = self.run_command(
            ["poetry", "run", "python", "--version"]
        )
        if returncode == 0:
            version_match = re.search(r"Python (\d+)\.(\d+)", stdout)
            if version_match:
                return (int(version_match.group(1)), int(version_match.group(2)))
        return None

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
                timeout=300,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 5 minutes"
        except FileNotFoundError:
            return 1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return 1, "", str(e)

    def find_python_manifest_files(self) -> List[Path]:
        """Find Python dependency manifest files."""
        manifests = []
        candidates = [
            "pyproject.toml",
            "poetry.lock",
            "requirements.txt",
        ]

        for candidate in candidates:
            path = self.repo_root / candidate
            if path.exists():
                manifests.append(path)

        return manifests

    def find_cpp_manifest_files(self) -> List[Path]:
        """Find C++/CUDA dependency manifest files."""
        manifests = []
        candidates = [
            "CMakeLists.txt",
            "cmake/CPM.cmake",
            "cmake/Dependencies.cmake",
            "cmake/Options.cmake",
            "3rdparty/cpm-cache/.gitkeep",
        ]

        for candidate in candidates:
            path = self.repo_root / candidate
            if path.exists():
                manifests.append(path)

        return manifests

    def poetry_add(
        self, package: str, version: Optional[str] = None, dev: bool = False
    ) -> Tuple[bool, str]:
        """Add package using Poetry.

        Returns (success, message).
        """
        # Ensure in-project venv is configured
        self.configure_poetry_in_project()

        cmd = ["poetry", "add"]

        if dev:
            cmd.extend(["--group", "dev"])

        if version:
            cmd.append(f"{package}^{version}")
        else:
            cmd.append(package)

        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            return True, stdout
        else:
            return False, stderr

    def poetry_init(self, python_executable: str = "python3") -> Tuple[bool, str]:
        """Initialise a new Poetry project.

        Args:
            python_executable: Python executable to use for Poetry environment

        Returns:
            (success, message)
        """
        # Configure Poetry to use in-project virtualenvs
        import os

        # First, configure Poetry to create venv in project
        config_cmd = ["poetry", "config", "virtualenvs.in-project", "true"]
        try:
            subprocess.run(
                config_cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            # If config fails, continue - we'll try with env var
            pass

        # Use non-interactive mode with specific Python version
        cmd = ["poetry", "init", "--no-interaction", "--python=^3.10"]

        # Set environment to use specific Python and in-project venv
        env = os.environ.copy()
        env["POETRY_PYTHON"] = python_executable
        env["POETRY_VIRTUALENVS_IN_PROJECT"] = "true"

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_root,
                capture_output=True,
                text=True,
                timeout=300,
                env=env,
            )
            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr
        except Exception as e:
            return False, str(e)

    def poetry_install(self, with_dev: bool = True) -> Tuple[bool, str]:
        """Install dependencies using Poetry.

        Returns (success, message).
        """
        # Ensure in-project venv is configured
        self.configure_poetry_in_project()

        cmd = ["poetry", "install"]
        if with_dev:
            cmd.extend(["--with", "dev"])

        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            # Verify venv is in project
            is_in_project, venv_path = self.check_poetry_venv_location()
            if venv_path and is_in_project:
                return True, f"{stdout}\n\nVirtual environment created at: {venv_path}"
            elif venv_path:
                return (
                    True,
                    f"{stdout}\n\nWARNING: Virtual environment is at {venv_path} (not in project)",
                )
            else:
                return True, stdout
        else:
            return False, stderr

    def add_to_requirements_txt(
        self, package: str, version: Optional[str] = None
    ) -> bool:
        """Add package to requirements.txt (for trivial projects only)."""
        requirements_file = self.repo_root / "requirements.txt"

        # Create if doesn't exist
        if not requirements_file.exists():
            requirements_file.touch()

        # Read existing content
        content = requirements_file.read_text()
        lines = content.strip().split("\n") if content.strip() else []

        # Check if package already exists
        package_name = package.split("[")[0]  # Handle extras like package[extra]
        for line in lines:
            if line.strip().startswith(package_name):
                print(f"Package {package_name} already in requirements.txt")
                return False

        # Add new package
        if version:
            new_line = f"{package}>={version}"
        else:
            new_line = package

        lines.append(new_line)

        # Write back
        requirements_file.write_text("\n".join(lines) + "\n")
        return True

    def add_to_cmake(self, package: str, version: Optional[str] = None) -> bool:
        """Add package to CMakeLists.txt."""
        cmake_file = self.repo_root / "CMakeLists.txt"

        if not cmake_file.exists():
            print("CMakeLists.txt not found")
            return False

        content = cmake_file.read_text()

        # Check if package already referenced
        if package in content:
            print(f"Package {package} already in CMakeLists.txt")
            return False

        # Find appropriate location to add find_package
        # Look for other find_package calls
        find_package_pattern = r"find_package\("
        matches = list(re.finditer(find_package_pattern, content))

        if matches:
            # Add after last find_package
            last_match = matches[-1]
            insert_pos = content.find("\n", last_match.end()) + 1
        else:
            # Add after project() call
            project_pattern = r"project\([^)]+\)"
            project_match = re.search(project_pattern, content)
            if project_match:
                insert_pos = content.find("\n", project_match.end()) + 1
            else:
                # Add at beginning
                insert_pos = 0

        # Create find_package line
        if version:
            new_line = f"find_package({package} {version} REQUIRED)\n"
        else:
            new_line = f"find_package({package} REQUIRED)\n"

        # Insert
        new_content = content[:insert_pos] + new_line + content[insert_pos:]
        cmake_file.write_text(new_content)
        return True

    def add_to_cpm_dependencies(
        self,
        name: str,
        repository: str,
        tag: str,
        reason: str = "TODO: document reason",
        target: str = "TODO::target",
        license_note: str = "TODO: document license",
        scope: str = "runtime",
    ) -> bool:
        """Add a pinned CPM dependency declaration."""
        deps_file = self.repo_root / "cmake" / "Dependencies.cmake"
        deps_file.parent.mkdir(parents=True, exist_ok=True)

        if not deps_file.exists():
            deps_file.write_text(
                "set(CPM_SOURCE_CACHE\n"
                '    "${CMAKE_SOURCE_DIR}/3rdparty/cpm-cache"\n'
                '    CACHE PATH "CPM source cache")\n'
            )

        content = deps_file.read_text()
        if f"NAME {name}" in content or repository in content:
            print(f"Dependency {name} already appears in cmake/Dependencies.cmake")
            return False

        block = (
            "\n"
            f"# {name}\n"
            f"# Upstream: https://github.com/{repository}\n"
            f"# Reason: {reason}\n"
            f"# Target: {target}\n"
            f"# License: {license_note}\n"
            f"# Scope: {scope}\n"
            "CPMAddPackage(\n"
            f"  NAME {name}\n"
            f"  GITHUB_REPOSITORY {repository}\n"
            f"  GIT_TAG {tag}\n"
            ")\n"
        )

        deps_file.write_text(content.rstrip() + "\n" + block)
        return True
