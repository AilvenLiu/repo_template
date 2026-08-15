#!/usr/bin/env python3
"""Cross-platform constraint checks used by wrappers and CI."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    from .constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from .instruction_safety import scan as scan_instruction_safety
    from .paths import resolve_repo_root
    from .project_profile import BuildSystem, Language, ProjectProfile, detect
except ImportError:
    from constants import PROTECTED_BRANCHES, PROTECTED_PREFIXES
    from instruction_safety import scan as scan_instruction_safety
    from paths import resolve_repo_root
    from project_profile import BuildSystem, Language, ProjectProfile, detect


@dataclass
class Violation:
    category: str
    severity: str
    message: str
    remediation: str

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "remediation": self.remediation,
        }


def _run(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, cwd=cwd)


def _current_branch(repo_root: Path) -> str:
    proc = _run(["git", "branch", "--show-current"], repo_root)
    return proc.stdout.strip() if proc.returncode == 0 else ""


def _is_protected_branch(branch: str) -> bool:
    return branch in PROTECTED_BRANCHES or any(
        branch.startswith(prefix) for prefix in PROTECTED_PREFIXES
    )


def _check_git(repo_root: Path) -> List[Violation]:
    violations: List[Violation] = []
    branch = _current_branch(repo_root)
    if branch and _is_protected_branch(branch):
        violations.append(
            Violation(
                category="Git Workflow",
                severity="CRITICAL",
                message=f"On protected branch: {branch}",
                remediation="Create a feature branch before committing.",
            )
        )
    return violations


def _check_python(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations: List[Violation] = []

    pyproject = repo_root / "pyproject.toml"
    poetry_lock = repo_root / "poetry.lock"
    if (
        profile.build_system == BuildSystem.POETRY
        and pyproject.exists()
        and not poetry_lock.exists()
    ):
        violations.append(
            Violation(
                category="Dependency Management",
                severity="CRITICAL",
                message="Poetry project missing poetry.lock",
                remediation="Run `poetry lock` and commit poetry.lock.",
            )
        )

    if pyproject.exists():
        text = pyproject.read_text()
        if 'python = "^3.9"' in text or 'python = ">=3.9"' in text:
            violations.append(
                Violation(
                    category="Dependency Management",
                    severity="CRITICAL",
                    message="Python version requirement below 3.10",
                    remediation="Set Python requirement to 3.10+.",
                )
            )

    return violations


def _check_cpp(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations: List[Violation] = []

    cmake = repo_root / "CMakeLists.txt"
    cpm_files = [
        repo_root / "cmake" / "CPM.cmake",
        repo_root / "cmake" / "Dependencies.cmake",
        repo_root / "cmake" / "Options.cmake",
        repo_root / "3rdparty" / "cpm-cache" / ".gitkeep",
    ]
    missing = [path for path in cpm_files if not path.exists()]
    if cmake.exists() and profile.has_language(Language.CPP) and missing:
        violations.append(
            Violation(
                category="Dependency Management",
                severity="CRITICAL",
                message="C++ project missing CMake/CPM dependency layout",
                remediation=(
                    "Add cmake/CPM.cmake, cmake/Dependencies.cmake, "
                    "cmake/Options.cmake, and 3rdparty/cpm-cache/.gitkeep."
                ),
            )
        )

    return violations


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


_ARTIFACT_EXCEPTION_PATH = Path(".agents/github-artifact-exceptions.json")
_ARTIFACT_ACTION_RE = re.compile(
    r"""(?im)^(?P<uses_indent>[ \t]*)(?:-[ \t]+)?uses:[ \t]*["']?(?P<surface>actions/(?:upload(?:-pages)?|download)-artifact)\b(?:@(?P<ref>[^ \t\r\n#"']+))?"""
)
_ARTIFACT_RUN_DOWNLOAD_RE = re.compile(r"(?im)^[^#\n]*\bgh[ \t]+run[ \t]+download\b")
_ARTIFACT_API_RE = re.compile(
    r"(?im)^[^#\n]*\b(?:repos/[^\s\"']+/actions/artifacts|actions/runs/[^/\s]+/artifacts)\b"
)
_UNINSPECTABLE_ARTIFACT_SURFACES = frozenset(
    {"gh run download", "github-actions-artifact-api"}
)
_ARTIFACT_EXCEPTION_TEXT_FIELDS = (
    "workflow",
    "surface",
    "technical_necessity",
    "user_request",
    "request_reference",
    "producer",
    "consumer",
    "environment",
    "contents",
    "artifact_name",
    "source_sha",
    "digest",
)


