#!/usr/bin/env python3
"""Claude /init adapter that delegates to the shared .ai/tools runtime."""

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Claude session initialization adapter")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[4]
    command = [
        sys.executable,
        str(repo_root / ".ai" / "tools" / "session_init.py"),
        "--platform",
        "claude",
    ]
    if args.verbose:
        command.append("--verbose")

    result = subprocess.run(command, cwd=repo_root)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
