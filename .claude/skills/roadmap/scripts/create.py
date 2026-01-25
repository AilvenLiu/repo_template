#!/usr/bin/env python3
"""Create new roadmap from template."""

import sys
import re
import shutil
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def validate_roadmap_name(name: str) -> bool:
    """Validate roadmap name format.

    Args:
        name: Roadmap name to validate

    Returns:
        True if valid, False otherwise
    """
    # Must be lowercase, hyphens, no spaces
    pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    return bool(re.match(pattern, name))


def create_roadmap(name: str, description: str = "") -> None:
    """Create new roadmap directory structure.

    Args:
        name: Roadmap name (lowercase, hyphens)
        description: Optional roadmap description
    """
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)

    # Check for active roadmap (enforce single-active rule)
    active = manager.find_active_roadmap()
    if active:
        print(f"ERROR: Roadmap '{active['name']}' is already active")
        print("You must complete or deactivate it before creating a new one")
        print(f"Active roadmap path: {active['path']}")
        sys.exit(1)

    # Validate roadmap name
    if not validate_roadmap_name(name):
        print(f"ERROR: Invalid roadmap name '{name}'")
        print("Roadmap name must be lowercase with hyphens (e.g., 'api-v2-migration')")
        sys.exit(1)

    # Create roadmap directory
    roadmap_dir = manager.roadmaps_dir / name
    if roadmap_dir.exists():
        print(f"ERROR: Roadmap directory already exists: {roadmap_dir}")
        sys.exit(1)

    try:
        roadmap_dir.mkdir(parents=True, exist_ok=False)
        print(f"Created roadmap directory: {roadmap_dir.relative_to(repo_root)}")

        # Copy template files
        skill_dir = Path(__file__).parent.parent
        templates_dir = skill_dir / "templates"

        for template_file in ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]:
            src = templates_dir / template_file
            dst = roadmap_dir / template_file
            if src.exists():
                shutil.copy2(src, dst)
                print(f"  Created: {template_file}")
            else:
                print(f"  WARNING: Template not found: {template_file}")

        # Create sessions directory
        sessions_dir = roadmap_dir / "sessions"
        sessions_dir.mkdir(exist_ok=True)
        print(f"  Created: sessions/")

        # Update roadmap.yml with provided name and description
        roadmap_yml = roadmap_dir / "roadmap.yml"
        if roadmap_yml.exists():
            updates = {
                "roadmap": {
                    "name": name,
                    "description": description or f"Roadmap for {name}",
                }
            }
            manager.update_roadmap_yml(roadmap_yml, updates)
            print(f"  Initialised: roadmap.yml")

        # Validate structure
        errors = manager.validate_roadmap_structure(roadmap_dir)
        if errors:
            print("\nWARNING: Roadmap structure has validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("\nRoadmap created successfully!")
            print(f"\nNext steps:")
            print(f"1. Edit {roadmap_dir.relative_to(repo_root)}/INVARIANTS.md")
            print(f"2. Edit {roadmap_dir.relative_to(repo_root)}/ROADMAP.md")
            print(f"3. Edit {roadmap_dir.relative_to(repo_root)}/roadmap.yml")
            print(f"4. Activate roadmap by setting status.active: true in roadmap.yml")

    except Exception as e:
        print(f"ERROR: Failed to create roadmap: {e}")
        # Clean up partial creation
        if roadmap_dir.exists():
            shutil.rmtree(roadmap_dir)
        sys.exit(1)


def main():
    """Main entry point for create command."""
    if len(sys.argv) < 2:
        print("Usage: create.py <roadmap-name> [description]")
        print("Example: create.py api-v2-migration 'Migrate to API v2'")
        sys.exit(1)

    name = sys.argv[1]
    description = sys.argv[2] if len(sys.argv) > 2 else ""

    create_roadmap(name, description)


if __name__ == "__main__":
    main()
