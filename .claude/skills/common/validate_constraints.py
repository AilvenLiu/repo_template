#!/usr/bin/env python3
"""
Runtime constraint validation utility.
Checks for common constraint violations.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict


class ConstraintViolation:
    def __init__(self, category: str, severity: str, message: str,
                 detail: str, remediation: str):
        self.category = category
        self.severity = severity
        self.message = message
        self.detail = detail
        self.remediation = remediation

    def __str__(self):
        return (
            f"[{self.severity}] {self.category}: {self.message}\n"
            f"  Detail: {self.detail}\n"
            f"  Remediation: {self.remediation}"
        )


def check_python_dependency_constraints() -> List[ConstraintViolation]:
    """Check Python dependency management constraints."""
    violations = []

    # Check 1: Virtual environment exists
    if not os.path.exists('.venv') and not os.path.exists('poetry.lock'):
        violations.append(ConstraintViolation(
            category='Dependency Management',
            severity='CRITICAL',
            message='No virtual environment or Poetry detected',
            detail='System Python usage is FORBIDDEN',
            remediation='Run: poetry init --python=^3.10'
        ))

    # Check 2: Poetry lock file exists if pyproject.toml exists
    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml') as f:
            content = f.read()
            if '[tool.poetry]' in content or 'poetry-core' in content:
                if not os.path.exists('poetry.lock'):
                    violations.append(ConstraintViolation(
                        category='Dependency Management',
                        severity='CRITICAL',
                        message='Poetry project missing poetry.lock',
                        detail='Lock file is MANDATORY for reproducibility',
                        remediation='Run: poetry lock'
                    ))

    # Check 3: Python version requirement
    if os.path.exists('pyproject.toml'):
        with open('pyproject.toml') as f:
            content = f.read()
            if 'python = "^3.9"' in content or 'python = ">=3.9"' in content:
                violations.append(ConstraintViolation(
                    category='Dependency Management',
                    severity='CRITICAL',
                    message='Python version requirement too low',
                    detail='Python 3.10+ is MANDATORY for Poetry projects',
                    remediation='Update pyproject.toml: python = "^3.10"'
                ))

    return violations


def check_git_workflow_constraints() -> List[ConstraintViolation]:
    """Check git workflow constraints."""
    violations = []

    try:
        # Check current branch
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            capture_output=True,
            text=True,
            check=True
        )
        branch = result.stdout.strip()

        # Check if on protected branch
        protected_branches = ['master', 'main', 'develop']
        if branch in protected_branches:
            violations.append(ConstraintViolation(
                category='Git Workflow',
                severity='CRITICAL',
                message=f'On protected branch: {branch}',
                detail='Direct commits to protected branches are FORBIDDEN',
                remediation=f'Create feature branch: git checkout -b feature/your-feature'
            ))

    except subprocess.CalledProcessError:
        pass  # Not a git repository

    return violations


def validate_all_constraints() -> List[ConstraintViolation]:
    """Run all constraint validations."""
    all_violations = []

    # Determine project type
    if os.path.exists('pyproject.toml') or os.path.exists('requirements.txt'):
        all_violations.extend(check_python_dependency_constraints())

    all_violations.extend(check_git_workflow_constraints())

    return all_violations


def print_violations(violations: List[ConstraintViolation]):
    """Print violations in formatted output."""
    if not violations:
        print("✓ No constraint violations detected")
        return

    print("=" * 70)
    print("CONSTRAINT VIOLATIONS DETECTED")
    print("=" * 70)
    print()

    critical = [v for v in violations if v.severity == 'CRITICAL']
    warnings = [v for v in violations if v.severity == 'WARNING']

    if critical:
        print(f"CRITICAL VIOLATIONS: {len(critical)}")
        print("-" * 70)
        for v in critical:
            print(str(v))
            print()

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        print("-" * 70)
        for v in warnings:
            print(str(v))
            print()

    print("=" * 70)
    print(f"Total violations: {len(violations)}")
    print("=" * 70)


if __name__ == '__main__':
    violations = validate_all_constraints()
    print_violations(violations)

    # Exit with error code if critical violations found
    critical_count = sum(1 for v in violations if v.severity == 'CRITICAL')
    if critical_count > 0:
        exit(1)
