#!/usr/bin/env python3
"""Main validation orchestrator for pre-commit checks."""

from __future__ import annotations

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from check_session import (  # type: ignore[import-not-found]  # noqa: E402  # isort: skip
    check_session_initialized,
)
from validate_constraints import (  # type: ignore[import-not-found]  # noqa: E402  # isort: skip
    print_violations,
    validate_all_constraints,
)

# Check session initialization
session_state = check_session_initialized("pre-commit")

from utils import PreCommitManager, ProjectType, ValidationResult  # noqa: E402  # isort: skip


def _emit(message: str = "") -> None:
    """Write a single console line."""
    sys.stdout.write(f"{message}\n")


def validate_python(manager: PreCommitManager) -> list[ValidationResult]:
    """Run Python validation checks."""
    results: list[ValidationResult] = []

    profile = manager.detect_project_profile()
    env_ok, env_message = manager.python_environment_status(profile)
    if env_ok:
        results.append(
            ValidationResult(
                "python environment",
                True,
                env_message,
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "python environment",
                False,
                "",
                env_message,
            )
        )

    manifest_ok, manifest_message = manager.python_dependency_manifest_status(profile)
    if manifest_ok:
        results.append(
            ValidationResult(
                "dependency manifest",
                True,
                manifest_message,
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "dependency manifest",
                False,
                "",
                manifest_message,
            )
        )

    python_files = manager.find_changed_python_files()
    file_args = [str(file.relative_to(manager.repo_root)) for file in python_files]

    # Check for ruff (formatter + linter + import sorter)
    if manager.check_tool_available("ruff"):
        if file_args:
            returncode, stdout, stderr = manager.run_command(
                ["ruff", "format", "--check", "--diff"] + file_args
            )
            results.append(
                ValidationResult(
                    "ruff format (formatter)",
                    returncode == 0,
                    stdout,
                    stderr,
                )
            )

            returncode, stdout, stderr = manager.run_command(
                ["ruff", "check"] + file_args
            )
            results.append(
                ValidationResult(
                    "ruff check (linter + import order)",
                    returncode == 0,
                    stdout,
                    stderr,
                )
            )
        else:
            results.append(
                ValidationResult(
                    "ruff format (formatter)",
                    True,
                    "No project Python files found",
                    "",
                )
            )
            results.append(
                ValidationResult(
                    "ruff check (linter + import order)",
                    True,
                    "No project Python files found",
                    "",
                )
            )
    else:
        results.append(
            ValidationResult(
                "ruff format (formatter)",
                False,
                "",
                "ruff not installed. Add it with: .agents/bin/agent-dependency add ruff --dev",
            )
        )
        results.append(
            ValidationResult(
                "ruff check (linter + import order)",
                False,
                "",
                "ruff not installed. Add it with: .agents/bin/agent-dependency add ruff --dev",
            )
        )

    # Check for mypy (type checker)
    if manager.check_tool_available("mypy"):
        mypy_targets = manager.find_mypy_targets()
        if mypy_targets:
            mypy_cmd = ["mypy"]
            if (manager.repo_root / "src").exists() and any(
                target.startswith("src/") for target in mypy_targets
            ):
                mypy_cmd.extend(["--namespace-packages", "--explicit-package-bases"])
            returncode, stdout, stderr = manager.run_command(mypy_cmd + mypy_targets)
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
                    True,
                    "No project Python files found",
                    "",
                )
            )
    else:
        results.append(
            ValidationResult(
                "mypy (type checker)",
                False,
                "",
                "mypy not installed. Add it with: .agents/bin/agent-dependency add mypy --dev",
            )
        )

    # Run pytest
    if manager.check_tool_available("pytest"):
        returncode, stdout, stderr = manager.run_command(
            ["pytest", "--tb=short", "-q", "-x"],
            timeout=600,
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
                "pytest not installed. Add it with: .agents/bin/agent-dependency add pytest --dev",
            )
        )

    return results


