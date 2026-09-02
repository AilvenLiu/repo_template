#!/usr/bin/env python3
"""Fix pyenv+Poetry environment configuration issues."""

import subprocess
import sys
from pathlib import Path

# Import diagnostics
sys.path.insert(0, str(Path(__file__).parent))
from diagnose import EnvironmentDiagnostics, parent_virtual_env

_caller_virtual_env = parent_virtual_env


class EnvironmentFixer:
    """Fix Python environment configuration issues."""

    def __init__(self, repo_root: Path = None, auto_approve: bool = False):
        self.repo_root = repo_root or Path.cwd()
        self.auto_approve = auto_approve
        self.diagnostics = EnvironmentDiagnostics(repo_root)

    def run_command(self, cmd: list) -> tuple:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            return result.returncode, result.stdout.strip(), result.stderr.strip()
        except Exception as e:
            return 1, "", str(e)

    def confirm(self, message: str) -> bool:
        """Ask for user confirmation."""
        if self.auto_approve:
            return True

        response = input(f"{message} (y/n): ").strip().lower()
        return response in ("y", "yes")

    def fix_virtual_env(self) -> bool:
        """Fix VIRTUAL_ENV variable issue."""
        print("[1/5] Checking VIRTUAL_ENV variable...")

        virtual_env = parent_virtual_env()
        if not virtual_env:
            print("  [OK] Calling shell has no active VIRTUAL_ENV")
            return True

        print(f"  [ISSUE] Calling shell has an active VIRTUAL_ENV: {virtual_env}")
        print("  This can shadow the intended pyenv Python selection")
        print()

        if not self.confirm("  Unset VIRTUAL_ENV and add to ~/.zshrc?"):
            print("  [SKIP] Skipped by user")
            return False

        # Add unset to ~/.zshrc
        zshrc = Path.home() / ".zshrc"
        if zshrc.exists():
            content = zshrc.read_text()
            if "unset VIRTUAL_ENV" not in content:
                with open(zshrc, "a") as f:
                    f.write(
                        "\n# CRITICAL: Unset system-set VIRTUAL_ENV to prevent Poetry conflicts\n"
                    )
                    f.write("unset VIRTUAL_ENV\n")
                print("  [OK] Added 'unset VIRTUAL_ENV' to ~/.zshrc")
            else:
                print("  [OK] 'unset VIRTUAL_ENV' already in ~/.zshrc")
        else:
            print("  [WARNING] ~/.zshrc not found, creating it")
            with open(zshrc, "w") as f:
                f.write(
                    "# CRITICAL: Unset system-set VIRTUAL_ENV to prevent Poetry conflicts\n"
                )
                f.write("unset VIRTUAL_ENV\n")
            print("  [OK] Created ~/.zshrc with 'unset VIRTUAL_ENV'")

        print()
        print("  IMPORTANT: Open a new terminal or run: source ~/.zshrc")
        print()
        return True

    def check_pyenv(self) -> bool:
        """Check and guide pyenv installation."""
        print("[2/5] Checking pyenv...")

        returncode, stdout, _ = self.run_command(["pyenv", "--version"])
        if returncode == 0:
            print(f"  [OK] pyenv is installed: {stdout}")
            return True

        print("  [ISSUE] pyenv is not installed")
        print()
        print("  To install pyenv, run:")
        print("    curl https://pyenv.run | bash")
        print()
        print("  Then add to ~/.zshrc:")
        print('    export PYENV_ROOT="$HOME/.pyenv"')
        print('    [[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"')
        print('    eval "$(pyenv init -)"')
        print('    eval "$(pyenv virtualenv-init -)"')
        print()
        return False

    def check_poetry_venv(self) -> bool:
        """Check and fix Poetry venv location."""
        print("[3/5] Checking Poetry virtual environment...")

        returncode, stdout, _ = self.run_command(["poetry", "env", "info", "--path"])
        if returncode != 0:
            print("  [INFO] No Poetry venv exists yet")
            return True

        venv_path = Path(stdout)
        try:
            venv_path.relative_to(self.repo_root)
            print(f"  [OK] Poetry venv is in project: {venv_path}")
            return True
        except ValueError:
            print(f"  [ISSUE] Poetry venv is outside project: {venv_path}")
            print()

            if not self.confirm(
                "  Remove external venv and configure for in-project venvs?"
            ):
                print("  [SKIP] Skipped by user")
                return False

            # Configure Poetry for in-project venvs
            returncode, _, _ = self.run_command(
                ["poetry", "config", "virtualenvs.in-project", "true", "--local"]
            )
            if returncode == 0:
                print("  [OK] Configured Poetry for in-project venvs")
            else:
                print("  [WARNING] Could not configure Poetry")

            # Remove external venv
            returncode, _, _ = self.run_command(["poetry", "env", "remove", "--all"])
            if returncode == 0:
                print("  [OK] Removed external venv")
            else:
                print("  [WARNING] Could not remove external venv")

            return True

    def guide_poetry_setup(self) -> bool:
        """Guide Poetry environment setup."""
        print("[4/5] Poetry environment setup...")
        print()
        print("  To create Poetry environment with correct Python:")
        print("    1. Ensure VIRTUAL_ENV is unset (open new terminal)")
        print("    2. Run: poetry env use <python-version>")
        print("       Example: poetry env use 3.12")
        print("    3. Run: poetry install")
        print()
        return True

    def verify_setup(self) -> bool:
        """Verify the setup."""
        print("[5/5] Verification...")
        print()
        print("  Run these commands to verify:")
        print("    poetry env info")
        print("    poetry run python --version")
        print()
        return True

    def fix(self) -> bool:
        """Run all fixes."""
        print("=" * 70)
        print("PYTHON ENVIRONMENT FIX")
        print("=" * 70)
        print()

        # Run diagnostics first
        print("Running diagnostics...")
        self.diagnostics.diagnose()
        print()

        if not self.diagnostics.has_critical_issues():
            print("No critical issues found. Run diagnostics for details:")
            print("  .agents/bin/agent-python-env-setup diagnose")
            return True

        print("=" * 70)
        print("APPLYING FIXES")
        print("=" * 70)
        print()

        # Apply fixes
        self.fix_virtual_env()
        self.check_pyenv()
        self.check_poetry_venv()
        self.guide_poetry_setup()
        self.verify_setup()

        print("=" * 70)
        print("FIX PROCESS COMPLETE")
        print("=" * 70)
        print()
        print("IMPORTANT NEXT STEPS:")
        print("1. Open a new terminal (or run: source ~/.zshrc)")
        print("2. Navigate to your project directory")
        print("3. Run: poetry env use <python-version>")
        print("4. Run: poetry install")
        print("5. Verify: .agents/bin/agent-python-env-setup verify")
        print()

        return True


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Fix Python environment issues")
    parser.add_argument(
        "--auto-approve", action="store_true", help="Skip confirmation prompts"
    )
    args = parser.parse_args()

    fixer = EnvironmentFixer(auto_approve=args.auto_approve)
    fixer.fix()


if __name__ == "__main__":
    main()
