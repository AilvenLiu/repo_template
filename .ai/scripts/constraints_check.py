#!/usr/bin/env python3
"""Cross-platform constraint checks used by wrappers and CI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    from .constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from .paths import resolve_repo_root
    from .project_profile import BuildSystem, Language, ProjectProfile, detect
except ImportError:
    from constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from paths import resolve_repo_root
    from project_profile import BuildSystem, Language, ProjectProfile, detect


@dataclass
class Violation:
    category: str
    severity: str
    message: str
    remediation: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
        }


def _run(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def _current_branch(repo_root: Path) -> str:
    proc = _run(["git", "branch", "--show-current"], repo_root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _is_protected_branch(branch: str) -> bool:
    return branch in PROTECTED_BRANCHES or any(
        branch.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def _check_git(repo_root: Path) -> List[Violation]:
    violations: List[Violation] = []
    branch = _current_branch(repo_root)
    if branch and _is_protected_branch(branch):
        violations.append(
            Violation(
                category="Git Workflow",
                severity="CRITICAL",
                message=f"On protected branch: {branch}",
                remediation="Create a feature branch before committing.",
            )
        )
    return violations


def _check_python(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations: List[Violation] = []

    pyproject = repo_root / "pyproject.toml"
    poetry_lock = repo_root / "poetry.lock"
    if (
        profile.build_system == BuildSystem.POETRY
        and pyproject.exists()
        and not poetry_lock.exists()
    ):
        violations.append(
            Violation(
                category="Dependency Management",
                severity="CRITICAL",
                message="Poetry project missing poetry.lock",
                remediation="Run `poetry lock` and commit poetry.lock.",
            )
        )

    if pyproject.exists():
        text = pyproject.read_text()
        if 'python = "^3.9"' in text or 'python = ">=3.9"' in text:
            violations.append(
                Violation(
                    category="Dependency Management",
                    severity="CRITICAL",
                    message="Python version requirement below 3.10",
                    remediation="Set Python requirement to 3.10+.",
                )
            )

    return violations


def _check_cpp(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations: List[Violation] = []

    cmake = repo_root / "CMakeLists.txt"
    cpm_files = [
        repo_root / "cmake" / "CPM.cmake",
        repo_root / "cmake" / "Dependencies.cmake",
        repo_root / "cmake" / "Options.cmake",
        repo_root / "3rdparty" / "cpm-cache" / ".gitkeep",
    ]
    missing = [path for path in cpm_files if not path.exists()]
    if cmake.exists() and profile.has_language(Language.CPP) and missing:
        violations.append(
            Violation(
                category="Dependency Management",
                severity="CRITICAL",
                message="C++ project missing CMake/CPM dependency layout",
                remediation=(
                    "Add cmake/CPM.cmake, cmake/Dependencies.cmake, "
                    "cmake/Options.cmake, and 3rdparty/cpm-cache/.gitkeep."
                ),
            )
        )

    return violations


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _check_native_build_ownership(
    repo_root: Path, profile: ProjectProfile
) -> List[Violation]:
    violations: List[Violation] = []
    if not profile.has_language(Language.CPP):
        return violations

    cmake = repo_root / "CMakeLists.txt"
    if not cmake.exists():
        violations.append(
            Violation(
                category="Native Build Ownership",
                severity="CRITICAL",
                message="C++/CUDA profile has no root CMakeLists.txt",
                remediation="Restore CMake as the native build authority before editing Python packaging.",
            )
        )

    setup_py = repo_root / "setup.py"
    if setup_py.exists():
        text = _read_text(setup_py)
        native_setup_patterns = [
            r"\bsetuptools\s*\.\s*Extension\s*\(",
            r"\bExtension\s*\(",
            r"\bCUDAExtension\s*\(",
            r"\bCppExtension\s*\(",
            r"\bBuildExtension\b",
            r"\bextra_compile_args\b",
            r"\bextra_link_args\b",
            r"\bdefine_macros\b",
            r"\blibrary_dirs\b",
            r"\binclude_dirs\b",
        ]
        if any(re.search(pattern, text) for pattern in native_setup_patterns):
            violations.append(
                Violation(
                    category="Native Build Ownership",
                    severity="CRITICAL",
                    message="setup.py appears to define native C++/CUDA build logic",
                    remediation=(
                        "Move native targets, compiler/link flags, CUDA policy, and dependency "
                        "discovery into CMake; keep Python packaging as a thin bridge."
                    ),
                )
            )

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        text = _read_text(pyproject)
        if re.search(r'build-backend\s*=\s*["\']setuptools\.build_meta', text):
            native_markers = [
                "tool.setuptools",
                "ext_modules",
                "Extension(",
                "CUDAExtension",
                "CppExtension",
            ]
            if any(marker in text for marker in native_markers):
                violations.append(
                    Violation(
                        category="Native Build Ownership",
                        severity="CRITICAL",
                        message="pyproject.toml routes native extension building through setuptools",
                        remediation="Use scikit-build-core only as a bridge to the CMake-owned native graph.",
                    )
                )

        python_owned_native_policy = [
            "CMAKE_CUDA_ARCHITECTURES",
            "CUDA_ARCHITECTURES",
            "TORCH_CUDA_ARCH_LIST",
            "extra_compile_args",
            "extra_link_args",
            "define_macros",
            "library_dirs",
            "include_dirs",
        ]
        if any(marker in text for marker in python_owned_native_policy):
            violations.append(
                Violation(
                    category="Native Build Ownership",
                    severity="CRITICAL",
                    message="pyproject.toml appears to own native compiler/link/CUDA policy",
                    remediation=(
                        "Define native compiler flags, link flags, CUDA architectures, and "
                        "dependency discovery in CMake instead of Python packaging metadata."
                    ),
                )
            )

    return violations


def check_constraints(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations = _check_git(repo_root)

    if profile.has_language(Language.PYTHON):
        violations.extend(_check_python(repo_root, profile))
    if profile.has_language(Language.CPP):
        violations.extend(_check_cpp(repo_root, profile))
        violations.extend(_check_native_build_ownership(repo_root, profile))

    return violations


def print_report(violations: List[Violation]) -> None:
    if not violations:
        print("No critical constraint violations detected.")
        return

    print("=" * 70)
    print("CONSTRAINT VIOLATIONS")
    print("=" * 70)
    for violation in violations:
        print(f"[{violation.severity}] {violation.category}: {violation.message}")
        print(f"  Remediation: {violation.remediation}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Constraint checker")
    parser.add_argument(
        "--project-type",
        choices=["auto", "python", "cpp", "hybrid"],
        default="auto",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--changed-files", nargs="*", default=[])
    args = parser.parse_args()

    repo_root = resolve_repo_root(Path(__file__).resolve())
    if args.project_type == "auto":
        profile = detect(repo_root)
    else:
        if args.project_type == "python":
            profile = ProjectProfile(
                language=[Language.PYTHON], build_system=BuildSystem.POETRY
            )
        elif args.project_type == "cpp":
            profile = ProjectProfile(
                language=[Language.CPP], build_system=BuildSystem.CMAKE
            )
        else:
            profile = ProjectProfile(
                language=[Language.PYTHON, Language.CPP],
                build_system=BuildSystem.SCIKIT_BUILD_CORE,
            )

    if profile is None:
        print("ERROR: Could not detect project profile")
        sys.exit(1)

    violations = check_constraints(repo_root, profile)

    if args.json:
        print(
            json.dumps(
                {
                    "project_type": "hybrid"
                    if profile.is_hybrid()
                    else profile.language[0].value,
                    "violations": [v.to_dict() for v in violations],
                },
                indent=2,
            )
        )
    else:
        print_report(violations)

    critical = [v for v in violations if v.severity == "CRITICAL"]
    sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main()
