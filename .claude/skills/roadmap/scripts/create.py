#!/usr/bin/env python3
"""Create new per-phase roadmap structure from template."""

import argparse
import re
import shutil
import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


def validate_roadmap_name(name: str) -> bool:
    """Validate roadmap/phase name format (lowercase, hyphens only).

    Args:
        name: Name string to validate.

    Returns:
        True if valid, False otherwise.
    """
    pattern = r'^[a-z0-9]+(-[a-z0-9]+)*$'
    return bool(re.match(pattern, name))


def _replace_placeholders(text: str, replacements: dict) -> str:
    """Apply a mapping of placeholder -> value substitutions to *text*.

    Args:
        text: Source text that may contain placeholders.
        replacements: Mapping of placeholder string to replacement value.

    Returns:
        Text with all placeholders substituted.
    """
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def _create_phase_folder(
    phase_folder_name: str,
    phase_id: str,
    task_id: str,
    phase_title: str,
    is_active: bool,
    roadmaps_dir: Path,
    templates_dir: Path,
    repo_root: Path,
) -> None:
    """Create a single phase folder under *roadmaps_dir*.

    Args:
        phase_folder_name: Full folder name, e.g. ``phase-0-baseline``.
        phase_id: Short phase ID, e.g. ``phase-0``.
        task_id: Short task prefix, e.g. ``task-0``.
        phase_title: Title-cased phase name, e.g. ``Baseline``.
        is_active: Whether this phase should start as active.
        roadmaps_dir: ``agent_roadmaps/`` directory path.
        templates_dir: ``.claude/skills/roadmap/templates/`` directory path.
        repo_root: Repository root for display purposes.
    """
    phase_dir = roadmaps_dir / phase_folder_name
    if phase_dir.exists():
        print(f"ERROR: Phase directory already exists: {phase_dir}")
        sys.exit(1)

    phase_dir.mkdir(parents=True, exist_ok=False)

    # Placeholder replacements applied to every file in the phase folder
    replacements = {
        "<PHASE_FOLDER_NAME>": phase_folder_name,
        "<PHASE_ID>": phase_id,
        "<TASK_ID>": task_id,
        "<Phase Title>": phase_title,
    }

    for template_file in ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]:
        src = templates_dir / template_file
        dst = phase_dir / template_file
        if src.exists():
            content = src.read_text(encoding="utf-8")
            content = _replace_placeholders(content, replacements)

            # For roadmap.yml: also set status.active appropriately
            if template_file == "roadmap.yml" and not is_active:
                content = content.replace("active: true", "active: false", 1)

            dst.write_text(content, encoding="utf-8")
        else:
            print(f"  WARNING: Template not found: {template_file}")

    # Create sessions directory
    (phase_dir / "sessions").mkdir(exist_ok=True)

    rel = phase_dir.relative_to(repo_root)
    status_label = "active" if is_active else "pending"
    print(f"  Created phase folder: {rel}/ ({status_label})")