@dataclass(frozen=True)
class _ArtifactUsage:
    workflow: str
    surface: str
    action_line: int
    artifact_name: str | None
    has_one_day_retention: bool
    has_full_sha_pin: bool
    is_upload: bool
    is_workflow_source: bool


def _indent_width(value: str) -> int:
    return len(value.expandtabs(8))


def _step_region(content: str, match: re.Match[str]) -> str | None:
    """Return the YAML step containing a matched ``uses`` line."""
    line_start = content.rfind("\n", 0, match.start()) + 1
    line_end = content.find("\n", match.start())
    if line_end < 0:
        line_end = len(content)
    line = content[line_start:line_end]
    inline_step = re.match(r"(?P<indent>[ \t]*)-[ \t]+uses:[ \t]", line, re.I)
    if inline_step:
        step_start = line_start
        step_indent = inline_step.group("indent")
    else:
        candidates = list(
            re.finditer(r"(?m)^(?P<indent>[ \t]*)-[ \t]+", content[:line_start])
        )
        uses_indent = _indent_width(match.group("uses_indent"))
        candidate = next(
            (
                item
                for item in reversed(candidates)
                if _indent_width(item.group("indent")) < uses_indent
            ),
            None,
        )
        if candidate is None:
            return None
        step_start = candidate.start()
        step_indent = candidate.group("indent")

    following = content[line_end + 1 :]
    next_step = re.search(
        rf"(?m)^{re.escape(step_indent)}-[ \t]+",
        following,
    )
    step_end = line_end + 1 + next_step.start() if next_step else len(content)
    return content[step_start:step_end]


def _with_values(step: str, key: str) -> list[str]:
    """Return scalar values of ``key`` in direct ``with:`` mappings of a step."""
    values: list[str] = []
    lines = step.splitlines()
    for start, line in enumerate(lines):
        with_match = re.match(r"^(?P<indent>[ \t]*)with:[ \t]*(?:#.*)?$", line)
        if not with_match:
            continue
        with_indent = _indent_width(with_match.group("indent"))
        field_pattern = re.compile(
            rf"^[ \t]*{re.escape(key)}:[ \t]*[\"']?(?P<value>[^#\"']*?)[\"']?[ \t]*(?:#.*)?$",
            re.I,
        )
        for nested in lines[start + 1 :]:
            if not nested.strip() or nested.lstrip().startswith("#"):
                continue
            nested_indent = _indent_width(nested) - _indent_width(nested.lstrip())
            if nested_indent <= with_indent:
                break
            field_match = field_pattern.match(nested)
            if field_match:
                value = field_match.group("value").strip()
                if value:
                    values.append(value)
    return values


def _upload_step_has_one_day_retention(content: str, match: re.Match[str]) -> bool:
    step = _step_region(content, match)
    return step is not None and _with_values(step, "retention-days") == ["1"]


