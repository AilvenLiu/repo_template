#!/usr/bin/env python3
"""Main validation orchestrator for pre-commit checks."""

import sys
from pathlib import Path
from typing import List

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import PreCommitManager, ProjectType, ValidationResult


def validate_python(manager: PreCommitManager) -> List[ValidationResult]:
    """Run Python validation checks."""
    results = []

    # CRITICAL: Check for virtual environment (dependency management)
    venv_paths = [".venv", "venv", ".virtualenv"]
    venv_exists = any((manager.repo_root / venv).exists() for venv in venv_paths)

    if venv_exists:
        venv_name = next(venv for venv in venv_paths if (manager.repo_root / venv).exists())
        results.append(
            ValidationResult(
                "virtual environment",
                True,
                f"Found virtual environment: {venv_name}",
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "virtual environment",
                False,
                "",
                "No virtual environment found. Create with: python3 -m venv .venv\n"
                "CRITICAL: NEVER install packages globally or to system Python.",
            )
        )

    # Check for requirements.txt (dependency management)
    requirements_file = manager.repo_root / "requirements.txt"
    if requirements_file.exists():
        results.append(
            ValidationResult(
                "requirements.txt",
                True,
                "requirements.txt exists",
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "requirements.txt",
                False,
                "",
                "requirements.txt not found. Create it to track dependencies.",
            )
        )

    # Check for black (formatter)
    if manager.check_tool_available("black"):
        returncode, stdout, stderr = manager.run_command(
            ["black", "--check", "--diff", "."]
        )
        results.append(
            ValidationResult(
                "black (formatter)",
                returncode == 0,
                stdout,
                stderr,
            )
        )
    else:
        results.append(
            ValidationResult(
                "black (formatter)",
                False,
                "",
                "black not installed. Install with: pip install black",
            )
        )

    # Check for isort (import sorter)
    if manager.check_tool_available("isort"):
        returncode, stdout, stderr = manager.run_command(
            ["isort", "--check-only", "--diff", "."]
        )
        results.append(
            ValidationResult(
                "isort (import sorter)",
                returncode == 0,
                stdout,
                stderr,
            )
        )
    else:
        results.append(
            ValidationResult(
                "isort (import sorter)",
                False,
                "",
                "isort not installed. Install with: pip install isort",
            )
        )

    # Check for ruff (linter)
    if manager.check_tool_available("ruff"):
        returncode, stdout, stderr = manager.run_command(["ruff", "check", "."])
        results.append(
            ValidationResult(
                "ruff (linter)",
                returncode == 0,
                stdout,
                stderr,
            )
        )
    else:
        results.append(
            ValidationResult(
                "ruff (linter)",
                False,
                "",
                "ruff not installed. Install with: pip install ruff",
            )
        )

    # Check for mypy (type checker)
    if manager.check_tool_available("mypy"):
        returncode, stdout, stderr = manager.run_command(["mypy", "."])
        results.append(
            ValidationResult(
                "mypy (type checker)",
                returncode == 0,
                stdout,
                stderr,
            )
        )
    else:
        results.append(
            ValidationResult(
                "mypy (type checker)",
                False,
                "",
                "mypy not installed. Install with: pip install mypy",
            )
        )

    # Run pytest
    if manager.check_tool_available("pytest"):
        returncode, stdout, stderr = manager.run_command(
            ["pytest", "--tb=short", "-v"]
        )
        results.append(
            ValidationResult(
                "pytest (tests)",
                returncode == 0,
                stdout,
                stderr,
            )
        )
    else:
        results.append(
            ValidationResult(
                "pytest (tests)",
                False,
                "",
                "pytest not installed. Install with: pip install pytest",
            )
        )

    return results


