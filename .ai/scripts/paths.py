#!/usr/bin/env python3
"""Path utilities for robust repository-root discovery."""

from __future__ import annotations

from pathlib import Path


def resolve_repo_root(start: Path) -> Path:
    """Resolve repository root by walking up parents for project markers."""
    current = start if start.is_dir() else start.parent

    for candidate in [current, *current.parents]:
        if (candidate / ".ai").is_dir() and (
            (candidate / ".git").exists()
            or (candidate / "AGENTS.md").exists()
            or (candidate / "README.md").exists()
        ):
            return candidate

    # Conservative fallback for legacy layouts.
    return start if start.is_dir() else start.parent
