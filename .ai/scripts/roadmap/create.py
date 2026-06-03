#!/usr/bin/env python3
"""Create new dependency-aware per-step roadmap structure from template."""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from check_session import check_session_initialized

from utils import RoadmapManager


def validate_roadmap_name(name: str) -> bool:
    return bool(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", name))


def _replace_placeholders(text: str, replacements: Dict[str, str]) -> str:
    for placeholder, value in replacements.items():
        text = text.replace(placeholder, value)
    return text


def _serialise_dependency_inline(deps: List[str]) -> str:
    if not deps:
        return "[]"
    return "[" + ", ".join(deps) + "]"


def _make_step_table_rows(step_names: List[str]) -> str:
    rows: List[str] = []
    for index, suffix in enumerate(step_names):
        folder = f"step-{index}-{suffix}"
        status = "active" if index == 0 else "pending"
        dependency = (
            "none" if index == 0 else f"step-{index - 1}-{step_names[index - 1]}"
        )
        rows.append(f"| {index} | `{folder}` | {status} | `{dependency}` |")
    return "\n".join(rows)


def _make_dependency_graph(step_names: List[str]) -> str:
    if not step_names:
        return "(none)"
    chain = [f"step-{idx}-{suffix}" for idx, suffix in enumerate(step_names)]
    if len(chain) == 1:
        return chain[0]
    return " -> ".join(chain)


def _write_series_readme(
    roadmaps_dir: Path,
    templates_dir: Path,
    roadmap_name: str,
    description: str,
    step_names: List[str],
    repo_root: Path,
) -> None:
    template_path = templates_dir / "README.md"
    output_path = roadmaps_dir / "README.md"

    if not template_path.exists():
        print("WARNING: README template not found; skipping roadmap README generation")
        return

    if description.strip():
        description_block = description.strip()
    else:
        description_block = (
            "TODO: Add a concise description of the roadmap's business objective, "
            "scope, and success criteria."
        )

    replacements = {
        "<ROADMAP_TITLE>": roadmap_name.replace("-", " ").title(),
        "<ROADMAP_SLUG>": roadmap_name,
        "<ROADMAP_DESCRIPTION>": description_block,
        "<STEP_TABLE_ROWS>": _make_step_table_rows(step_names),
        "<ACTIVE_STEP_FOLDER>": f"step-0-{step_names[0]}",
        "<STEP_DEP_GRAPH>": _make_dependency_graph(step_names),
    }

    content = _replace_placeholders(
        template_path.read_text(encoding="utf-8"), replacements
    )
    output_path.write_text(content, encoding="utf-8")
    print(f"Created: {output_path.relative_to(repo_root)}")


def _create_step_folder(
    step_folder_name: str,
    step_number: int,
    step_title: str,
    task_prefix: str,
    is_active: bool,
    step_dependencies: List[str],
    roadmaps_dir: Path,
    templates_dir: Path,
    repo_root: Path,
) -> None:
    step_dir = roadmaps_dir / step_folder_name
    if step_dir.exists():
        print(f"ERROR: Step directory already exists: {step_dir}")
        sys.exit(1)

    step_dir.mkdir(parents=True, exist_ok=False)

    replacements = {
        "<STEP_FOLDER_NAME>": step_folder_name,
        "<STEP_NUMBER>": str(step_number),
        "<STEP_TITLE>": step_title,
        "<TASK_PREFIX>": task_prefix,
        "<STEP_DEPENDENCIES>": _serialise_dependency_inline(step_dependencies),
    }

    for template_file in ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]:
        source = templates_dir / template_file
        destination = step_dir / template_file

        if not source.exists():
            print(f"  WARNING: Template not found: {template_file}")
            continue

        content = _replace_placeholders(
            source.read_text(encoding="utf-8"), replacements
        )

        if template_file == "roadmap.yml":
            data = yaml.safe_load(content)
            if not is_active:
                data["status"]["active"] = False
                data["status"]["blocked"] = False
                data["status"]["started_at"] = None
                data["focus"]["current_task"] = None
                for task in data.get("tasks", []):
                    if task.get("status") == "active":
                        task["status"] = "pending"
            else:
                data["status"]["active"] = True
                data["status"]["blocked"] = False
                data["status"]["started_at"] = date.today().isoformat()

            destination.write_text(
                yaml.safe_dump(data, sort_keys=False), encoding="utf-8"
            )
        else:
            destination.write_text(content, encoding="utf-8")

    (step_dir / "sessions").mkdir(exist_ok=True)
    (step_dir / "sessions" / ".gitkeep").write_text("", encoding="utf-8")

    rel = step_dir.relative_to(repo_root)
    label = "active" if is_active else "pending"
    print(f"  Created step folder: {rel}/ ({label})")


