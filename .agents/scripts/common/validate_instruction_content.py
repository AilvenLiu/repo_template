#!/usr/bin/env python3
"""Fail when repository instructions teach known policy-breaking commands."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    rule: str
    text: str


RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "mutable-action-ref",
        re.compile(r"(?i)\buses:\s+[^\s]+@(v\d+(?:\.\d+)*|main|master)\b"),
    ),
    (
        "direct-pip-command",
        re.compile(
            r"^\s*(?:pip\d*(?:\.\d+)?|python\d*(?:\.\d+)?\s+-m\s+pip)\s+install\b"
        ),
    ),
    (
        "direct-poetry-dependency-command",
        re.compile(r"^\s*poetry\s+(?:add|remove|update)\b"),
    ),
    (
        "manual-venv-command",
        re.compile(r"^\s*python\d*(?:\.\d+)?\s+-m\s+venv\b"),
    ),
    ("disabled-ssh-host-check", re.compile(r"StrictHostKeyChecking\s*=\s*no")),
    ("unsafe-tempfile", re.compile(r"\btempfile\.mktemp\s*\(")),
)

INSTRUCTION_ROOTS = (
    Path(".agents/skills"),
    Path(".agents/constraints"),
    Path(".claude/skills"),
    Path(".claude/docs"),
    Path("templates"),
)


def scan(repo_root: Path) -> list[Finding]:
    """Return forbidden instructional patterns from checked-in Markdown."""
    findings: list[Finding] = []
    for relative_root in INSTRUCTION_ROOTS:
        root = repo_root / relative_root
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.md")):
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8", errors="replace").splitlines(),
                start=1,
            ):
                for rule, pattern in RULES:
                    if pattern.search(line):
                        findings.append(
                            Finding(
                                path=path.relative_to(repo_root),
                                line=line_number,
                                rule=rule,
                                text=line.strip(),
                            )
                        )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate that agent instructions do not teach forbidden commands"
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
    )
    args = parser.parse_args()

    findings = scan(args.repo_root.resolve())
    if findings:
        print("Instruction-content validation failed:")
        for finding in findings:
            print(f"  {finding.path}:{finding.line}: [{finding.rule}] {finding.text}")
        return 1

    print("Instruction-content validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
