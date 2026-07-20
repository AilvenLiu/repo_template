#!/usr/bin/env python3
"""Legacy project_type API - backward compatibility shim.

This module maintains the old ProjectType enum API for existing callers
while delegating to the new project_profile module internally.

New code should use project_profile.py directly.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Optional

try:
    from .project_profile import Language, ProjectProfile, detect as detect_profile
except ImportError:
    from project_profile import Language, ProjectProfile, detect as detect_profile


class ProjectType(Enum):
    """Legacy project type enum.

    Maintained for backward compatibility. New code should use ProjectProfile.
    """

    PYTHON = "python"
    CPP = "cpp"
    UNKNOWN = "unknown"


def _profile_to_project_type(profile: ProjectProfile) -> ProjectType:
    """Map a ProjectProfile to legacy ProjectType.

    Args:
        profile: The detected project profile

    Returns:
        Equivalent legacy ProjectType
    """
    # Hybrid projects default to Python if it's one of the languages
    if profile.has_language(Language.PYTHON):
        return ProjectType.PYTHON
    elif profile.has_language(Language.CPP):
        return ProjectType.CPP
    else:
        return ProjectType.UNKNOWN


def detect(repo_root: Optional[Path] = None) -> ProjectType:
    """Detect project type from configuration or heuristics.

    This is a legacy API maintained for backward compatibility.
    New code should use project_profile.detect() directly.

    Args:
        repo_root: Repository root path (defaults to current directory)

    Returns:
        ProjectType enum value (PYTHON, CPP, or UNKNOWN)
    """
    profile = detect_profile(repo_root)
    if profile is None:
        return ProjectType.UNKNOWN
    return _profile_to_project_type(profile)
