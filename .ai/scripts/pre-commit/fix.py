#!/usr/bin/env python3
"""Auto-fix formatting issues."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import PreCommitManager, ProjectType


def fix_python_formatting(manager: PreCommitManager) -> None:
    """Auto-fix Python formatting issues."""
    print("Fixing Python formatting...")
    print("-" * 50)
    python_files = manager.find_python_files()
    file_args = [str(file.relative_to(manager.repo_root)) for file in python_files]

    if not file_args:
        print("No project Python files found")
        return

    # Run ruff (format + lint auto-fix; covers import order via the I rule)
    if manager.check_tool_available("ruff"):
        print("Running ruff format...")
        returncode, _stdout, stderr = manager.run_command(["ruff", "format"] + file_args)
        if returncode == 0:
            print("[OK] ruff format applied")
        else:
            print(f"[ERROR] ruff format failed: {stderr}")

        print("Running ruff check --fix...")
        returncode, _stdout, stderr = manager.run_command(
            ["ruff", "check", "--fix"] + file_args
        )
        if returncode == 0:
            print("[OK] ruff check --fix applied")
        else:
            print(f"[ERROR] ruff check --fix failed: {stderr}")
    else:
        print("[INFO] ruff not installed")


def fix_cpp_formatting(manager: PreCommitManager) -> None:
    """Auto-fix C++/CUDA formatting issues."""
    print("Fixing C++/CUDA formatting...")
    print("-" * 50)

    cpp_files = manager.find_cpp_files()
    if not cpp_files:
        print("No C++ files found")
        return

    # Run clang-format
    if manager.check_tool_available("clang-format"):
        print(f"Running clang-format on {len(cpp_files)} files...")
        for file in cpp_files:
            returncode, stdout, stderr = manager.run_command(
                ["clang-format", "-i", str(file)]
            )
            if returncode != 0:
                print(f"[ERROR] Failed to format {file}: {stderr}")
        print("[OK] clang-format applied")
    else:
        print("[INFO] clang-format not installed")


def main():
    """Main entry point for fix command."""
    repo_root = Path.cwd()
    manager = PreCommitManager(repo_root)

    # Detect project type
    project_type = manager.detect_project_type()

    print("Pre-Commit Auto-Fix")
    print("=" * 50)
    print(f"Project Type: {project_type.value}")
    print()

    # Run appropriate fixes
    if project_type == ProjectType.PYTHON:
        fix_python_formatting(manager)
    elif project_type == ProjectType.CPP:
        fix_cpp_formatting(manager)
    else:
        print("ERROR: Unknown project type")
        print("Could not detect Python or C++/CUDA project")
        sys.exit(1)

    print()
    print("Auto-fix complete. Run validation to check results.")


if __name__ == "__main__":
    main()