def validate_cpp(manager: PreCommitManager) -> List[ValidationResult]:
    """Run C++/CUDA validation checks."""
    results = []

    # CRITICAL: Check for package manager configuration (dependency management)
    conan_file = manager.repo_root / "conanfile.txt"
    vcpkg_file = manager.repo_root / "vcpkg.json"
    has_package_manager = conan_file.exists() or vcpkg_file.exists()

    if has_package_manager:
        pkg_mgr = "conanfile.txt" if conan_file.exists() else "vcpkg.json"
        results.append(
            ValidationResult(
                "package manager",
                True,
                f"Found package manager configuration: {pkg_mgr}",
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "package manager",
                False,
                "",
                "No package manager configuration found (conanfile.txt or vcpkg.json).\n"
                "CRITICAL: NEVER install C++ libraries system-wide (apt, yum, brew).\n"
                "Create conanfile.txt or vcpkg.json for dependency management.",
            )
        )

    # Check for clang-format
    cpp_files = manager.find_cpp_files()
    if manager.check_tool_available("clang-format"):
        if cpp_files:
            # Check formatting
            all_formatted = True
            output_lines = []
            for file in cpp_files:
                returncode, stdout, stderr = manager.run_command(
                    ["clang-format", "--dry-run", "-Werror", str(file)]
                )
                if returncode != 0:
                    all_formatted = False
                    output_lines.append(f"Formatting issues in {file}")
                    if stderr:
                        output_lines.append(stderr)

            results.append(
                ValidationResult(
                    "clang-format (formatter)",
                    all_formatted,
                    "\n".join(output_lines) if output_lines else "All files formatted correctly",
                    "",
                )
            )
        else:
            results.append(
                ValidationResult(
                    "clang-format (formatter)",
                    True,
                    "No C++ files found",
                    "",
                )
            )
    else:
        results.append(
            ValidationResult(
                "clang-format (formatter)",
                False,
                "",
                "clang-format not installed",
            )
        )

    # Check for clang-tidy
    if manager.check_tool_available("clang-tidy"):
        if cpp_files:
            returncode, stdout, stderr = manager.run_command(
                ["clang-tidy"] + [str(f) for f in cpp_files[:10]]  # Limit to first 10 files
            )
            results.append(
                ValidationResult(
                    "clang-tidy (linter)",
                    returncode == 0,
                    stdout,
                    stderr,
                )
            )
        else:
            results.append(
                ValidationResult(
                    "clang-tidy (linter)",
                    True,
                    "No C++ files found",
                    "",
                )
            )
    else:
        results.append(
            ValidationResult(
                "clang-tidy (linter)",
                False,
                "",
                "clang-tidy not installed",
            )
        )

    # Check for cppcheck
    if manager.check_tool_available("cppcheck"):
        if cpp_files:
            returncode, stdout, stderr = manager.run_command(
                ["cppcheck", "--enable=all", "--error-exitcode=1", "."]
            )
            results.append(
                ValidationResult(
                    "cppcheck (static analyser)",
                    returncode == 0,
                    stdout,
                    stderr,
                )
            )
        else:
            results.append(
                ValidationResult(
                    "cppcheck (static analyser)",
                    True,
                    "No C++ files found",
                    "",
                )
            )
    else:
        results.append(
            ValidationResult(
                "cppcheck (static analyser)",
                False,
                "",
                "cppcheck not installed",
            )
        )

    # Check for CMake build
    if (manager.repo_root / "CMakeLists.txt").exists():
        build_dir = manager.repo_root / "build"
        if build_dir.exists():
            returncode, stdout, stderr = manager.run_command(
                ["cmake", "--build", "build"], cwd=manager.repo_root
            )
            results.append(
                ValidationResult(
                    "cmake build",
                    returncode == 0,
                    stdout,
                    stderr,
                )
            )
        else:
            results.append(
                ValidationResult(
                    "cmake build",
                    False,
                    "",
                    "Build directory not found. Run: cmake -B build",
                )
            )

    return results


def main():
    """Main entry point for validation."""
    repo_root = Path.cwd()
    manager = PreCommitManager(repo_root)

    # Detect project type
    project_type = manager.detect_project_type()

    print("Pre-Commit Validation")
    print("=" * 50)
    print(f"Project Type: {project_type.value}")
    print()

    # Run appropriate validations
    results = []
    if project_type == ProjectType.PYTHON:
        results = validate_python(manager)
    elif project_type == ProjectType.CPP_CUDA:
        results = validate_cpp(manager)
    else:
        print("ERROR: Unknown project type")
        print("Could not detect Python or C++/CUDA project")
        sys.exit(1)

    # Display results
    print("Validation Results:")
    print("-" * 50)
    passed_count = 0
    failed_count = 0

    for result in results:
        print(result)
        if result.passed:
            passed_count += 1
        else:
            failed_count += 1

    print()
    print(f"Passed: {passed_count}/{len(results)}")
    print(f"Failed: {failed_count}/{len(results)}")

    # Show detailed errors
    if failed_count > 0:
        print()
        print("Detailed Errors:")
        print("-" * 50)
        for result in results:
            if not result.passed:
                print(f"\n{result.tool}:")
                if result.error:
                    print(f"  Error: {result.error}")
                if result.output:
                    print(f"  Output: {result.output[:500]}")  # Limit output

    # Exit with appropriate code
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
