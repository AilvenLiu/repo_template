#!/usr/bin/env python3
"""Cross-platform session initialization for Claude and Codex."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:  # pragma: no cover - fallback for minimal environments
    yaml = None

try:
    from .capability_audit import AuditResult, print_audit_report, run_audit
    from .constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from .paths import resolve_repo_root
    from .project_profile import Language, ProjectProfile, detect
    from .session_state import write_state
except ImportError:
    from capability_audit import AuditResult, print_audit_report, run_audit
    from constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from paths import resolve_repo_root
    from project_profile import Language, ProjectProfile, detect
    from session_state import write_state


def _repo_root() -> Path:
    return resolve_repo_root(Path(__file__).resolve())


def git_current_branch(repo_root: Path) -> Optional[str]:
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
    except FileNotFoundError:
        return None

    return result.stdout.strip() if result.returncode == 0 else None


def git_modified_files(repo_root: Path) -> List[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            capture_output=True,
            text=True,
            cwd=repo_root,
        )
    except FileNotFoundError:
        return []

    if result.returncode != 0:
        return []

    return [line for line in result.stdout.splitlines() if line.strip()]


def find_active_roadmap(repo_root: Path) -> Optional[Path]:
    roadmaps_dir = repo_root / "agent_roadmaps"
    if not roadmaps_dir.is_dir():
        return None

    active_candidates: List[Path] = []

    for roadmap_file in sorted(roadmaps_dir.rglob("roadmap.yml")):
        if "template" in roadmap_file.parts:
            continue
        child = roadmap_file.parent
        if not child.is_dir():
            continue

        try:
            content = roadmap_file.read_text(encoding="utf-8")
        except OSError:
            continue

        parsed = None
        if yaml is not None:
            try:
                parsed = yaml.safe_load(content)
            except yaml.YAMLError:
                parsed = None

        is_active = False

        if isinstance(parsed, dict):
            status = parsed.get("status")
            if isinstance(status, dict):
                active_flag = status.get("active")
                if isinstance(active_flag, bool):
                    is_active = active_flag
                elif isinstance(active_flag, str):
                    is_active = active_flag.strip().lower() in {"true", "active", "in_progress"}
            elif isinstance(status, str):
                is_active = status.strip().lower() in {"active", "in_progress"}

        # Fallback for malformed/legacy files that still use plaintext markers.
        if not is_active and ("status: active" in content or "status: in_progress" in content):
            is_active = True

        if is_active:
            active_candidates.append(child)

    return active_candidates[0] if active_candidates else None


_ALWAYS_COMMON = [
    "common/git-workflow",
    "common/session-discipline",
    "common/karpathy-guidelines",
    "common/mcp-integration",
    "common/ascii-only",
    "common/agentic-team",
]
_ALWAYS_PYTHON = [
    "python/dependencies",
    "python/forbidden-practices",
    "python/security",
    "python/error-handling",
]
_ALWAYS_CPP = [
    "cpp/dependencies",
    "cpp/forbidden-practices",
    "cpp/error-handling",
    "cpp/static-analysis",
]

_PYTHON_TRIGGERS = {
    ".py": ["python/formatting", "python/type-checking"],
}
_CPP_TRIGGERS = {
    ".cpp": ["cpp/formatting", "cpp/memory-safety"],
    ".hpp": ["cpp/formatting", "cpp/memory-safety"],
    ".cu": ["cpp/cuda", "cpp/cuda-modern", "cpp/kernel-correctness"],
    ".cuh": ["cpp/cuda", "cpp/cuda-modern", "cpp/kernel-correctness"],
}

_DOC_FILENAMES = {
    "README.md",
    "CONTRIBUTING.md",
    "AGENTS.md",
    "CLAUDE.md",
}


def _is_test_path(path: str) -> bool:
    lowered = path.lower()
    return (
        "test" in lowered
        or lowered.endswith("pytest.ini")
        or lowered.endswith("tox.ini")
        or lowered.endswith("conftest.py")
    )


def _is_doc_path(path: str) -> bool:
    pure = Path(path)
    lowered = path.lower()
    return (
        pure.name in _DOC_FILENAMES
        or lowered.startswith("docs/")
        or pure.suffix in {".md", ".rst"}
    )


def _is_cmake_path(path: str) -> bool:
    pure = Path(path)
    lowered = path.lower()
    return (
        pure.name == "CMakeLists.txt"
        or pure.suffix == ".cmake"
        or lowered.startswith("cmake/")
    )


def resolve_constraints(
    profile: ProjectProfile,
    modified_files: List[str],
    has_roadmap: bool,
) -> List[str]:
    keys = list(_ALWAYS_COMMON)
    if has_roadmap:
        keys.append("common/roadmap-awareness")

    # Load constraints for each language in the profile
    exts_seen = {Path(path).suffix for path in modified_files}

    if profile.has_language(Language.PYTHON):
        keys.extend(_ALWAYS_PYTHON)
        for ext, extra in _PYTHON_TRIGGERS.items():
            if ext in exts_seen:
                keys.extend(extra)
        if any(_is_test_path(path) for path in modified_files):
            keys.append("python/testing")
        if any(_is_doc_path(path) for path in modified_files):
            keys.append("python/documentation")

    if profile.has_language(Language.CPP):
        keys.extend(_ALWAYS_CPP)
        for ext, extra in _CPP_TRIGGERS.items():
            if ext in exts_seen:
                keys.extend(extra)
        if any(_is_cmake_path(path) for path in modified_files):
            keys.append("cpp/cmake")
        if any(_is_test_path(path) for path in modified_files):
            keys.append("cpp/testing")
        if any(_is_doc_path(path) for path in modified_files):
            keys.append("cpp/documentation")

    # Load hybrid constraints when both Python and C++ are present
    if profile.has_language(Language.PYTHON) and profile.has_language(Language.CPP):
        keys.append("hybrid/ffi-boundary")

    deduped: List[str] = []
    seen = set()
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        deduped.append(key)
    return deduped


def load_constraint(repo_root: Path, key: str) -> Optional[str]:
    path = repo_root / ".ai" / "constraints" / f"{key}.md"
    if not path.exists():
        return None
    try:
        return path.read_text()
    except OSError:
        return None


def write_session_state(
    repo_root: Path,
    platform: str,
    profile: ProjectProfile,
    branch: Optional[str],
    loaded_constraints: List[str],
    roadmap_dir: Optional[Path],
    audit_result: AuditResult,
) -> None:
    payload: Dict[str, Any] = {
        "initialized": True,
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "project_profile": profile.to_dict(),
        "branch": branch,
        "loaded_constraints": loaded_constraints,
        "active_roadmap": str(roadmap_dir) if roadmap_dir else None,
        "capability_audit": audit_result.to_dict(),
    }
    write_state(repo_root, payload)


def run_init(platform: str, verbose: bool = False) -> int:
    repo_root = _repo_root()
    effective_verbose = verbose or platform == "claude"

    separator = "=" * 70
    print(separator)
    print("SESSION INITIALIZATION")
    print(separator)

    profile = detect(repo_root)
    if profile is None:
        print("[WARN] Unable to detect project profile. Defaulting to python.")
        from .project_profile import legacy_project_type_to_profile
        profile = legacy_project_type_to_profile("python")

    project_yml = repo_root / ".ai" / "project.yml"
    source = ".ai/project.yml" if project_yml.exists() else "heuristic"

    # Display primary language for backward compatibility with existing output format
    primary_lang = profile.language[0].value.upper() if profile.language else "UNKNOWN"
    print(f"[OK] Project type: {primary_lang} ({source})")

    roadmap_dir = find_active_roadmap(repo_root)
    if roadmap_dir:
        print(f"[OK] Active roadmap: {roadmap_dir.name}")
    else:
        print("[--] No active roadmap")

    branch = git_current_branch(repo_root)
    if branch:
        if branch in PROTECTED_BRANCHES or any(branch.startswith(p) for p in PROTECTED_PREFIXES):
            print(f"[WARN] Branch: {branch} (protected)")
        else:
            print(f"[OK] Branch: {branch}")

    modified = git_modified_files(repo_root)
    if modified:
        print(f"[OK] {len(modified)} modified file(s)")

    print()
    print(separator)
    print("CAPABILITY AUDIT")
    print(separator)

    audit_result = run_audit(repo_root, platform=platform, verbose=False)
    print_audit_report(audit_result)

    keys = resolve_constraints(profile, modified, roadmap_dir is not None)
    loaded: List[str] = []

    print(separator)
    print("LOADED CONSTRAINTS")
    print(separator)

    for key in keys:
        body = load_constraint(repo_root, key)
        if body is None:
            print(f"[MISS] {key}")
            continue
        loaded.append(key)
        if effective_verbose:
            print(f"[CONSTRAINT] {key}")
            print(body)
            print()
        else:
            print(f"[OK] {key}")

    write_session_state(
        repo_root=repo_root,
        platform=platform,
        profile=profile,
        branch=branch,
        loaded_constraints=loaded,
        roadmap_dir=roadmap_dir,
        audit_result=audit_result,
    )

    print()
    print(separator)
    print(f"Total constraints loaded: {len(loaded)}")
    print(separator)

    if not audit_result.passed:
        print("Session is BLOCKED due to failed capability audit.")
        return 1

    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-platform session init")
    parser.add_argument("--platform", choices=["claude", "codex"], default="codex")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    code = run_init(platform=args.platform, verbose=args.verbose)
    sys.exit(code)


if __name__ == "__main__":
    main()
