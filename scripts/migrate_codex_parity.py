#!/usr/bin/env python3
"""Migrate an existing repository to Codex parity-plus layout.

Usage:
    python3 scripts/migrate_codex_parity.py /path/to/repo [--force]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List, Tuple


def read_project_type(target: Path) -> str:
    yml = target / ".ai" / "project.yml"
    if not yml.exists():
        return "python"
    for line in yml.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("project_type:"):
            value = stripped.split(":", 1)[1].strip()
            if value in {"python", "cpp"}:
                return value
    return "python"


def copy_tree(src: Path, dst: Path, force: bool, changed: List[str], skipped: List[str]) -> None:
    if not src.exists():
        return

    dst.mkdir(parents=True, exist_ok=True)
    for src_file in src.rglob("*"):
        rel = src_file.relative_to(src)
        dst_file = dst / rel
        if src_file.is_dir():
            dst_file.mkdir(parents=True, exist_ok=True)
            continue

        if dst_file.exists() and not force:
            skipped.append(str(dst_file))
            continue

        dst_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_file, dst_file)
        changed.append(str(dst_file))


def copy_file(src: Path, dst: Path, force: bool, changed: List[str], skipped: List[str]) -> None:
    if dst.exists() and not force:
        skipped.append(str(dst))
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    changed.append(str(dst))


def migrate(source_root: Path, target_root: Path, force: bool) -> Tuple[List[str], List[str]]:
    changed: List[str] = []
    skipped: List[str] = []

    copy_tree(source_root / ".ai" / "tools", target_root / ".ai" / "tools", force, changed, skipped)
    copy_tree(source_root / ".codex", target_root / ".codex", force, changed, skipped)
    copy_tree(source_root / "bin", target_root / "bin", force, changed, skipped)

    project_type = read_project_type(target_root)
    codex_variant = "CODEX_PYTHON.md" if project_type == "python" else "CODEX_CPP.md"
    copy_file(source_root / codex_variant, target_root / "CODEX.md", force, changed, skipped)

    # Upgrade capabilities schema if target still uses legacy shape.
    target_manifest = target_root / ".ai" / "capabilities.yml"
    if target_manifest.exists():
        text = target_manifest.read_text()
        if "platform_requirements:" not in text:
            backup = target_manifest.with_suffix(".yml.bak")
            if not backup.exists() or force:
                shutil.copy2(target_manifest, backup)
                changed.append(str(backup))
            shutil.copy2(source_root / ".ai" / "capabilities.yml", target_manifest)
            changed.append(str(target_manifest))
    else:
        copy_file(source_root / ".ai" / "capabilities.yml", target_manifest, force, changed, skipped)

    return changed, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate repository to Codex parity-plus layout")
    parser.add_argument("target", nargs="?", default=".", help="Repository to migrate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parents[1]
    target_root = Path(args.target).resolve()

    changed, skipped = migrate(source_root, target_root, args.force)

    print("Codex parity migration complete.")
    print(f"Changed files: {len(changed)}")
    for path in changed:
        print(f"  + {path}")

    if skipped:
        print()
        print(f"Skipped existing files ({len(skipped)}). Re-run with --force to overwrite:")
        for path in skipped:
            print(f"  - {path}")

    print()
    print("Manual follow-up:")
    print("  1. Run: bin/agent-init --platform codex")
    print("  2. Run: bin/agent-precommit")
    print("  3. Review AGENTS.md/CLAUDE.md/CODEX.md alignment in your repo")


if __name__ == "__main__":
    main()