def _workflow_artifact_usages(repo_root: Path, source: Path) -> List[_ArtifactUsage]:
    content = _read_text(source)
    relative_path = source.relative_to(repo_root).as_posix()
    is_workflow_source = relative_path.startswith(".github/workflows/")
    usages: list[_ArtifactUsage] = []
    for match in _ARTIFACT_ACTION_RE.finditer(content):
        surface = match.group("surface").lower()
        is_upload = surface.startswith("actions/upload")
        step = _step_region(content, match)
        names = _with_values(step, "name") if step is not None else []
        usages.append(
            _ArtifactUsage(
                workflow=relative_path,
                surface=surface,
                action_line=content.count("\n", 0, match.start()) + 1,
                artifact_name=names[0] if len(names) == 1 else None,
                has_one_day_retention=(
                    _upload_step_has_one_day_retention(content, match)
                    if is_upload
                    else False
                ),
                has_full_sha_pin=bool(
                    re.fullmatch(r"[0-9a-fA-F]{40}", match.group("ref") or "")
                ),
                is_upload=is_upload,
                is_workflow_source=is_workflow_source,
            )
        )
    for match in _ARTIFACT_RUN_DOWNLOAD_RE.finditer(content):
        usages.append(
            _ArtifactUsage(
                workflow=relative_path,
                surface="gh run download",
                action_line=content.count("\n", 0, match.start()) + 1,
                artifact_name=None,
                has_one_day_retention=False,
                has_full_sha_pin=True,
                is_upload=False,
                is_workflow_source=is_workflow_source,
            )
        )
    for match in _ARTIFACT_API_RE.finditer(content):
        usages.append(
            _ArtifactUsage(
                workflow=relative_path,
                surface="github-actions-artifact-api",
                action_line=content.count("\n", 0, match.start()) + 1,
                artifact_name=None,
                has_one_day_retention=False,
                has_full_sha_pin=True,
                is_upload=False,
                is_workflow_source=is_workflow_source,
            )
        )
    return usages


_ARTIFACT_SCRIPT_SUFFIXES = {
    ".bash",
    ".cjs",
    ".js",
    ".mjs",
    ".py",
    ".sh",
    ".ts",
    ".zsh",
}


def _artifact_sources(repo_root: Path) -> list[Path]:
    """Return workflow and local helper sources that can invoke artifact storage."""
    paths: set[Path] = set()
    workflows_root = repo_root / ".github" / "workflows"
    if workflows_root.is_dir():
        paths.update(path for path in workflows_root.rglob("*.y*ml") if path.is_file())

    local_actions = repo_root / ".github" / "actions"
    if local_actions.is_dir():
        paths.update(
            path
            for path in local_actions.rglob("*")
            if path.is_file() and path.suffix.lower() != ".md"
        )

    for directory in (
        repo_root / ".github" / "scripts",
        repo_root / "ci",
        repo_root / "scripts",
        repo_root / "tools",
    ):
        if directory.is_dir():
            paths.update(
                path
                for path in directory.rglob("*")
                if path.is_file() and path.suffix.lower() in _ARTIFACT_SCRIPT_SUFFIXES
            )
    return sorted(paths)


def _positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _load_artifact_exceptions(
    repo_root: Path,
) -> tuple[List[dict[str, object]] | None, str | None]:
    policy_path = repo_root / _ARTIFACT_EXCEPTION_PATH
    if not policy_path.is_file():
        return (
            None,
            f"missing {_ARTIFACT_EXCEPTION_PATH.as_posix()}",
        )

    try:
        payload = json.loads(_read_text(policy_path))
    except json.JSONDecodeError as error:
        return None, f"invalid JSON in {_ARTIFACT_EXCEPTION_PATH}: {error.msg}"

    if not isinstance(payload, dict) or payload.get("version") != 1:
        return (
            None,
            f"{_ARTIFACT_EXCEPTION_PATH} must be an object with version 1",
        )

    raw_exceptions = payload.get("exceptions")
    if not isinstance(raw_exceptions, list):
        return None, f"{_ARTIFACT_EXCEPTION_PATH} must contain an exceptions list"

    exceptions: List[dict[str, object]] = []
    errors: List[str] = []
    for index, raw_exception in enumerate(raw_exceptions):
        if not isinstance(raw_exception, dict):
            errors.append(f"exception {index} is not an object")
            continue

        invalid_fields = [
            field
            for field in _ARTIFACT_EXCEPTION_TEXT_FIELDS
            if not isinstance(raw_exception.get(field), str)
            or not raw_exception[field].strip()
        ]
        if invalid_fields:
            errors.append(
                f"exception {index} has missing text fields: {', '.join(invalid_fields)}"
            )

        for field in ("action_line", "size_limit_bytes"):
            if not _positive_int(raw_exception.get(field)):
                errors.append(f"exception {index} must set a positive {field}")

        retention_days = raw_exception.get("retention_days")
        if (
            isinstance(retention_days, bool)
            or not isinstance(retention_days, int)
            or retention_days != 1
        ):
            errors.append(f"exception {index} must set retention_days to 1")
        if raw_exception.get("non_secret") is not True:
            errors.append(f"exception {index} must set non_secret to true")
        if raw_exception.get("release_or_rollback_authority") is not False:
            errors.append(
                f"exception {index} must set release_or_rollback_authority to false"
            )
        if raw_exception.get("reviewed") is not True:
            errors.append(f"exception {index} must set reviewed to true")
        if raw_exception.get(
            "surface"
        ) == "actions/download-artifact" and not _positive_int(
            raw_exception.get("producer_upload_line")
        ):
            errors.append(
                f"exception {index} must set producer_upload_line for a download"
            )

        exceptions.append(raw_exception)

    if errors:
        return None, "; ".join(errors)
    return exceptions, None


