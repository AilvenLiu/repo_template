#!/usr/bin/env python3
"""Migrate an existing repository to Codex parity-plus layout.

Usage:
    python3 scripts/migrate_codex_parity.py /path/to/repo [--force] [--backup]
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from typing import List, Tuple


CLAUDE_MIGRATION_PATHS = [
    Path(".claude/hooks"),
    Path(".claude/skills/common"),
    Path(".claude/skills/init"),
    Path(".claude/skills/check-constraints"),
    Path(".claude/skills/pre-commit"),
    Path(".claude/skills/dependency"),
    Path(".claude/skills/karpathy-guidelines"),
    Path(".claude/skills/roadmap"),
    Path(".claude/skills/build"),
    Path(".claude/skills/navigate"),
    Path(".claude/skills/context7"),
    Path(".claude/skills/python-env-setup"),
]


def _should_skip_relpath(rel: Path) -> bool:
    if any(part == "__pycache__" for part in rel.parts):
        return True
    if rel.suffix in {".pyc", ".pyo"}:
        return True
    if rel.name in {".DS_Store"}:
        return True
    return False


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
        if _should_skip_relpath(rel):
            continue
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


def migrate(source_root: Path, target_root: Path, force: bool, backup: bool) -> Tuple[List[str], List[str]]:
    changed: List[str] = []
    skipped: List[str] = []

    copy_tree(source_root / ".ai" / "constraints", target_root / ".ai" / "constraints", force, changed, skipped)
    copy_tree(source_root / ".ai" / "tools", target_root / ".ai" / "tools", force, changed, skipped)
    copy_tree(source_root / ".codex", target_root / ".codex", force, changed, skipped)
    copy_tree(source_root / "bin", target_root / "bin", force, changed, skipped)
    for rel_path in CLAUDE_MIGRATION_PATHS:
        copy_tree(source_root / rel_path, target_root / rel_path, force, changed, skipped)

    copy_file(source_root / ".claude" / "settings.json", target_root / ".claude" / "settings.json", force, changed, skipped)

    project_type = read_project_type(target_root)
    codex_variant = "CODEX_PYTHON.md" if project_type == "python" else "CODEX_CPP.md"
    copy_file(source_root / codex_variant, target_root / "CODEX.md", force, changed, skipped)

    if project_type == "cpp":
        cpp_python_env_skill = target_root / ".codex" / "skills" / "python-env-setup"
        if cpp_python_env_skill.is_dir():
            shutil.rmtree(cpp_python_env_skill)
        claude_python_env_skill = target_root / ".claude" / "skills" / "python-env-setup"
        if claude_python_env_skill.is_dir():
            shutil.rmtree(claude_python_env_skill)
        cpp_python_env_wrapper = target_root / "bin" / "agent-python-env-setup"
        if cpp_python_env_wrapper.exists():
            cpp_python_env_wrapper.unlink()

    # Upgrade capabilities schema if target still uses legacy shape.
    target_manifest = target_root / ".ai" / "capabilities.yml"
    if target_manifest.exists():
        text = target_manifest.read_text()
        if "platform_requirements:" not in text:
            backup_path = target_manifest.with_suffix(".yml.bak")
            if backup and (not backup_path.exists() or force):
                shutil.copy2(target_manifest, backup_path)
                changed.append(str(backup_path))
            shutil.copy2(source_root / ".ai" / "capabilities.yml", target_manifest)
            changed.append(str(target_manifest))
    else:
        copy_file(source_root / ".ai" / "capabilities.yml", target_manifest, force, changed, skipped)

    return changed, skipped


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate repository to Codex parity-plus layout")
    parser.add_argument("target", nargs="?", default=".", help="Repository to migrate")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create .ai/capabilities.yml.bak before legacy-manifest upgrade",
    )
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parents[1]
    target_root = Path(args.target).resolve()

    changed, skipped = migrate(source_root, target_root, args.force, args.backup)

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
    print("  3. If stale behavior persists, re-run migration with --force")
    print("  4. Review AGENTS.md/CLAUDE.md/CODEX.md alignment in your repo")


if __name__ == "__main__":
    main()
