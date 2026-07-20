#!/usr/bin/env python3
"""Cross-platform repository skill and wrapper verification.

Verifies the repo-bundled assets that make skills and constraints discoverable
for both Claude Code and AGENTS.md-based platforms (Codex, Cursor, Cline, etc.).

Usage:
    python3 .agents/scripts/common/verify_skills.py
    python3 .agents/scripts/common/verify_skills.py --platform claude
    python3 .agents/scripts/common/verify_skills.py --platform codex
    python3 .agents/scripts/common/verify_skills.py --platform both
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from capability_audit import (  # type: ignore[import-not-found]  # noqa: E402
    _entry_enabled_for_repo,
    _is_template_repo,
    _load_manifest,
    _normalize_manifest,
)


def _has_valid_skill_frontmatter(content: str, expected_name: str) -> tuple[bool, str]:
    """Check that a canonical skill or platform stub has valid frontmatter."""
    if not content.startswith("---"):
        return False, "missing YAML frontmatter"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False, "invalid YAML frontmatter format"

    frontmatter_text = parts[1]

    if yaml is not None:
        try:
            parsed = yaml.safe_load(frontmatter_text)
        except yaml.YAMLError as exc:
            return False, f"invalid YAML frontmatter: {exc}"

        if not isinstance(parsed, dict):
            return False, "frontmatter did not parse to a mapping"
        if not parsed.get("name"):
            return False, "frontmatter missing name"
        if not parsed.get("description"):
            return False, "frontmatter missing description"
        if str(parsed["name"]).strip() != expected_name:
            return False, f"frontmatter name mismatch: expected '{expected_name}'"
        return True, ""

    if not re.search(r"(?m)^name:\s*\S+", frontmatter_text):
        return False, "frontmatter missing name"
    if not re.search(r"(?m)^description:\s*.+", frontmatter_text):
        return False, "frontmatter missing description"
    return True, ""


class RepoVerifier:
    """Verify repo-bundled platform assets."""

    def __init__(self, repo_root: Path, platform: str):
        self.repo_root = repo_root
        self.platform = platform
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.checked: list[str] = []

    def verify_all(self) -> bool:
        print("=" * 70)
        print("REPOSITORY SKILL + WRAPPER VERIFICATION")
        print("=" * 70)
        print(f"Repo: {self.repo_root}")
        print(f"Platform: {self.platform}")
        print()

        manifest = _normalize_manifest(
            _load_manifest(self.repo_root / ".agents" / "capabilities.yml")
        )
        is_template = _is_template_repo(self.repo_root)

        self._verify_entrypoints()
        self._verify_skills(manifest, is_template)
        self._verify_wrappers(manifest, is_template)
        self._verify_no_legacy_codex_tree()

        self._print_results()
        return not self.errors

    def _record_success(self, label: str) -> None:
        self.checked.append(label)

    def _verify_entrypoints(self) -> None:
        agents = self.repo_root / "AGENTS.md"
        if agents.is_file():
            self._record_success("AGENTS.md")
        else:
            self.errors.append("Missing AGENTS.md entrypoint")

        claude = self.repo_root / "CLAUDE.md"
        if claude.is_file():
            self._record_success("CLAUDE.md")
        else:
            self.errors.append("Missing CLAUDE.md entrypoint")

    def _verify_skills(self, manifest: dict[str, Any], is_template: bool) -> None:
        entries = manifest.get("common_requirements", {}).get("project_skills", [])
        if not isinstance(entries, list):
            self.errors.append("Capability manifest project_skills section is invalid")
            return

        for raw_entry in entries:
            entry = raw_entry if isinstance(raw_entry, dict) else {}
            if not _entry_enabled_for_repo(entry, is_template, self.repo_root):
                continue

            skill_id = str(entry.get("id", "")).strip()
            if not skill_id or not entry.get("required", False):
                continue

            agents_skill = self.repo_root / ".agents" / "skills" / skill_id / "SKILL.md"
            claude_skill = self.repo_root / ".claude" / "skills" / skill_id / "SKILL.md"

            if not is_template:
                agents_content = (self.repo_root / "AGENTS.md").read_text(
                    encoding="utf-8"
                )
                if skill_id not in agents_content:
                    self.errors.append(
                        f"AGENTS.md does not expose required skill: {skill_id}"
                    )
                if self.platform in {"claude", "both"}:
                    claude_content = (self.repo_root / "CLAUDE.md").read_text(
                        encoding="utf-8"
                    )
                    if skill_id not in claude_content:
                        self.errors.append(
                            f"CLAUDE.md does not expose required skill: {skill_id}"
                        )

            if not agents_skill.is_file():
                self.errors.append(f"Missing canonical skill body: {agents_skill}")
            elif not (
                agents_content := agents_skill.read_text(encoding="utf-8")
            ).strip():
                self.errors.append(f"Empty canonical skill body: {agents_skill}")
            else:
                valid, reason = _has_valid_skill_frontmatter(agents_content, skill_id)
                if not valid:
                    self.errors.append(
                        f"Invalid canonical skill {agents_skill}: {reason}"
                    )
                else:
                    self._record_success(f".agents/skills/{skill_id}/SKILL.md")

            if self.platform in {"claude", "both"}:
                if not claude_skill.is_file():
                    self.errors.append(f"Missing Claude skill stub: {claude_skill}")
                    continue

                content = claude_skill.read_text(encoding="utf-8")
                if not content.strip():
                    self.errors.append(f"Empty Claude skill stub: {claude_skill}")
                    continue

                valid, reason = _has_valid_skill_frontmatter(content, skill_id)
                if not valid:
                    self.errors.append(
                        f"Invalid Claude skill stub {claude_skill}: {reason}"
                    )
                    continue

                canonical_ref = f".agents/skills/{skill_id}/SKILL.md"
                if canonical_ref not in content:
                    self.errors.append(
                        f"Claude skill stub does not delegate to {canonical_ref}: "
                        f"{claude_skill}"
                    )
                    continue

                self._record_success(f".claude/skills/{skill_id}/SKILL.md")

    def _verify_wrappers(self, manifest: dict[str, Any], is_template: bool) -> None:
        entries = manifest.get("common_requirements", {}).get("repo_commands", [])
        if not isinstance(entries, list):
            self.errors.append("Capability manifest repo_commands section is invalid")
            return

        for raw_entry in entries:
            entry = raw_entry if isinstance(raw_entry, dict) else {}
            if not _entry_enabled_for_repo(entry, is_template, self.repo_root):
                continue

            command_id = str(entry.get("id", "")).strip()
            rel_path = str(entry.get("path", "")).strip()
            required = bool(entry.get("required", False))

            if not command_id or not rel_path or not required:
                continue

            command_path = self.repo_root / rel_path
            if not command_path.is_file():
                self.errors.append(f"Missing wrapper: {command_path}")
                continue

            if bool(entry.get("executable", False)) and not (
                command_path.stat().st_mode & 0o111
            ):
                self.errors.append(f"Wrapper is not executable: {command_path}")
                continue

            self._record_success(rel_path)

    def _verify_no_legacy_codex_tree(self) -> None:
        legacy = self.repo_root / ".codex" / "skills"
        if legacy.exists():
            self.errors.append(
                "Legacy .codex/skills present; Codex skills must use .agents/skills/"
            )

    def _print_results(self) -> None:
        print("=" * 70)
        print("RESULTS")
        print("=" * 70)
        print(f"Checked assets: {len(self.checked)}")

        if self.warnings:
            print(f"Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  [WARN] {warning}")

        if self.errors:
            print(f"Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  [ERROR] {error}")
            print()
            print("Verification failed.")
        else:
            print("Errors: 0")
            print()
            print("Verification passed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify repo skill and wrapper assets")
    parser.add_argument(
        "--platform",
        choices=["claude", "codex", "both"],
        default="both",
        help="Platform asset surface to verify",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    repo_root = script_path.parents[3]

    verifier = RepoVerifier(repo_root, args.platform)
    success = verifier.verify_all()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