def validate_cpp(manager: PreCommitManager) -> list[ValidationResult]:
    """Run C++/CUDA validation checks."""
    results: list[ValidationResult] = []

    # CRITICAL: Check for CMake/CPM dependency layout.
    cpm_files = [
        manager.repo_root / "cmake" / "CPM.cmake",
        manager.repo_root / "cmake" / "Dependencies.cmake",
        manager.repo_root / "cmake" / "Options.cmake",
        manager.repo_root / "3rdparty" / "cpm-cache" / ".gitkeep",
    ]
    missing_cpm_files = [path for path in cpm_files if not path.exists()]

    if not missing_cpm_files:
        results.append(
            ValidationResult(
                "CMake/CPM dependency layout",
                True,
                "Found cmake/CPM.cmake, cmake/Dependencies.cmake, "
                "cmake/Options.cmake, and 3rdparty/cpm-cache/.gitkeep",
                "",
            )
        )
    else:
        results.append(
            ValidationResult(
                "CMake/CPM dependency layout",
                False,
                "",
                "Missing CMake/CPM dependency layout files:\n"
                + "\n".join(
                    f"  - {path.relative_to(manager.repo_root)}"
                    for path in missing_cpm_files
                )
                + "\nCRITICAL: CMake owns the native build graph and CPM owns "
                "lightweight C++ dependency acquisition.",
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
                    "\n".join(output_lines)
                    if output_lines
                    else "All files formatted correctly",
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
                ["clang-tidy"]
                + [str(f) for f in cpp_files[:10]]  # Limit to first 10 files
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
                    "Build directory not found. Run: "
                    "cmake -S . -B build -G Ninja "
                    "-DCMAKE_BUILD_TYPE=RelWithDebInfo",
                )
            )

    return results


def main() -> None:
    """Main entry point for validation."""
    repo_root = Path.cwd()
    manager = PreCommitManager(repo_root)

    # Detect project type
    profile = manager.detect_project_profile()
    project_type = manager.detect_project_type()
    project_label = manager.describe_project_type()

    _emit("Pre-Commit Validation")
    _emit("=" * 50)
    _emit(f"Project Type: {project_label}")
    _emit()

    # Run constraint validation first
    _emit("=" * 50)
    _emit("CONSTRAINT VALIDATION")
    _emit("=" * 50)
    _emit()

    constraint_violations = validate_all_constraints()
    print_violations(constraint_violations)

    # If critical constraint violations, fail immediately
    critical = [
        violation
        for violation in constraint_violations
        if violation.severity == "CRITICAL"
    ]
    if critical:
        _emit()
        _emit("=" * 50)
        _emit("FAILED: Critical constraint violations must be fixed before committing")
        _emit("=" * 50)
        sys.exit(1)

    _emit()

    # Run appropriate validations
    results: list[ValidationResult] = []
    if profile.is_hybrid():
        results = validate_python(manager)
        results.extend(validate_cpp(manager))
    elif project_type == ProjectType.PYTHON:
        results = validate_python(manager)
    elif project_type == ProjectType.CPP:
        results = validate_cpp(manager)
    else:
        _emit("ERROR: Unknown project type")
        _emit(
            "Could not detect a supported project profile (Python, C++/CUDA, or hybrid)"
        )
        sys.exit(1)

    # Display results
    _emit("Validation Results:")
    _emit("-" * 50)
    passed_count = 0
    failed_count = 0

    for result in results:
        _emit(str(result))
        if result.passed:
            passed_count += 1
        else:
            failed_count += 1

    _emit()
    _emit(f"Passed: {passed_count}/{len(results)}")
    _emit(f"Failed: {failed_count}/{len(results)}")

    # Show detailed errors
    if failed_count > 0:
        _emit()
        _emit("Detailed Errors:")
        _emit("-" * 50)
        for result in results:
            if not result.passed:
                _emit(f"\n{result.tool}:")
                if result.error:
                    _emit(f"  Error: {result.error}")
                if result.output:
                    _emit(f"  Output: {result.output[:500]}")

    # Exit with appropriate code
    sys.exit(0 if failed_count == 0 else 1)


if __name__ == "__main__":
    main()
