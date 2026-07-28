#!/usr/bin/env python3
"""Verify pyenv+Poetry environment configuration."""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple

from diagnose import parent_virtual_env


class EnvironmentVerifier:
    """Verify Python environment configuration."""

    def __init__(self, repo_root: Path = None):
        self.repo_root = repo_root or Path.cwd()
        self.checks_passed = 0
        self.checks_failed = 0

    def run_command(self, cmd: list) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return 1, "", str(e)

    def check(self, name: str, condition: bool, details: str = "") -> bool:
        """Record a check result."""
        if condition:
            print(f"[OK] {name}")
            if details:
                print(f"     {details}")
            self.checks_passed += 1
            return True
        else:
            print(f"[FAIL] {name}")
            if details:
                print(f"       {details}")
            self.checks_failed += 1
            return False

    def verify(self) -> bool:
        """Run all verification checks."""
        print("=" * 70)
        print("PYTHON ENVIRONMENT VERIFICATION")
        print("=" * 70)
        print()

        # Check the caller's shell, not Poetry's child-process environment.
        virtual_env = parent_virtual_env()
        self.check(
            "Calling shell has no active VIRTUAL_ENV",
            virtual_env is None,
            f"Current value: {virtual_env}" if virtual_env else "",
        )

        # Check pyenv is installed
        returncode, stdout, _ = self.run_command(["pyenv", "--version"])
        self.check(
            "pyenv is installed",
            returncode == 0,
            stdout if returncode == 0 else "pyenv not found",
        )

        # Check pyenv shims in PATH
        path_env = os.environ.get("PATH", "")
        self.check("pyenv shims in PATH", ".pyenv/shims" in path_env)

        # Check Poetry is installed
        returncode, stdout, _ = self.run_command(["poetry", "--version"])
        self.check(
            "Poetry is installed",
            returncode == 0,
            stdout if returncode == 0 else "Poetry not found",
        )

        # Check Poetry detects correct Python
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'python\s*=\s*"([^"]+)"', content)
            if match:
                required_python = match.group(1).lstrip("^~")

                returncode, stdout, _ = self.run_command(["poetry", "env", "info"])
                if returncode == 0:
                    match = re.search(r"Python:\s+(\d+\.\d+\.\d+)", stdout)
                    if match:
                        poetry_python = match.group(1)
                        # Simple version check
                        poetry_parts = poetry_python.split(".")[:2]
                        required_parts = required_python.split(".")[:2]
                        try:
                            poetry_ver = tuple(int(p) for p in poetry_parts)
                            required_ver = tuple(int(p) for p in required_parts)
                            matches = poetry_ver >= required_ver
                            self.check(
                                "Poetry Python version matches requirements",
                                matches,
                                f"Poetry: {poetry_python}, Required: {required_python}",
                            )
                        except (ValueError, IndexError):
                            self.check(
                                "Poetry Python version matches requirements",
                                False,
                                "Could not parse versions",
                            )

        # Check Poetry venv location
        returncode, stdout, _ = self.run_command(["poetry", "env", "info", "--path"])
        if returncode == 0 and stdout:
            venv_path = Path(stdout)
            try:
                venv_path.relative_to(self.repo_root)
                in_project = True
            except ValueError:
                in_project = False

            self.check(
                "Poetry venv is in project directory",
                in_project,
                f"Location: {venv_path}",
            )

        # Summary
        print()
        print("=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"Checks passed: {self.checks_passed}")
        print(f"Checks failed: {self.checks_failed}")
        print()

        if self.checks_failed == 0:
            print("Status: ENVIRONMENT OK")
            return True
        else:
            print("Status: ENVIRONMENT HAS ISSUES")
            print()
            print("Run diagnostics: .agents/bin/agent-python-env-setup diagnose")
            return False


def main():
    """Main entry point."""
    verifier = EnvironmentVerifier()
    success = verifier.verify()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