def _artifact_violation(message: str, remediation: str) -> Violation:
    return Violation(
        category="GitHub Artifact Storage",
        severity="CRITICAL",
        message=message,
        remediation=remediation,
    )


def _is_exception_eligible(usage: _ArtifactUsage) -> bool:
    """Report whether a usage can even reach the reviewed-exception stage."""
    return (
        usage.is_workflow_source
        and usage.surface not in _UNINSPECTABLE_ARTIFACT_SURFACES
        and usage.has_full_sha_pin
        and usage.artifact_name is not None
    )


def check_github_artifact_storage(repo_root: Path) -> List[Violation]:
    """Fail closed on GitHub Actions artifact transport in CI sources."""
    usages = [
        usage
        for source in _artifact_sources(repo_root)
        for usage in _workflow_artifact_usages(repo_root, source)
    ]
    if not usages:
        return []

    # Only consult the exception record when a usage could actually be excused;
    # an ineligible route must report its own reason, not a missing-file error.
    exceptions: List[dict[str, object]] = []
    configuration_error: str | None = None
    if any(_is_exception_eligible(usage) for usage in usages):
        loaded, configuration_error = _load_artifact_exceptions(repo_root)
        exceptions = loaded or []

    violations: List[Violation] = []
    for usage in usages:
        location = f"{usage.workflow}:{usage.action_line}"
        if not usage.is_workflow_source:
            violations.append(
                _artifact_violation(
                    f"{location} hides {usage.surface} outside a workflow",
                    "Do not put GitHub artifact transport in a composite action or "
                    "helper; use the fixed local store or direct transfer.",
                )
            )
            continue
        if usage.surface in _UNINSPECTABLE_ARTIFACT_SURFACES:
            violations.append(
                _artifact_violation(
                    f"{location} uses uninspectable {usage.surface}",
                    "API and CLI artifact routes are not exception-eligible; use a "
                    "fixed local/direct route instead.",
                )
            )
            continue
        if not usage.has_full_sha_pin:
            violations.append(
                _artifact_violation(
                    f"{location} uses {usage.surface} without a full commit SHA pin",
                    "Pin the action to a reviewed full 40-character commit SHA or "
                    "remove the GitHub artifact route.",
                )
            )
            continue
        if usage.artifact_name is None:
            violations.append(
                _artifact_violation(
                    f"{location} uses {usage.surface} without one exact with.name value",
                    "Use the fixed local store or give the exceptional route one "
                    "literal or recorded artifact name.",
                )
            )
            continue
        if configuration_error:
            violations.append(
                _artifact_violation(
                    f"{location} uses default-deny {usage.surface} and "
                    f"{configuration_error}",
                    "Remove the GitHub artifact route, or obtain and record a "
                    "current explicit user request with documented technical "
                    "necessity.",
                )
            )
            continue
        matching_exceptions = [
            exception
            for exception in exceptions
            if exception["workflow"] == usage.workflow
            and exception["surface"] == usage.surface
            and exception["action_line"] == usage.action_line
            and exception["artifact_name"] == usage.artifact_name
        ]
        if len(matching_exceptions) != 1:
            violations.append(
                _artifact_violation(
                    f"{location} uses {usage.surface} without one exact reviewed exception",
                    "Remove the route, or record one line-bound exception after the "
                    "current user explicitly requests it and alternatives demonstrably fail.",
                )
            )
            continue
        exception = matching_exceptions[0]
        if usage.is_upload and not usage.has_one_day_retention:
            violations.append(
                _artifact_violation(
                    f"{location} uses {usage.surface} without exactly retention-days: 1",
                    "Set exactly one retention-days: 1 under that action's with mapping, "
                    "or remove the GitHub artifact route.",
                )
            )
            continue
        if usage.surface == "actions/download-artifact":
            producer_line = exception["producer_upload_line"]
            producer_candidates = [
                candidate
                for candidate in usages
                if candidate.workflow == usage.workflow
                and candidate.action_line == producer_line
                and candidate.is_upload
                and candidate.has_one_day_retention
            ]
            producer_exceptions = [
                candidate
                for candidate in exceptions
                if candidate["workflow"] == usage.workflow
                and candidate["action_line"] == producer_line
                and str(candidate["surface"]).startswith("actions/upload")
            ]
            if (
                len(producer_candidates) != 1
                or len(producer_exceptions) != 1
                or producer_exceptions[0]["artifact_name"] != exception["artifact_name"]
                or producer_exceptions[0]["digest"] != exception["digest"]
                or producer_exceptions[0]["source_sha"] != exception["source_sha"]
            ):
                violations.append(
                    _artifact_violation(
                        f"{location} is not bound to one approved one-day producer upload",
                        "Bind the download to the matching upload action line, artifact "
                        "name, SHA, and digest, or use the fixed local/direct route.",
                    )
                )
    return violations


