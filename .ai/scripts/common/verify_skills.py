#!/usr/bin/env python3
"""
Skill Verification Tool

Verifies that all skills in .claude/skills/ are properly configured and discoverable
by Claude Code. Run this after copying the template to a new project.

Usage:
    python3 .ai/scripts/common/verify_skills.py
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


class SkillVerifier:
    """Verifies skill installation and configuration."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.skills_dir = repo_root / ".claude" / "skills"
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.skills_found: List[Dict] = []

    def verify_all(self) -> bool:
        """Run all verification checks. Returns True if all checks pass."""
        print("=" * 70)
        print("CLAUDE CODE SKILL VERIFICATION")
        print("=" * 70)
        print()

        if not self.skills_dir.exists():
            self.errors.append(f"Skills directory not found: {self.skills_dir}")
            self._print_results()
            return False

        # Find all potential skill directories
        skill_dirs = [d for d in self.skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

        print(f"Scanning {len(skill_dirs)} directories in {self.skills_dir.relative_to(self.repo_root)}")
        print()

        for skill_dir in sorted(skill_dirs):
            if skill_dir.name == "common":
                continue  # Skip common utilities directory
            self._verify_skill(skill_dir)

        self._print_results()
        return len(self.errors) == 0

    def _verify_skill(self, skill_dir: Path) -> None:
        """Verify a single skill directory."""
        skill_name = skill_dir.name
        print(f"Checking skill: {skill_name}")

        # Check for SKILL.md
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            # Check for lowercase variant (common mistake)
            if (skill_dir / "skill.md").exists():
                self.errors.append(
                    f"  [{skill_name}] Found 'skill.md' but Claude Code requires 'SKILL.md' (uppercase)"
                )
                print(f"  [ERROR] SKILL.md not found (found skill.md instead)")
                return
            else:
                self.errors.append(f"  [{skill_name}] SKILL.md not found")
                print(f"  [ERROR] SKILL.md not found")
                return

        # Parse YAML frontmatter
        try:
            content = skill_md.read_text()
            if not content.startswith("---"):
                self.errors.append(f"  [{skill_name}] SKILL.md missing YAML frontmatter")
                print(f"  [ERROR] Missing YAML frontmatter")
                return

            # Extract frontmatter
            parts = content.split("---", 2)
            if len(parts) < 3:
                self.errors.append(f"  [{skill_name}] Invalid YAML frontmatter format")
                print(f"  [ERROR] Invalid frontmatter format")
                return

            if not HAS_YAML:
                self.warnings.append(f"  [{skill_name}] Cannot parse YAML (PyYAML not installed)")
                print(f"  [WARN] Cannot validate YAML (install PyYAML to enable)")
                # Basic validation without YAML parsing
                if "name:" in content and "description:" in content:
                    print(f"  [OK] Basic frontmatter structure detected")
                    self.skills_found.append({
                        "name": skill_name,
                        "description": "Unknown (PyYAML not installed)",
                        "version": "unknown",
                        "path": skill_dir.relative_to(self.repo_root),
                    })
                return

            frontmatter = yaml.safe_load(parts[1])

            # Validate required fields
            if "name" not in frontmatter:
                self.errors.append(f"  [{skill_name}] Missing 'name' in frontmatter")
                print(f"  [ERROR] Missing 'name' field")
                return

            if "description" not in frontmatter:
                self.errors.append(f"  [{skill_name}] Missing 'description' in frontmatter")
                print(f"  [ERROR] Missing 'description' field")
                return

            # Check name matches directory
            if frontmatter["name"] != skill_name:
                self.warnings.append(
                    f"  [{skill_name}] Name mismatch: directory='{skill_name}', "
                    f"frontmatter='{frontmatter['name']}'"
                )
                print(f"  [WARN] Name mismatch: '{frontmatter['name']}'")

            # Check for scripts directory
            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                self.warnings.append(f"  [{skill_name}] No scripts/ directory found")
                print(f"  [WARN] No scripts/ directory")
            else:
                # Count Python scripts
                scripts = list(scripts_dir.glob("*.py"))
                if len(scripts) == 0:
                    self.warnings.append(f"  [{skill_name}] No Python scripts in scripts/")
                    print(f"  [WARN] No Python scripts found")
                else:
                    print(f"  [OK] Found {len(scripts)} script(s)")

            # Record successful skill
            self.skills_found.append({
                "name": frontmatter["name"],
                "description": frontmatter.get("description", ""),
                "version": frontmatter.get("version", "unknown"),
                "path": skill_dir.relative_to(self.repo_root),
            })

            print(f"  [OK] Skill '{frontmatter['name']}' is properly configured")

        except yaml.YAMLError as e:
            self.errors.append(f"  [{skill_name}] Invalid YAML in frontmatter: {e}")
            print(f"  [ERROR] Invalid YAML: {e}")
        except Exception as e:
            self.errors.append(f"  [{skill_name}] Verification failed: {e}")
            print(f"  [ERROR] {e}")

        print()

    def _print_results(self) -> None:
        """Print verification results summary."""
        print("=" * 70)
        print("VERIFICATION RESULTS")
        print("=" * 70)
        print()

        if self.skills_found:
            print(f"✓ Found {len(self.skills_found)} valid skill(s):")
            for skill in self.skills_found:
                print(f"  - /{skill['name']}: {skill['description'][:60]}...")
            print()

        if self.warnings:
            print(f"⚠ {len(self.warnings)} warning(s):")
            for warning in self.warnings:
                print(f"  {warning}")
            print()

        if self.errors:
            print(f"✗ {len(self.errors)} error(s):")
            for error in self.errors:
                print(f"  {error}")
            print()
            print("Skills with errors will NOT be discoverable by Claude Code.")
            print()
        else:
            print("✓ All skills are properly configured and should be discoverable.")
            print()

        print("=" * 70)


def main():
    """Main entry point."""
    # Find repository root by walking up from script location
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent.parent  # common/ -> skills/ -> .claude/ -> repo/

    verifier = SkillVerifier(repo_root)
    success = verifier.verify_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
