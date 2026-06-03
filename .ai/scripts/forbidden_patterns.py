#!/usr/bin/env python3
"""Scan source files for patterns forbidden by .ai/constraints/*.

Catches things the declarative constraints *document* as forbidden but that
previously had no runtime enforcement in pre-commit / check-constraints.

Each finding is reported with (path, line, category, snippet, remediation).
False positives are reduced by:
  - skipping .git, __pycache__, .venv, build dirs, test fixtures
  - line-level regexes bound to the violation shape, not substrings
  - per-category allowlist comments: append `# ai-allow: <category>` on the
    offending line to suppress (for intentional test fixtures, etc.)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

try:
    from .paths import resolve_repo_root
    from .project_type import ProjectType, detect
except ImportError:  # script-mode
    from paths import resolve_repo_root
    from project_type import ProjectType, detect


@dataclass
class Finding:
    path: Path
    line_no: int
    category: str
    message: str
    snippet: str
    remediation: str

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "line": self.line_no,
            "category": self.category,
            "message": self.message,
            "snippet": self.snippet.strip(),
            "remediation": self.remediation,
        }


SKIP_DIR_PARTS = {
    ".git",
    "__pycache__",
    ".venv",
    "venv",
    "build",
    "cmake-build-debug",
    "cmake-build-release",
    "node_modules",
    "dist",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "agent_roadmaps",
    ".ai",
    ".claude",
    ".codex",
    "tests",  # seeded violations live in test fixtures; users opt-in via --include-tests
}

ALLOW_PRAGMA = re.compile(r"#\s*ai-allow\s*:\s*(?P<category>[a-zA-Z0-9_-]+)")


def _scannable_files(
    root: Path, suffixes: set[str], include_tests: bool
) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix not in suffixes:
            continue
        parts = set(path.relative_to(root).parts)
        if not include_tests and parts & SKIP_DIR_PARTS:
            continue
        # still skip hidden/machine dirs even when including tests
        if parts & (SKIP_DIR_PARTS - {"tests"}):
            continue
        yield path


def _line_allowed(line: str, category: str) -> bool:
    match = ALLOW_PRAGMA.search(line)
    return bool(match and match.group("category") == category)


# ---------------------------------------------------------------------------
# Python rules
# ---------------------------------------------------------------------------

_PY_RULES: List[tuple[str, re.Pattern[str], str, str]] = [
    (
        "bare-except",
        re.compile(r"^\s*except\s*:\s*(#.*)?$"),
        "Bare `except:` clause",
        "Catch a specific exception class.",
    ),
    (
        "eval-exec",
        re.compile(r"(?<![A-Za-z0-9_])(eval|exec)\s*\("),
        "Use of eval()/exec()",
        "Replace with explicit parsing or a safe dispatch table.",
    ),
    (
        "pip-install",
        # Match both shell-level `pip install` and string-embedded
        # `"pip install ..."` / `'pip install ...'` that end up executed by subprocess.
        re.compile(r"""(?:^|[\s'"])(pip3?\s+install)\b"""),
        "Direct `pip install` invocation",
        "Use Poetry (poetry add) or the /dependency skill.",
    ),
    (
        "shell-true-user-input",
        re.compile(r"subprocess\.[A-Za-z_]+\([^)]*shell\s*=\s*True[^)]*"),
        "subprocess shell=True (review for user-controlled input)",
        "Avoid shell=True; pass argv as a list.",
    ),
]


_PY_SECRET_RULES: List[tuple[str, re.Pattern[str], str, str]] = [
    (
        "hardcoded-secret",
        re.compile(
            r"""(?ix)
            (?P<name>api[_-]?key|secret|password|token|access[_-]?key)
            \s*=\s*
            ['"](?P<value>[A-Za-z0-9_\-]{16,})['"]
            """
        ),
        "Hardcoded secret-like literal",
        "Move to environment variable or secret store; rotate if already committed.",
    ),
]


_MUTABLE_DEFAULT = re.compile(r"def\s+\w+\s*\([^)]*=\s*(\[\]|\{\}|set\(\))")


def _scan_python_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(lines, start=1):
        for cat, pat, msg, rem in _PY_RULES + _PY_SECRET_RULES:
            if pat.search(line) and not _line_allowed(line, cat):
                findings.append(Finding(path, idx, cat, msg, line, rem))

    # Multi-line: mutable default (single-line regex still works but keep separate for clarity)
    for idx, line in enumerate(lines, start=1):
        if _MUTABLE_DEFAULT.search(line) and not _line_allowed(line, "mutable-default"):
            findings.append(
                Finding(
                    path,
                    idx,
                    "mutable-default",
                    "Mutable default argument",
                    line,
                    "Use None and create the container inside the function.",
                )
            )

    return findings


# ---------------------------------------------------------------------------
# C++ / CUDA rules
# ---------------------------------------------------------------------------


