#!/usr/bin/env python3
"""Diagnose pyenv+Poetry environment configuration issues."""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Tuple

class Issue:
    """Represents an environment issue."""

    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"
    OK = "OK"

    def __init__(self, severity: str, message: str, details: str = "", fix: str = ""):
        self.severity = severity
        self.message = message
        self.details = details
        self.fix = fix

    def __str__(self) -> str:
        result = f"[{self.severity}] {self.message}"
        if self.details:
            result += f"\n  {self.details}"
        if self.fix:
            result += f"\n  Fix: {self.fix}"
        return result


class EnvironmentDiagnostics:
    """Diagnose Python environment configuration."""

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        self.issues: List[Issue] = []

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out"
        except FileNotFoundError:
            return 1, "", f"Command not found: {cmd[0]}"
        except Exception as e:
            return 1, "", str(e)

    def check_virtual_env_variable(self) -> None:
        """Check if VIRTUAL_ENV environment variable is set."""
        virtual_env = os.environ.get("VIRTUAL_ENV")
        if virtual_env:
            self.issues.append(Issue(
                severity=Issue.CRITICAL,
                message="VIRTUAL_ENV is set to system Python",
                details=f"Current value: {virtual_env}\n  Impact: Poetry will always detect the system Python instead of pyenv Python",
                fix='unset VIRTUAL_ENV && echo "unset VIRTUAL_ENV" >> ~/.zshrc'
            ))
        else:
            self.issues.append(Issue(
                severity=Issue.OK,
                message="VIRTUAL_ENV is not set"
            ))

    def check_python_versions(self) -> None:
        """Check Python versions (system, required, Poetry)."""
        # Check system Python
        returncode, stdout, _ = self.run_command(["python3", "--version"])
        system_python = None
        if returncode == 0:
            match = re.search(r"Python (\d+\.\d+\.\d+)", stdout)
            if match:
                system_python = match.group(1)

        # Check required Python from pyproject.toml
        required_python = None
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'python\s*=\s*"([^"]+)"', content)
            if match:
                required_python = match.group(1)

        # Check Poetry's Python
        poetry_python = None
        returncode, stdout, _ = self.run_command(["poetry", "env", "info"])
        if returncode == 0:
            match = re.search(r"Python:\s+(\d+\.\d+\.\d+)", stdout)
            if match:
                poetry_python = match.group(1)

        # Check pyenv Python
        pyenv_python = None
        returncode, stdout, _ = self.run_command(["pyenv", "version"])
        if returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", stdout)
            if match:
                pyenv_python = match.group(1)

        # Analyze versions
        if poetry_python and required_python:
            # Check if Poetry's Python matches requirements
            if not self._version_matches_constraint(poetry_python, required_python):
                self.issues.append(Issue(
                    severity=Issue.WARNING,
                    message="Poetry detects wrong Python version",
                    details=f"Poetry Python: {poetry_python}\n  Required: {required_python}\n  pyenv Python: {pyenv_python or 'not installed'}",
                    fix="Remove Poetry venv and recreate with correct Python"
                ))
            else:
                self.issues.append(Issue(
                    severity=Issue.OK,
                    message=f"Poetry Python version matches requirements ({poetry_python})"
                ))

    def _version_matches_constraint(self, version: str, constraint: str) -> bool:
        """Check if version matches constraint (simplified)."""
        # Remove ^ and ~ prefixes
        constraint = constraint.lstrip("^~")

        # Extract major.minor from both
        version_parts = version.split(".")[:2]
        constraint_parts = constraint.split(".")[:2]

        try:
            version_major_minor = tuple(int(p) for p in version_parts)
            constraint_major_minor = tuple(int(p) for p in constraint_parts)
            return version_major_minor >= constraint_major_minor
        except (ValueError, IndexError):
            return False

    def check_pyenv(self) -> None:
        """Check pyenv installation and configuration."""
        # Check if pyenv is installed
        returncode, stdout, _ = self.run_command(["pyenv", "--version"])
        if returncode != 0:
            self.issues.append(Issue(
                severity=Issue.WARNING,
                message="pyenv is not installed",
                fix="Install pyenv: curl https://pyenv.run | bash"
            ))
            return

        # pyenv is installed
        pyenv_version = stdout

        # Check if pyenv is in PATH
        returncode, stdout, _ = self.run_command(["which", "pyenv"])
        if returncode == 0:
            pyenv_path = stdout
        else:
            pyenv_path = "not in PATH"

        # Check if pyenv shims are in PATH
        path_env = os.environ.get("PATH", "")
        if ".pyenv/shims" in path_env:
            shims_in_path = True
        else:
            shims_in_path = False

        if not shims_in_path:
            self.issues.append(Issue(
                severity=Issue.WARNING,
                message="pyenv shims not in PATH",
                details="pyenv is installed but not properly initialized",
                fix='Add to ~/.zshrc: eval "$(pyenv init -)"'
            ))
        else:
            self.issues.append(Issue(
                severity=Issue.OK,
                message=f"pyenv is installed and configured\n  Version: {pyenv_version}\n  Path: {pyenv_path}"
            ))

    def check_poetry(self) -> None:
        """Check Poetry installation and configuration."""
        # Check if Poetry is installed
        returncode, stdout, _ = self.run_command(["poetry", "--version"])
        if returncode != 0:
            self.issues.append(Issue(
                severity=Issue.WARNING,
                message="Poetry is not installed",
                fix="Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
            ))
            return

        poetry_version = stdout

        # Check Poetry's Python
        returncode, stdout, _ = self.run_command(["poetry", "debug", "info"])
        if returncode == 0:
            match = re.search(r"Python:\s+(\d+\.\d+\.\d+)", stdout)
            if match:
                poetry_python = match.group(1)
                self.issues.append(Issue(
                    severity=Issue.INFO,
                    message=f"Poetry is installed\n  Version: {poetry_version}\n  Python: {poetry_python}"
                ))

        # Check Poetry venv location
        returncode, stdout, _ = self.run_command(["poetry", "env", "info", "--path"])
        if returncode == 0 and stdout:
            venv_path = Path(stdout)
            try:
                venv_path.relative_to(self.repo_root)
                in_project = True
            except ValueError:
                in_project = False

            if not in_project:
                self.issues.append(Issue(
                    severity=Issue.INFO,
                    message="Poetry venv is outside project directory",
                    details=f"Location: {venv_path}",
                    fix="poetry config virtualenvs.in-project true --local"
                ))

    def check_path_order(self) -> None:
        """Check PATH order to ensure pyenv shims come first."""
        path_env = os.environ.get("PATH", "")
        path_parts = path_env.split(":")

        pyenv_shim_index = None
        system_python_index = None

        for i, part in enumerate(path_parts):
            if ".pyenv/shims" in part and pyenv_shim_index is None:
                pyenv_shim_index = i
            if "/usr/bin" in part or "/usr/local/bin" in part:
                if system_python_index is None:
                    system_python_index = i

        if pyenv_shim_index is not None:
            if system_python_index is None or pyenv_shim_index < system_python_index:
                self.issues.append(Issue(
                    severity=Issue.OK,
                    message="pyenv shims are prioritized in PATH"
                ))
            else:
                self.issues.append(Issue(
                    severity=Issue.WARNING,
                    message="System Python comes before pyenv in PATH",
                    fix="Ensure pyenv init is called in ~/.zshrc before other PATH modifications"
                ))

    def diagnose(self) -> List[Issue]:
        """Run all diagnostic checks."""
        print("=" * 70)
        print("PYTHON ENVIRONMENT DIAGNOSTICS")
        print("=" * 70)
        print()

        self.check_virtual_env_variable()
        self.check_python_versions()
        self.check_pyenv()
        self.check_poetry()
        self.check_path_order()

        return self.issues

    def print_report(self) -> None:
        """Print diagnostic report."""
        for issue in self.issues:
            print(issue)
            print()

        # Summary
        critical_count = sum(1 for i in self.issues if i.severity == Issue.CRITICAL)
        warning_count = sum(1 for i in self.issues if i.severity == Issue.WARNING)

        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Critical issues: {critical_count}")
        print(f"Warnings: {warning_count}")

        if critical_count > 0:
            print("Status: ENVIRONMENT NEEDS CRITICAL FIXES")
        elif warning_count > 0:
            print("Status: ENVIRONMENT NEEDS FIXES")
        else:
            print("Status: ENVIRONMENT OK")

        # Recommendations
        if critical_count > 0 or warning_count > 0:
            print()
            print("RECOMMENDED ACTIONS:")
            action_num = 1
            for issue in self.issues:
                if issue.severity in (Issue.CRITICAL, Issue.WARNING) and issue.fix:
                    print(f"{action_num}. {issue.fix}")
                    action_num += 1
            print()
            print("Run: python3 .claude/skills/python-env-setup/scripts/fix.py")

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(i.severity == Issue.CRITICAL for i in self.issues)


def main():
    """Main entry point."""
    diagnostics = EnvironmentDiagnostics()
    diagnostics.diagnose()
    diagnostics.print_report()

    # Exit with error code if critical issues found
    if diagnostics.has_critical_issues():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()

