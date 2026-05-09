#!/usr/bin/env python3
"""
Base utilities for Claude Code skills.

Provides path resolution and repository detection that works regardless of:
- Where the skill is invoked from
- Where the template was copied to
- What the repository structure looks like
"""

import sys
from pathlib import Path
from typing import Optional


class SkillBase:
    """Base class for skill scripts with robust path resolution."""

    def __init__(self, script_file: str):
        """
        Initialize skill with self-locating path resolution.

        Args:
            script_file: Pass __file__ from the calling script
        """
        # Find the skill's own location
        self.script_path = Path(script_file).resolve()
        self.skill_dir = self.script_path.parent.parent  # scripts/ -> skill/
        self.skills_root = self.skill_dir.parent  # skill/ -> skills/
        self.claude_dir = self.skills_root.parent  # skills/ -> .claude/
        self.repo_root = self.claude_dir.parent  # .claude/ -> repo/

        # Validate we're in a proper skill structure
        if not self._validate_structure():
            raise RuntimeError(
                f"Skill structure validation failed.\n"
                f"Expected: repo/.ai/scripts/<skill-name>/<script>.py\n"
                f"Got: {self.script_path}"
            )

    def _validate_structure(self) -> bool:
        """Validate we're in the expected .claude/skills/ structure."""
        # Check that we're in .claude/skills/
        if self.claude_dir.name != ".claude":
            return False
        if self.skills_root.name != "skills":
            return False
        # Check that scripts directory exists
        if not (self.skill_dir / "scripts").exists():
            return False
        return True

    def get_constraint_path(self, constraint_name: str) -> Path:
        """Get path to a constraint file."""
        return self.claude_dir / "constraints" / f"{constraint_name}.md"

    def get_skill_path(self, skill_name: str) -> Path:
        """Get path to another skill's directory."""
        return self.skills_root / skill_name

    def is_git_repo(self) -> bool:
        """Check if we're in a git repository."""
        return (self.repo_root / ".git").exists()

    def find_file_upward(self, filename: str, start_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Search for a file by walking up the directory tree.

        Useful for finding pyproject.toml, CMakeLists.txt, etc.
        """
        current = start_dir or self.repo_root
        while current != current.parent:
            candidate = current / filename
            if candidate.exists():
                return candidate
            current = current.parent
        return None


def get_repo_root(script_file: str) -> Path:
    """
    Convenience function to get repository root from any skill script.

    Usage:
        from skill_base import get_repo_root
        repo_root = get_repo_root(__file__)
    """
    skill = SkillBase(script_file)
    return skill.repo_root


def add_common_to_path(script_file: str) -> None:
    """
    Add the common/ directory to Python path for imports.

    Usage at top of skill script:
        from skill_base import add_common_to_path
        add_common_to_path(__file__)
        from validate_constraints import check_poetry_compliance
    """
    skill = SkillBase(script_file)
    common_dir = skill.skills_root / "common"
    if common_dir.exists():
        sys.path.insert(0, str(common_dir))