def _check_native_build_ownership(
    repo_root: Path, profile: ProjectProfile
) -> List[Violation]:
    violations: List[Violation] = []
    if not profile.has_language(Language.CPP):
        return violations

    cmake = repo_root / "CMakeLists.txt"
    if not cmake.exists():
        violations.append(
            Violation(
                category="Native Build Ownership",
                severity="CRITICAL",
                message="C++/CUDA profile has no root CMakeLists.txt",
                remediation="Restore CMake as the native build authority before editing Python packaging.",
            )
        )

    setup_py = repo_root / "setup.py"
    if setup_py.exists():
        text = _read_text(setup_py)
        native_setup_patterns = [
            r"\bsetuptools\s*\.\s*Extension\s*\(",
            r"\bExtension\s*\(",
            r"\bCUDAExtension\s*\(",
            r"\bCppExtension\s*\(",
            r"\bBuildExtension\b",
            r"\bextra_compile_args\b",
            r"\bextra_link_args\b",
            r"\bdefine_macros\b",
            r"\blibrary_dirs\b",
            r"\binclude_dirs\b",
        ]
        if any(re.search(pattern, text) for pattern in native_setup_patterns):
            violations.append(
                Violation(
                    category="Native Build Ownership",
                    severity="CRITICAL",
                    message="setup.py appears to define native C++/CUDA build logic",
                    remediation=(
                        "Move native targets, compiler/link flags, CUDA policy, and dependency "
                        "discovery into CMake; keep Python packaging as a thin bridge."
                    ),
                )
            )

    pyproject = repo_root / "pyproject.toml"
    if pyproject.exists():
        text = _read_text(pyproject)
        if re.search(r'build-backend\s*=\s*["\']setuptools\.build_meta', text):
            native_markers = [
                "tool.setuptools",
                "ext_modules",
                "Extension(",
                "CUDAExtension",
                "CppExtension",
            ]
            if any(marker in text for marker in native_markers):
                violations.append(
                    Violation(
                        category="Native Build Ownership",
                        severity="CRITICAL",
                        message="pyproject.toml routes native extension building through setuptools",
                        remediation="Use scikit-build-core only as a bridge to the CMake-owned native graph.",
                    )
                )

        python_owned_native_policy = [
            "CMAKE_CUDA_ARCHITECTURES",
            "CUDA_ARCHITECTURES",
            "TORCH_CUDA_ARCH_LIST",
            "extra_compile_args",
            "extra_link_args",
            "define_macros",
            "library_dirs",
            "include_dirs",
        ]
        if any(marker in text for marker in python_owned_native_policy):
            violations.append(
                Violation(
                    category="Native Build Ownership",
                    severity="CRITICAL",
                    message="pyproject.toml appears to own native compiler/link/CUDA policy",
                    remediation=(
                        "Define native compiler flags, link flags, CUDA architectures, and "
                        "dependency discovery in CMake instead of Python packaging metadata."
                    ),
                )
            )

    return violations


