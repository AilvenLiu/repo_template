#!/usr/bin/env python3
"""Cross-platform constraint checks used by wrappers and CI."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    from .constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from .paths import resolve_repo_root
    from .project_type import ProjectType, detect
except ImportError:
    from constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from paths import resolve_repo_root
    from project_type import ProjectType, detect


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


def _check_python(repo_root: Path) -> List[Violation]:
    violations: List[Violation] = []

    pyproject = repo_root / "pyproject.toml"
    poetry_lock = repo_root / "poetry.lock"
    if pyproject.exists() and not poetry_lock.exists():
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
        if "python = \"^3.9\"" in text or "python = \">=3.9\"" in text:
            violations.append(
                Violation(
                    category="Dependency Management",
                    severity="CRITICAL",
                    message="Python version requirement below 3.10",
                    remediation="Set Python requirement to 3.10+.",
                )
            )

    return violations


def _check_cpp(repo_root: Path) -> List[Violation]:
    violations: List[Violation] = []

    cmake = repo_root / "CMakeLists.txt"
    has_dep_manifest = (repo_root / "conanfile.txt").exists() or (repo_root / "vcpkg.json").exists()
    if cmake.exists() and not has_dep_manifest:
        violations.append(
            Violation(
                category="Dependency Management",
                severity="CRITICAL",
                message="C++ project missing dependency manifest",
                remediation="Add conanfile.txt (preferred) or vcpkg.json.",
            )
        )

    return violations


def check_constraints(repo_root: Path, project_type: ProjectType) -> List[Violation]:
    violations = _check_git(repo_root)

    if project_type == ProjectType.PYTHON:
        violations.extend(_check_python(repo_root))
    elif project_type == ProjectType.CPP:
        violations.extend(_check_cpp(repo_root))

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
        choices=["auto", "python", "cpp"],
        default="auto",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--changed-files", nargs="*", default=[])
    args = parser.parse_args()

    repo_root = resolve_repo_root(Path(__file__).resolve())
    if args.project_type == "auto":
        project_type = detect(repo_root)
    else:
        project_type = ProjectType(args.project_type)

    violations = check_constraints(repo_root, project_type)

    if args.json:
        print(
            json.dumps(
                {
                    "project_type": project_type.value,
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
