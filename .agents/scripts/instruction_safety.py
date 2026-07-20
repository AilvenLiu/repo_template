#!/usr/bin/env python3
"""Detect instruction wording that conflicts with platform hierarchy."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class InstructionSafetyViolation:
    """One unsafe instruction pattern with a concrete remediation."""

    path: Path
    line: int
    rule: str
    reason: str
    remediation: str

    def format(self, root: Path) -> str:
        try:
            display_path = self.path.relative_to(root)
        except ValueError:
            display_path = self.path
        return (
            f"{display_path}:{self.line}: [{self.rule}] {self.reason}\n"
            f"  Remediation: {self.remediation}"
        )


@dataclass(frozen=True)
class _Rule:
    name: str
    pattern: re.Pattern[str]
    reason: str
    remediation: str


_RULES: tuple[_Rule, ...] = (
    _Rule(
        name="repository-overrides-platform",
        pattern=re.compile(
            r"\b(?:override(?:s|d|ing)?|supersede(?:s|d|ing)?)\b"
            r"[^\n]{0,100}\b(?:system|platform|model|hidden)\b",
            re.IGNORECASE,
        ),
        reason="Repository content appears to override a platform-level requirement.",
        remediation=(
            "Scope precedence to repository-controlled guidance and acknowledge "
            "higher-priority platform and tool requirements."
        ),
    ),
    _Rule(
        name="ignore-platform-instruction",
        pattern=re.compile(
            r"\b(?:ignore|disregard|bypass)\b[^\n]{0,100}"
            r"\b(?:system|platform|model|hidden)\b",
            re.IGNORECASE,
        ),
        reason="Instruction asks an agent to ignore a platform-level requirement.",
        remediation=(
            "State the repository policy directly and require reporting when a "
            "higher-priority requirement prevents compliance."
        ),
    ),
    _Rule(
        name="platform-ranked-below-repository",
        pattern=re.compile(
            r"\b(?:system|platform|model)(?:[- ]level)?\b[^\n]{0,80}"
            r"\b(?:lowest|lower[- ]priority)\b",
            re.IGNORECASE,
        ),
        reason="Hierarchy ranks platform guidance below repository content.",
        remediation=(
            "Describe the hierarchy as applying only among repository-controlled "
            "sources."
        ),
    ),
    _Rule(
        name="unscoped-all-instructions",
        pattern=re.compile(
            r"\b(?:override(?:s|d|ing)?|supersede(?:s|d|ing)?)\s+"
            r"(?:any|all|every)(?:\s+other)?\s+(?:instruction|instructions|prompt|prompts)\b",
            re.IGNORECASE,
        ),
        reason="Instruction claims unscoped authority over all instructions.",
        remediation=(
            "Name the repository-local sources governed by the rule and state its "
            "scope explicitly."
        ),
    ),
    _Rule(
        name="instruction-exposure-request",
        pattern=re.compile(
            r"\b(?:reveal|expose|reproduce|print|summari[sz]e)\b[^\n]{0,100}"
            r"\b(?:hidden|previous|prior|system)\b[^\n]{0,80}"
            r"\b(?:instruction|instructions|prompt|prompts)\b",
            re.IGNORECASE,
        ),
        reason="Instruction requests exposure of non-repository instructions.",
        remediation=(
            "Refer only to repository files the agent may inspect; do not request "
            "platform or prior-session instruction content."
        ),
    ),
)

_ROOT_FILES = (
    "AGENTS.md",
    "CLAUDE.md",
    "CONTRIBUTING.md",
    "README.md",
    ".agents/README.md",
)
_INSTRUCTION_DIRS = (
    "templates",
    ".agents/constraints",
    ".agents/skills",
    ".agents/scripts/roadmap/templates",
    ".claude/skills",
    ".claude/docs",
    ".claude/hooks",
    "agent_roadmaps",
    "docs",
)
_TEXT_SUFFIXES = {".md", ".yml", ".yaml", ".json", ".sh"}
_SKIP_PARTS = {".git", "__pycache__", ".pytest_cache", "tests", "build", "dist"}


def instruction_source_paths(repo_root: Path) -> list[Path]:
    """Return repository instruction surfaces, excluding tests and artefacts."""

    paths = [repo_root / name for name in _ROOT_FILES if (repo_root / name).is_file()]
    for relative_dir in _INSTRUCTION_DIRS:
        base = repo_root / relative_dir
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in _TEXT_SUFFIXES:
                continue
            if any(part in _SKIP_PARTS for part in path.relative_to(repo_root).parts):
                continue
            paths.append(path)
    return sorted(set(paths))


def _is_explicit_non_override(
    line: str, previous_line: str, match: re.Match[str]
) -> bool:
    """Permit explicit acknowledgements that repository guidance cannot override."""

    prefix = line[max(0, match.start() - 28) : match.start()].lower()
    if any(phrase in prefix for phrase in ("does not", "do not", "cannot", "can't")):
        return True
    return (
        previous_line.rstrip()
        .lower()
        .endswith(("does not", "do not", "cannot", "can't"))
    )


def scan_text(path: Path, text: str) -> list[InstructionSafetyViolation]:
    """Scan one instruction file without interpreting test fixtures or code."""

    violations: list[InstructionSafetyViolation] = []
    lines = text.splitlines()
    for line_number, line in enumerate(lines, start=1):
        for rule in _RULES:
            match = rule.pattern.search(line)
            if match is None:
                continue
            previous_line = lines[line_number - 2] if line_number > 1 else ""
            if (
                rule.name == "repository-overrides-platform"
                and _is_explicit_non_override(line, previous_line, match)
            ):
                continue
            violations.append(
                InstructionSafetyViolation(
                    path=path,
                    line=line_number,
                    rule=rule.name,
                    reason=rule.reason,
                    remediation=rule.remediation,
                )
            )
    return violations


def scan(repo_root: Path) -> list[InstructionSafetyViolation]:
    """Scan canonical template sources or a freshly generated project."""

    violations: list[InstructionSafetyViolation] = []
    for path in instruction_source_paths(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        violations.extend(scan_text(path, text))
    return violations


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check repository instruction surfaces for unsafe hierarchy wording."
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    root = args.root.resolve()
    violations = scan(root)
    if not violations:
        print("Instruction-safety check passed.")
        return 0

    print("Unsafe instruction wording detected:")
    for violation in violations:
        print(violation.format(root))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