_CPP_RULES: List[tuple[str, re.Pattern[str], str, str]] = [
    (
        "raw-new",
        re.compile(r"(?<![A-Za-z_])new\s+[A-Za-z_][\w:<>,\s]*\s*(?:\(|\[)"),
        "Raw `new` allocation",
        "Use std::make_unique / std::make_shared.",
    ),
    (
        "raw-delete",
        re.compile(r"(?<![A-Za-z_])delete(?:\s*\[\s*\])?\s+[A-Za-z_]"),
        "Raw `delete`",
        "Let RAII / smart pointers manage lifetime.",
    ),
    (
        "c-style-cast",
        # `(type) expr` — match RHS of assignment, return, or argument position.
        # Allow numeric literals, identifiers, and `(` after the cast.
        re.compile(
            r"(?:=|return|,|\()\s*\(\s*(?:const\s+|volatile\s+)?"
            r"(?:unsigned\s+|signed\s+)?"
            r"(?:void|bool|char|int|short|long|float|double|size_t|uint\d+_t|int\d+_t)"
            r"(?:\s*\*+)?\s*\)\s*[A-Za-z_0-9(\-]"
        ),
        "C-style cast",
        "Use static_cast / reinterpret_cast / dynamic_cast.",
    ),
    (
        "cuda-error-ignored",
        # cudaXxx(...) on its own statement, not assigned to a checked status var
        # and not wrapped by CUDA_CHECK / cuda_check / etc.
        re.compile(r"^\s*cuda[A-Z][A-Za-z0-9_]*\s*\(.*\)\s*;\s*(?://.*)?$"),
        "CUDA call with no error check",
        "Wrap with CUDA_CHECK / cudaGetLastError / explicit error handling.",
    ),
]


_ROADMAP_RESIDUE_RULES: List[tuple[str, re.Pattern[str], str, str]] = [
    (
        "roadmap-step-label",
        re.compile(
            r"(?:^|[^A-Za-z0-9_])"
            r"(phase-\d+(?:-[a-z0-9-]+)?|roadmap/phase-\d+(?:-[a-z0-9-]+)?|"
            r"step-\d+(?:-[a-z0-9-]+)?|roadmap/step-\d+(?:-[a-z0-9-]+)?)"
        ),
        "Roadmap-step identifier leaked into a durable project file",
        "Keep roadmap labels inside agent_roadmaps/ only, or remove the temporary roadmap reference.",
    ),
]


def _scan_cpp_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if (
            stripped.startswith("//")
            or stripped.startswith("/*")
            or stripped.startswith("*")
        ):
            continue
        for cat, pat, msg, rem in _CPP_RULES:
            if pat.search(line) and not _line_allowed(line, cat):
                findings.append(Finding(path, idx, cat, msg, line, rem))

    return findings


def _scan_roadmap_residue_file(path: Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return findings

    for idx, line in enumerate(lines, start=1):
        for cat, pat, msg, rem in _ROADMAP_RESIDUE_RULES:
            if pat.search(line) and not _line_allowed(line, cat):
                findings.append(Finding(path, idx, cat, msg, line, rem))

    return findings


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def scan(
    repo_root: Path, project_type: ProjectType, include_tests: bool = False
) -> List[Finding]:
    findings: List[Finding] = []

    if project_type == ProjectType.PYTHON:
        for file in _scannable_files(repo_root, {".py"}, include_tests):
            findings.extend(_scan_python_file(file))
    elif project_type == ProjectType.CPP:
        for file in _scannable_files(
            repo_root,
            {".cpp", ".hpp", ".cc", ".hh", ".h", ".cu", ".cuh"},
            include_tests,
        ):
            findings.extend(_scan_cpp_file(file))
    else:
        # best effort: scan all recognised files
        for file in _scannable_files(repo_root, {".py"}, include_tests):
            findings.extend(_scan_python_file(file))
        for file in _scannable_files(
            repo_root,
            {".cpp", ".hpp", ".cc", ".hh", ".h", ".cu", ".cuh"},
            include_tests,
        ):
            findings.extend(_scan_cpp_file(file))

    roadmap_suffixes = {
        ".py",
        ".cpp",
        ".hpp",
        ".cc",
        ".hh",
        ".h",
        ".cu",
        ".cuh",
        ".md",
        ".rst",
        ".toml",
        ".yml",
        ".yaml",
        ".json",
        ".ini",
        ".cfg",
        ".txt",
        ".sh",
    }
    for file in _scannable_files(repo_root, roadmap_suffixes, include_tests):
        findings.extend(_scan_roadmap_residue_file(file))

    return findings


def print_report(findings: List[Finding]) -> None:
    if not findings:
        print("No forbidden patterns detected.")
        return

    print("=" * 70)
    print(f"FORBIDDEN PATTERN FINDINGS: {len(findings)}")
    print("=" * 70)
    by_category: dict[str, list[Finding]] = {}
    for f in findings:
        by_category.setdefault(f.category, []).append(f)

    for category in sorted(by_category):
        group = by_category[category]
        print(f"\n[{category}] ({len(group)} hit(s))")
        for f in group:
            print(f"  {f.path}:{f.line_no}  {f.message}")
            print(f"    > {f.snippet.strip()}")
            print(f"    fix: {f.remediation}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Forbidden pattern scanner")
    parser.add_argument(
        "--project-type",
        choices=["auto", "python", "cpp"],
        default="auto",
    )
    parser.add_argument("--include-tests", action="store_true", help="Also scan tests/")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root(Path(__file__).resolve())
    project_type = (
        detect(repo_root)
        if args.project_type == "auto"
        else ProjectType(args.project_type)
    )

    findings = scan(repo_root, project_type, include_tests=args.include_tests)

    if args.json:
        print(
            json.dumps(
                {
                    "project_type": project_type.value,
                    "findings": [f.to_dict() for f in findings],
                },
                indent=2,
            )
        )
    else:
        print_report(findings)

    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
