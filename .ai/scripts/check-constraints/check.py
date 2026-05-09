#!/usr/bin/env python3
"""Constraint-check adapter to shared .ai/scripts implementation."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[4]
    command = [
        sys.executable,
        str(repo_root / ".ai" / "tools" / "constraints_check.py"),
        "--project-type",
        "auto",
    ]
    result = subprocess.run(command, cwd=repo_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