def create_roadmap(
    name: str, steps: int, step_names: List[str], description: str = ""
) -> None:
    repo_root = Path.cwd()
    manager = RoadmapManager(repo_root)
    roadmaps_dir = manager.roadmaps_dir
    templates_dir = Path(__file__).parent / "templates"

    active = manager.find_active_roadmap()
    if active:
        print(f"ERROR: Step '{active['name']}' is already active")
        print("You must complete or deactivate it before creating a new roadmap")
        print(f"Active roadmap path: {active['path']}")
        sys.exit(1)

    if not validate_roadmap_name(name):
        print(f"ERROR: Invalid roadmap name '{name}'")
        print("Name must be lowercase with hyphens (e.g., strategy-validation)")
        sys.exit(1)

    for suffix in step_names:
        if not validate_roadmap_name(suffix):
            print(f"ERROR: Invalid step name '{suffix}'")
            print("Step names must be lowercase with hyphens (e.g., baseline)")
            sys.exit(1)

    roadmaps_dir.mkdir(parents=True, exist_ok=True)

    _write_series_readme(
        roadmaps_dir=roadmaps_dir,
        templates_dir=templates_dir,
        roadmap_name=name,
        description=description,
        step_names=step_names,
        repo_root=repo_root,
    )

    created_steps: List[Tuple[str, bool]] = []

    try:
        for index, suffix in enumerate(step_names):
            folder_name = f"step-{index}-{suffix}"
            step_title = suffix.replace("-", " ").title()
            task_prefix = f"task-{index}"
            is_active = index == 0
            dependencies = (
                [] if index == 0 else [f"step-{index - 1}-{step_names[index - 1]}"]
            )

            _create_step_folder(
                step_folder_name=folder_name,
                step_number=index,
                step_title=step_title,
                task_prefix=task_prefix,
                is_active=is_active,
                step_dependencies=dependencies,
                roadmaps_dir=roadmaps_dir,
                templates_dir=templates_dir,
                repo_root=repo_root,
            )
            created_steps.append((folder_name, is_active))

    except SystemExit:
        raise
    except Exception as exc:
        print(f"ERROR: Failed during step creation: {exc}")
        for folder_name, _ in created_steps:
            step_dir = roadmaps_dir / folder_name
            if step_dir.exists():
                shutil.rmtree(step_dir)
        sys.exit(1)

    print(f"\nRoadmap created with {len(created_steps)} step(s):")
    for folder_name, is_active in created_steps:
        status = "(active)" if is_active else "(pending)"
        print(f"  {folder_name}/  {status}")

    first_folder = created_steps[0][0]
    print("\nNext steps:")
    print("1. Edit each step's INVARIANTS.md, ROADMAP.md, roadmap.yml, and prompt.md")
    print("2. Confirm or adjust depends_on_steps and task-level depends_on values")
    print(f"3. Create branch: git checkout -b roadmap/{first_folder}")
    print(f"4. Validate: python3 .ai/scripts/roadmap/validate_schema.py {first_folder}")


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Create a dependency-aware roadmap step series.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  create.py strategy-rebuild\n"
            "  create.py strategy-rebuild --steps 3 --step-names baseline refactor rollout\n"
            "  create.py strategy-rebuild 'Quant stack overhaul' --steps 2 --step-names core hardening\n"
        ),
    )
    parser.add_argument("name", help="Roadmap slug (lowercase-hyphen format)")
    parser.add_argument(
        "description", nargs="?", default="", help="Optional roadmap description"
    )
    parser.add_argument(
        "--steps", type=int, default=1, metavar="N", help="Number of step folders"
    )
    parser.add_argument(
        "--step-names",
        nargs="+",
        metavar="NAME",
        help=(
            "Suffix for each step folder. Must match --steps count. "
            "If omitted: single step uses roadmap name; multi-step uses todo placeholders."
        ),
    )
    return parser.parse_args(argv)


def main(argv=None) -> None:
    check_session_initialized("roadmap")

    args = _parse_args(argv)

    if args.steps < 1:
        print("ERROR: --steps must be >= 1")
        sys.exit(1)

    if args.step_names:
        if len(args.step_names) != args.steps:
            print(
                f"ERROR: --step-names count ({len(args.step_names)}) "
                f"does not match --steps {args.steps}"
            )
            sys.exit(1)
        step_names = args.step_names
    else:
        if args.steps == 1:
            step_names = [args.name]
        else:
            step_names = [f"todo-{idx}" for idx in range(args.steps)]

    create_roadmap(
        name=args.name,
        steps=args.steps,
        step_names=step_names,
        description=args.description,
    )


if __name__ == "__main__":
    main()
