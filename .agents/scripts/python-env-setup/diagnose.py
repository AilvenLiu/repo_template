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
        self._has_python = self._detect_python_project()

    def _detect_python_project(self) -> bool:
        """Return True if this project has a Python component."""
        project_yml = self.repo_root / ".agents" / "project.yml"
        if project_yml.exists():
            try:
                content = project_yml.read_text(encoding="utf-8")
                # Pure C++ projects have language: [cpp] and no python
                if "language:" in content and "python" not in content:
                    return False
            except OSError:
                pass

        # pyproject.toml or poetry.toml → Python project
        if (self.repo_root / "pyproject.toml").exists():
            return True
        if (self.repo_root / "poetry.toml").exists():
            return True
        # Look for .py files in project source dirs only (not infra dirs)
        _INFRA_DIRS = {
            ".agents",
            ".claude",
            ".venv",
            "venv",
            "build",
            ".git",
            ".codex",
            "agent_roadmaps",
        }
        py_files = [
            f
            for f in self.repo_root.rglob("*.py")
            if not any(p in _INFRA_DIRS for p in f.relative_to(self.repo_root).parts)
        ]
        return bool(py_files)

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

    # ------------------------------------------------------------------
    # Check 1: Poetry available from an isolated tool installation
    # ------------------------------------------------------------------

    def check_poetry_install(self) -> None:
        """Verify Poetry is available for projects with a Python component."""
        if not self._has_python:
            self.issues.append(
                Issue(
                    severity=Issue.INFO,
                    message="Pure C++ project; Poetry installation check skipped",
                )
            )
            return

        returncode, poetry_path, error = self.run_command(["which", "poetry"])
        if returncode != 0 or not poetry_path:
            self.issues.append(
                Issue(
                    severity=Issue.CRITICAL,
                    message="Poetry is not available on PATH",
                    details=error
                    or "Provision Poetry with pipx or a pinned tool image.",
                    fix="Install pipx with the platform package manager, then run: pipx install poetry",
                )
            )
            return

        returncode, version_out, error = self.run_command(["poetry", "--version"])
        if returncode != 0:
            self.issues.append(
                Issue(
                    severity=Issue.CRITICAL,
                    message="Poetry on PATH is not executable",
                    details=error,
                    fix="Repair the isolated Poetry installation and rerun verification.",
                )
            )
            return

        self.issues.append(
            Issue(
                severity=Issue.OK,
                message=f"Poetry is available ({version_out})",
                details=f"Path: {poetry_path}",
            )
        )

    # ------------------------------------------------------------------
    # Check 2: In-project virtual environment configured via poetry.toml
    # ------------------------------------------------------------------

    def check_poetry_toml_in_project(self) -> None:
        """Verify poetry.toml exists and sets in-project = true.

        Only applies to Python/Hybrid projects. Pure C++ projects do not use Poetry.
        """
        if not self._has_python:
            self.issues.append(
                Issue(
                    severity=Issue.INFO,
                    message="Pure C++ project — poetry.toml check skipped",
                )
            )
            return

        poetry_toml = self.repo_root / "poetry.toml"

        if not poetry_toml.exists():
            self.issues.append(
                Issue(
                    severity=Issue.CRITICAL,
                    message="poetry.toml not found in project root",
                    details=(
                        "poetry.toml is required to configure in-project virtual environments.\n"
                        "  Without it, Poetry may create the venv outside the project directory."
                    ),
                    fix=(
                        "Create poetry.toml with:\n"
                        "  [virtualenvs]\n"
                        "  in-project = true\n\n"
                        "  [virtualenvs.options]\n"
                        "  system-site-packages = false"
                    ),
                )
            )
            return

        content = poetry_toml.read_text(encoding="utf-8")
        if "in-project = true" not in content:
            self.issues.append(
                Issue(
                    severity=Issue.CRITICAL,
                    message="poetry.toml does not set in-project = true",
                    details=f"Current content:\n{content}",
                    fix='Add "in-project = true" under [virtualenvs] in poetry.toml',
                )
            )
            return

        self.issues.append(
            Issue(
                severity=Issue.OK,
                message="poetry.toml found with in-project = true",
            )
        )

        # Also verify the actual venv location if one exists
        returncode, venv_path_out, _ = self.run_command(
            ["poetry", "env", "info", "--path"]
        )
        if returncode == 0 and venv_path_out:
            venv_path = Path(venv_path_out)
            try:
                venv_path.relative_to(self.repo_root)
                self.issues.append(
                    Issue(
                        severity=Issue.OK,
                        message=f"Poetry venv is in-project at {venv_path}",
                    )
                )
            except ValueError:
                self.issues.append(
                    Issue(
                        severity=Issue.CRITICAL,
                        message="Poetry venv is outside the project directory",
                        details=f"Current venv: {venv_path}\n  Expected: {self.repo_root / '.venv'}",
                        fix=("poetry env remove --all\n  poetry install"),
                    )
                )

    # ------------------------------------------------------------------
    # Check 3: custom package-source safety
    # ------------------------------------------------------------------

    def check_package_sources(self) -> None:
        """Validate declared Poetry package sources without forcing a mirror."""
        pyproject = self.repo_root / "pyproject.toml"
        if not pyproject.exists():
            self.issues.append(
                Issue(
                    severity=Issue.INFO,
                    message="No pyproject.toml found; package-source check skipped",
                )
            )
            return

        content = pyproject.read_text(encoding="utf-8")
        blocks = re.findall(
            r"\[\[tool\.poetry\.source\]\](.*?)(?=\n\[|\Z)",
            content,
            re.DOTALL,
        )
        if not blocks:
            self.issues.append(
                Issue(
                    severity=Issue.OK,
                    message="No custom package source declared; Poetry default PyPI applies",
                )
            )
            return

        for block in blocks:
            name_match = re.search(r"name\s*=\s*[\"\']([^\"\']+)", block)
            url_match = re.search(r"url\s*=\s*[\"\']([^\"\']+)", block)
            priority_match = re.search(r"priority\s*=\s*[\"\']([^\"\']+)", block)
            name = name_match.group(1) if name_match else "<unnamed>"
            url = url_match.group(1) if url_match else ""
            priority = priority_match.group(1) if priority_match else ""

            if not url.startswith("https://"):
                self.issues.append(
                    Issue(
                        severity=Issue.CRITICAL,
                        message=f"Package source {name} does not use HTTPS",
                        details=f"Configured URL: {url or '<missing>'}",
                        fix="Use a reviewed HTTPS package-index URL.",
                    )
                )
            elif re.match(r"https://[^/@]+:[^/@]+@", url):
                self.issues.append(
                    Issue(
                        severity=Issue.CRITICAL,
                        message=f"Package source {name} embeds credentials",
                        fix=(
                            "Remove credentials from pyproject.toml and use approved "
                            "secret configuration."
                        ),
                    )
                )
            elif priority not in {"primary", "supplemental", "explicit"}:
                self.issues.append(
                    Issue(
                        severity=Issue.CRITICAL,
                        message=f"Package source {name} lacks an explicit reviewed priority",
                        details=f"Configured priority: {priority or '<missing>'}",
                        fix="Set priority to primary, supplemental, or explicit per project policy.",
                    )
                )
            else:
                self.issues.append(
                    Issue(
                        severity=Issue.OK,
                        message=f"Package source {name} uses HTTPS with {priority} priority",
                    )
                )

    # ------------------------------------------------------------------
    # Original checks (preserved and refined)
    # ------------------------------------------------------------------

    def check_virtual_env_variable(self) -> None:
        """Check if VIRTUAL_ENV environment variable is set."""
        virtual_env = os.environ.get("VIRTUAL_ENV")
        if virtual_env:
            self.issues.append(
                Issue(
                    severity=Issue.CRITICAL,
                    message="VIRTUAL_ENV is set to system Python",
                    details=(
                        f"Current value: {virtual_env}\n"
                        "  Impact: Poetry will always detect the system Python instead of pyenv Python"
                    ),
                    fix='unset VIRTUAL_ENV && echo "unset VIRTUAL_ENV" >> ~/.zshrc',
                )
            )
        else:
            self.issues.append(
                Issue(
                    severity=Issue.OK,
                    message="VIRTUAL_ENV is not set",
                )
            )

    def check_python_versions(self) -> None:
        """Check Python versions (system, required, Poetry)."""
        required_python = None
        pyproject = self.repo_root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            match = re.search(r'python\s*=\s*"([^"]+)"', content)
            if match:
                required_python = match.group(1)

        poetry_python = None
        returncode, stdout, _ = self.run_command(["poetry", "env", "info"])
        if returncode == 0:
            match = re.search(r"Python:\s+(\d+\.\d+\.\d+)", stdout)
            if match:
                poetry_python = match.group(1)

        pyenv_python = None
        returncode, stdout, _ = self.run_command(["pyenv", "version"])
        if returncode == 0:
            match = re.search(r"(\d+\.\d+\.\d+)", stdout)
            if match:
                pyenv_python = match.group(1)

        if poetry_python and required_python:
            if not self._version_matches_constraint(poetry_python, required_python):
                self.issues.append(
                    Issue(
                        severity=Issue.WARNING,
                        message="Poetry detects wrong Python version",
                        details=(
                            f"Poetry Python: {poetry_python}\n"
                            f"  Required: {required_python}\n"
                            f"  pyenv Python: {pyenv_python or 'not installed'}"
                        ),
                        fix="Remove Poetry venv and recreate with correct Python",
                    )
                )
            else:
                self.issues.append(
                    Issue(
                        severity=Issue.OK,
                        message=f"Poetry Python version matches requirements ({poetry_python})",
                    )
                )

    def _version_matches_constraint(self, version: str, constraint: str) -> bool:
        """Check if version matches constraint (simplified)."""
        constraint = constraint.lstrip("^~")
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
        returncode, stdout, _ = self.run_command(["pyenv", "--version"])
        if returncode != 0:
            self.issues.append(
                Issue(
                    severity=Issue.WARNING,
                    message="pyenv is not installed",
                    fix="Install pyenv: curl https://pyenv.run | bash",
                )
            )
            return

        pyenv_version = stdout
        path_env = os.environ.get("PATH", "")
        if ".pyenv/shims" not in path_env:
            self.issues.append(
                Issue(
                    severity=Issue.WARNING,
                    message="pyenv shims not in PATH",
                    details="pyenv is installed but not properly initialised",
                    fix='Add to ~/.zshrc: eval "$(pyenv init -)"',
                )
            )
        else:
            returncode, pyenv_path, _ = self.run_command(["which", "pyenv"])
            self.issues.append(
                Issue(
                    severity=Issue.OK,
                    message=(
                        "pyenv is installed and configured\n"
                        f"  Version: {pyenv_version}\n  Path: {pyenv_path}"
                    ),
                )
            )

    def check_path_order(self) -> None:
        """Check PATH order to ensure pyenv shims and ~/.local/bin come first."""
        path_env = os.environ.get("PATH", "")
        path_parts = path_env.split(":")

        local_bin_index = None
        pyenv_shim_index = None
        system_python_index = None

        for i, part in enumerate(path_parts):
            if ".local/bin" in part and local_bin_index is None:
                local_bin_index = i
            if ".pyenv/shims" in part and pyenv_shim_index is None:
                pyenv_shim_index = i
            if (
                "/usr/bin" in part or "/usr/local/bin" in part
            ) and system_python_index is None:
                system_python_index = i

        if local_bin_index is None:
            self.issues.append(
                Issue(
                    severity=Issue.WARNING,
                    message="~/.local/bin not found on PATH",
                    details="Poetry (installed via pipx) will not be found without this",
                    fix='Add to ~/.zshrc: export PATH="$HOME/.local/bin:$PATH"',
                )
            )
        elif system_python_index is not None and local_bin_index > system_python_index:
            self.issues.append(
                Issue(
                    severity=Issue.WARNING,
                    message="~/.local/bin comes after system directories on PATH",
                    fix='Move "export PATH=\\"$HOME/.local/bin:$PATH\\"" to the top of ~/.zshrc',
                )
            )
        else:
            self.issues.append(
                Issue(
                    severity=Issue.OK,
                    message="~/.local/bin is correctly prioritised on PATH",
                )
            )

        if pyenv_shim_index is not None:
            if system_python_index is None or pyenv_shim_index < system_python_index:
                self.issues.append(
                    Issue(
                        severity=Issue.OK,
                        message="pyenv shims are prioritised in PATH",
                    )
                )
            else:
                self.issues.append(
                    Issue(
                        severity=Issue.WARNING,
                        message="System Python comes before pyenv in PATH",
                        fix="Ensure pyenv init is called in ~/.zshrc before other PATH modifications",
                    )
                )

    def diagnose(self) -> List[Issue]:
        """Run all diagnostic checks."""
        print("=" * 70)
        print("PYTHON ENVIRONMENT DIAGNOSTICS")
        print("=" * 70)
        print()

        # Mandatory checks (STOP if critical)
        print("--- Mandatory Checks ---")
        self.check_poetry_install()
        self.check_poetry_toml_in_project()
        self.check_package_sources()

        # Environment checks
        print()
        print("--- Environment Checks ---")
        self.check_virtual_env_variable()
        self.check_python_versions()
        self.check_pyenv()
        self.check_path_order()

        return self.issues

    def print_report(self) -> None:
        """Print diagnostic report."""
        for issue in self.issues:
            print(issue)
            print()

        critical_count = sum(1 for i in self.issues if i.severity == Issue.CRITICAL)
        warning_count = sum(1 for i in self.issues if i.severity == Issue.WARNING)

        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"Critical issues: {critical_count}")
        print(f"Warnings: {warning_count}")

        if critical_count > 0:
            print("Status: ENVIRONMENT NEEDS CRITICAL FIXES — STOP AND ASK USER")
            print()
            print("REQUIRED ACTIONS (fix before continuing):")
            action_num = 1
            for issue in self.issues:
                if issue.severity == Issue.CRITICAL and issue.fix:
                    print(f"{action_num}. {issue.fix}")
                    action_num += 1
        elif warning_count > 0:
            print("Status: ENVIRONMENT NEEDS FIXES")
            print()
            print("RECOMMENDED ACTIONS:")
            action_num = 1
            for issue in self.issues:
                if issue.severity == Issue.WARNING and issue.fix:
                    print(f"{action_num}. {issue.fix}")
                    action_num += 1
        else:
            print("Status: ENVIRONMENT OK")

    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return any(i.severity == Issue.CRITICAL for i in self.issues)


def main():
    """Main entry point."""
    diagnostics = EnvironmentDiagnostics()
    diagnostics.diagnose()
    diagnostics.print_report()

    if diagnostics.has_critical_issues():
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