def check_constraints(repo_root: Path, profile: ProjectProfile) -> List[Violation]:
    violations = _check_git(repo_root)
    violations.extend(_check_instruction_safety(repo_root))
    violations.extend(check_github_artifact_storage(repo_root))

    if profile.has_language(Language.PYTHON):
        violations.extend(_check_python(repo_root, profile))
    if profile.has_language(Language.CPP):
        violations.extend(_check_cpp(repo_root, profile))
        violations.extend(_check_native_build_ownership(repo_root, profile))

    return violations


def _check_instruction_safety(repo_root: Path) -> List[Violation]:
    return [
        Violation(
            category="Instruction Safety",
            severity="CRITICAL",
            message=(
                f"{violation.path.relative_to(repo_root)}:{violation.line} "
                f"matches {violation.rule}: {violation.reason}"
            ),
            remediation=violation.remediation,
        )
        for violation in scan_instruction_safety(repo_root)
    ]


def print_report(violations: List[Violation]) -> None:
    if not violations:
        print("No critical constraint violations detected.")
        return

    print("=" * 70)
    print("CONSTRAINT VIOLATIONS")
    print("=" * 70)
    for violation in violations:
        print(f"[{violation.severity}] {violation.category}: {violation.message}")
        print(f"  Remediation: {violation.remediation}")
    print("=" * 70)


def main() -> None:
    parser = argparse.ArgumentParser(description="Constraint checker")
    parser.add_argument(
        "--project-type",
        choices=["auto", "python", "cpp", "hybrid"],
        default="auto",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--changed-files", nargs="*", default=[])
    args = parser.parse_args()

    repo_root = resolve_repo_root(Path(__file__).resolve())
    if args.project_type == "auto":
        profile = detect(repo_root)
    else:
        if args.project_type == "python":
            profile = ProjectProfile(
                language=[Language.PYTHON], build_system=BuildSystem.POETRY
            )
        elif args.project_type == "cpp":
            profile = ProjectProfile(
                language=[Language.CPP], build_system=BuildSystem.CMAKE
            )
        else:
            profile = ProjectProfile(
                language=[Language.PYTHON, Language.CPP],
                build_system=BuildSystem.SCIKIT_BUILD_CORE,
            )

    if profile is None:
        print("ERROR: Could not detect project profile")
        sys.exit(1)

    violations = check_constraints(repo_root, profile)

    if args.json:
        print(
            json.dumps(
                {
                    "project_type": "hybrid"
                    if profile.is_hybrid()
                    else profile.language[0].value,
                    "violations": [v.to_dict() for v in violations],
                },
                indent=2,
            )
        )
    else:
        print_report(violations)

    critical = [v for v in violations if v.severity == "CRITICAL"]
    sys.exit(1 if critical else 0)


if __name__ == "__main__":
    main()
