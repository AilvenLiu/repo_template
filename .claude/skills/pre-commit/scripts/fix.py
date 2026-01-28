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

    # Run black
    if manager.check_tool_available("black"):
        print("Running black...")
        returncode, stdout, stderr = manager.run_command(["black", "."])
        if returncode == 0:
            print("[OK] black formatting applied")
        else:
            print(f"[ERROR] black failed: {stderr}")
    else:
        print("[INFO] black not installed")

    # Run isort
    if manager.check_tool_available("isort"):
        print("Running isort...")
        returncode, stdout, stderr = manager.run_command(["isort", "."])
        if returncode == 0:
            print("[OK] isort applied")
        else:
            print(f"[ERROR] isort failed: {stderr}")
    else:
        print("[INFO] isort not installed")


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
    elif project_type == ProjectType.CPP_CUDA:
        fix_cpp_formatting(manager)
    else:
        print("ERROR: Unknown project type")
        print("Could not detect Python or C++/CUDA project")
        sys.exit(1)

    print()
    print("Auto-fix complete. Run validation to check results.")


if __name__ == "__main__":
    main()
