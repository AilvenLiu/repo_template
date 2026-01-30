#!/usr/bin/env python3
"""Utilities for dependency management skill."""

import re
import subprocess
from enum import Enum
from pathlib import Path
from typing import List, Optional, Tuple


class ProjectType(Enum):
    """Project type enumeration."""
    PYTHON = "python"
    CPP_CUDA = "cpp_cuda"
    UNKNOWN = "unknown"


class PythonProjectType(Enum):
    """Python project type enumeration."""
    POETRY = "poetry"
    TRIVIAL = "trivial"  # Manual venv with requirements.txt
    UNKNOWN = "unknown"


class DependencyManager:
    """Manager for dependency operations."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()

    def detect_project_type(self) -> ProjectType:
        """Detect project type based on files present."""
        # Check for Python indicators
        python_indicators = [
            "pyproject.toml",
            "setup.py",
            "requirements.txt",
        ]

        cpp_indicators = [
            "CMakeLists.txt",
            "conanfile.txt",
            "conanfile.py",
        ]

        # Check for C++/CUDA
        for indicator in cpp_indicators:
            if (self.repo_root / indicator).exists():
                return ProjectType.CPP_CUDA

        # Check for Python
        for indicator in python_indicators:
            if (self.repo_root / indicator).exists():
                return ProjectType.PYTHON

        return ProjectType.UNKNOWN

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
            "conanfile.txt",
            "conanfile.py",
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

    def poetry_init(self) -> Tuple[bool, str]:
        """Initialise a new Poetry project.

        Returns (success, message).
        """
        # Use non-interactive mode
        cmd = ["poetry", "init", "--no-interaction"]
        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
            return True, stdout
        else:
            return False, stderr

    def poetry_install(self, with_dev: bool = True) -> Tuple[bool, str]:
        """Install dependencies using Poetry.

        Returns (success, message).
        """
        cmd = ["poetry", "install"]
        if with_dev:
            cmd.extend(["--with", "dev"])

        returncode, stdout, stderr = self.run_command(cmd)

        if returncode == 0:
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

    def add_to_conanfile_txt(
        self, package: str, version: Optional[str] = None
    ) -> bool:
        """Add package to conanfile.txt."""
        conan_file = self.repo_root / "conanfile.txt"

        if not conan_file.exists():
            # Create basic conanfile.txt
            conan_file.write_text("[requires]\n\n[generators]\ncmake\n")

        content = conan_file.read_text()

        # Check if package already exists
        if package in content:
            print(f"Package {package} already in conanfile.txt")
            return False

        # Find [requires] section
        requires_match = re.search(r"\[requires\]", content)
        if not requires_match:
            print("Could not find [requires] section in conanfile.txt")
            return False

        # Find next section or end of file
        next_section = re.search(r"\n\[", content[requires_match.end():])
        if next_section:
            insert_pos = requires_match.end() + next_section.start()
        else:
            insert_pos = len(content)

        # Create package line
        if version:
            new_line = f"\n{package}/{version}"
        else:
            new_line = f"\n{package}/latest"

        # Insert
        new_content = content[:insert_pos] + new_line + content[insert_pos:]
        conan_file.write_text(new_content)
        return True