def create_roadmap(
    name: str,
    phases: int,
    phase_names: list,
    description: str = "",
) -> None:
    """Create the per-phase roadmap directory structure.

    Args:
        name: Overall roadmap name (used in README title).
        phases: Number of phase folders to create.
        phase_names: Descriptive suffix for each phase (length == phases).
        description: Optional overall roadmap description.
    """
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)
    roadmaps_dir = manager.roadmaps_dir
    templates_dir = Path(__file__).parent.parent / "templates"

    # ------------------------------------------------------------------
    # Enforce single-active-roadmap rule (scan existing phase-* dirs)
    # ------------------------------------------------------------------
    active = manager.find_active_roadmap()
    if active:
        print(f"ERROR: Roadmap '{active['name']}' is already active")
        print("You must complete or deactivate it before creating a new one")
        print(f"Active roadmap path: {active['path']}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Validate names
    # ------------------------------------------------------------------
    if not validate_roadmap_name(name):
        print(f"ERROR: Invalid roadmap name '{name}'")
        print("Name must be lowercase with hyphens (e.g., 'api-v2-migration')")
        sys.exit(1)

    for suffix in phase_names:
        if not validate_roadmap_name(suffix):
            print(f"ERROR: Invalid phase name '{suffix}'")
            print("Phase names must be lowercase with hyphens (e.g., 'baseline')")
            sys.exit(1)

    # ------------------------------------------------------------------
    # Ensure agent_roadmaps/ exists
    # ------------------------------------------------------------------
    roadmaps_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Create / update agent_roadmaps/README.md from template
    # ------------------------------------------------------------------
    readme_template = templates_dir / "README.md"
    readme_dst = roadmaps_dir / "README.md"

    if readme_template.exists():
        readme_content = readme_template.read_text(encoding="utf-8")

        # Build the numbered phase list for section 2
        phase_list_lines = []
        for i, suffix in enumerate(phase_names):
            folder = f"phase-{i}-{suffix}"
            if i == 0:
                status = "active"
            else:
                status = "pending"
            phase_list_lines.append(
                f"{i + 1}. `{folder}/` -- <brief description> -- status: {status}"
            )
        phase_list = "\n".join(phase_list_lines)

        # Replace the placeholder block (lines 23-25 in template)
        placeholder_block = (
            "1. `phase-0-<name>/` -- <brief description> -- status: pending | active | completed\n"
            "2. `phase-1-<name>/` -- <brief description> -- status: pending | active | completed\n"
            "3. `phase-2-<name>/` -- <brief description> -- status: pending | active | completed"
        )
        readme_content = readme_content.replace(placeholder_block, phase_list)

        # Replace the active phase placeholder with the first (active) phase folder
        readme_content = readme_content.replace(
            "<PHASE_FOLDER_NAME>", f"phase-0-{phase_names[0]}"
        )

        readme_dst.write_text(readme_content, encoding="utf-8")
        print(f"Created: {readme_dst.relative_to(repo_root)}")
    else:
        print("WARNING: README.md template not found; skipping README creation")

    # ------------------------------------------------------------------
    # Create each phase folder
    # ------------------------------------------------------------------
    created_phases = []
    try:
        for i, suffix in enumerate(phase_names):
            folder_name = f"phase-{i}-{suffix}"
            phase_id = f"phase-{i}"
            task_id = f"task-{i}"
            phase_title = suffix.replace("-", " ").title()
            is_active = i == 0

            _create_phase_folder(
                phase_folder_name=folder_name,
                phase_id=phase_id,
                task_id=task_id,
                phase_title=phase_title,
                is_active=is_active,
                roadmaps_dir=roadmaps_dir,
                templates_dir=templates_dir,
                repo_root=repo_root,
            )
            created_phases.append((folder_name, is_active))

    except SystemExit:
        raise
    except Exception as e:
        print(f"ERROR: Failed during phase creation: {e}")
        # Clean up any partially created phase dirs
        for folder_name, _ in created_phases:
            phase_dir = roadmaps_dir / folder_name
            if phase_dir.exists():
                shutil.rmtree(phase_dir)
        sys.exit(1)

    # ------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------
    print(f"\nRoadmap created with {len(phase_names)} phase(s):")
    for folder_name, is_active in created_phases:
        label = "(active)" if is_active else "(pending)"
        print(f"  {folder_name}/  {label}")

    first_folder = created_phases[0][0]
    print("\nNext steps:")
    print(
        "1. Edit each phase's INVARIANTS.md, ROADMAP.md, roadmap.yml, prompt.md"
    )
    print(
        f"2. Create branch: git checkout -b roadmap/{first_folder}"
    )
    print(
        f"3. Validate: python3 .claude/skills/roadmap/scripts/validate_schema.py {first_folder}"
    )


def _parse_args(argv=None):
    """Parse command-line arguments.

    Args:
        argv: Argument list (defaults to sys.argv[1:]).

    Returns:
        Parsed namespace.
    """
    parser = argparse.ArgumentParser(
        description="Create a new per-phase agent roadmap structure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  create.py my-project\n"
            "  create.py my-project --phases 3 --phase-names baseline core-impl cleanup\n"
            "  create.py my-project 'Overall description' --phases 2 --phase-names baseline core\n"
        ),
    )
    parser.add_argument(
        "name",
        help="Overall roadmap name (lowercase, hyphens; e.g. api-v2-migration)",
    )
    parser.add_argument(
        "description",
        nargs="?",
        default="",
        help="Optional overall roadmap description",
    )
    parser.add_argument(
        "--phases",
        type=int,
        default=1,
        metavar="N",
        help="Number of phase folders to create (default: 1)",
    )
    parser.add_argument(
        "--phase-names",
        nargs="+",
        metavar="NAME",
        help=(
            "Descriptive suffix for each phase (must match --phases count). "
            "If omitted, generates placeholder names (phase-0-todo, phase-1-todo, …)."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Main entry point for the create command."""
    args = _parse_args(argv)

    # ------------------------------------------------------------------
    # Resolve phase_names list
    # ------------------------------------------------------------------
    if args.phase_names:
        if len(args.phase_names) != args.phases:
            print(
                f"ERROR: --phase-names count ({len(args.phase_names)}) "
                f"does not match --phases {args.phases}"
            )
            sys.exit(1)
        phase_names = args.phase_names
    else:
        if args.phases == 1:
            # Default: single phase named after the roadmap itself
            phase_names = [args.name]
        else:
            phase_names = [f"todo" for _ in range(args.phases)]
            # Prefix each with its index to avoid collision (create_phase_folder
            # will turn these into "phase-N-todo")

    create_roadmap(
        name=args.name,
        phases=args.phases,
        phase_names=phase_names,
        description=args.description,
    )


if __name__ == "__main__":
    main()
