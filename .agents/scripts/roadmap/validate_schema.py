#!/usr/bin/env python3
"""Validate dependency-aware per-phase roadmap schema."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Set

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / "common"))
from check_session import check_session_initialized

from utils import RoadmapManager


class Severity(Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


@dataclass
class ValidationError:
    severity: Severity
    category: str
    message: str
    location: str
    remediation: str

    def __str__(self) -> str:
        return (
            f"[{self.severity.value}] {self.category}\n"
            f"  Location: {self.location}\n"
            f"  Issue: {self.message}\n"
            f"  Fix: {self.remediation}"
        )


class RoadmapSchemaValidator:
    """Schema validator for per-phase roadmap.yml files."""

    VALID_STATUSES = {"pending", "active", "completed", "blocked"}
    VALID_EFFORTS = {"low", "medium", "high"}
    TASK_ID_PATTERN = re.compile(r"^task-\d+-\d+$")
    PHASE_FOLDER_PATTERN = re.compile(r"^phase-\d+-[a-z0-9]+(?:-[a-z0-9]+)*$")
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    NON_ATOMIC_INDICATORS = {
        "entire",
        "all",
        "complete",
        "full",
        "whole",
        "everything",
        "comprehensive",
        "total",
    }

    CONJUNCTION_WORDS = {"and", "or", "then", "plus", "also"}

    def __init__(self, roadmap_data: Dict[str, Any]):
        self.data = roadmap_data
        self.errors: List[ValidationError] = []

    def _add_error(
        self,
        severity: Severity,
        category: str,
        message: str,
        location: str,
        remediation: str,
    ) -> None:
        self.errors.append(
            ValidationError(
                severity=severity,
                category=category,
                message=message,
                location=location,
                remediation=remediation,
            )
        )

    def validate(self) -> List[ValidationError]:
        self.errors = []
        self._validate_top_level()
        self._validate_status()
        self._validate_phase_dependencies()
        self._validate_tasks()
        self._validate_focus()
        self._validate_dependency_graph()
        self._validate_quality_hints()
        return self.errors

    def _validate_top_level(self) -> None:
        required = {"phase", "name", "status", "depends_on_phases", "tasks", "focus"}
        for key in sorted(required):
            if key not in self.data:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing required top-level key '{key}'",
                    "roadmap.yml (root)",
                    f"Add '{key}' following the roadmap template",
                )

        extra = set(self.data.keys()) - required
        if extra:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                f"Unknown top-level keys: {', '.join(sorted(extra))}",
                "roadmap.yml (root)",
                "Remove unknown fields to keep schema deterministic",
            )

        phase = self.data.get("phase")
        if phase is not None and not isinstance(phase, int):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'phase' must be an integer (e.g., 7)",
                "roadmap.yml:phase",
                "Set phase to an integer value",
            )

        name = self.data.get("name")
        if name is not None and (not isinstance(name, str) or not name.strip()):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'name' must be a non-empty string",
                "roadmap.yml:name",
                "Provide a descriptive phase name",
            )

    def _validate_status(self) -> None:
        status = self.data.get("status")
        if not isinstance(status, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'status' must be a dictionary",
                "roadmap.yml:status",
                "Use status with active/blocked/started_at/completed_at fields",
            )
            return

        required = {"active", "blocked", "started_at", "completed_at"}
        for key in sorted(required):
            if key not in status:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing status key '{key}'",
                    "roadmap.yml:status",
                    f"Add status.{key}",
                )

        if "active" in status and not isinstance(status["active"], bool):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "status.active must be boolean",
                "roadmap.yml:status.active",
                "Use true or false",
            )

        if "blocked" in status and not isinstance(status["blocked"], bool):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "status.blocked must be boolean",
                "roadmap.yml:status.blocked",
                "Use true or false",
            )

        for key in ("started_at", "completed_at"):
            if key not in status:
                continue
            value = status[key]
            if value is not None and not isinstance(value, str):
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"status.{key} must be null or YYYY-MM-DD string",
                    f"roadmap.yml:status.{key}",
                    "Use null or a date like 2026-04-17",
                )
            elif isinstance(value, str) and not self.DATE_PATTERN.match(value):
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"status.{key} has invalid date '{value}'",
                    f"roadmap.yml:status.{key}",
                    "Use YYYY-MM-DD format",
                )

    def _validate_phase_dependencies(self) -> None:
        deps = self.data.get("depends_on_phases")
        if not isinstance(deps, list):
            self._add_error(
                Severity.CRITICAL,
                "Dependencies",
                "depends_on_phases must be a list",
                "roadmap.yml:depends_on_phases",
                "Use [] when no phase dependencies are required",
            )
            return

        seen: Set[str] = set()
        for index, dep in enumerate(deps):
            if not isinstance(dep, str) or not dep.strip():
                self._add_error(
                    Severity.CRITICAL,
                    "Dependencies",
                    "Phase dependencies must be non-empty strings",
                    f"roadmap.yml:depends_on_phases[{index}]",
                    "Use the active roadmap folder name declared for this workspace",
                )
                continue

            dep_name = dep.strip()
            if dep_name in seen:
                self._add_error(
                    Severity.CRITICAL,
                    "Dependencies",
                    f"Duplicate phase dependency '{dep_name}'",
                    f"roadmap.yml:depends_on_phases[{index}]",
                    "Remove duplicate entries",
                )
            seen.add(dep_name)

            if not self.PHASE_FOLDER_PATTERN.match(dep_name):
                self._add_error(
                    Severity.WARNING,
                    "Dependencies",
                    f"Phase dependency '{dep_name}' does not match phase folder naming convention",
                    f"roadmap.yml:depends_on_phases[{index}]",
                    "Use phase-N-short-name format for reliable automation",
                )

    def _validate_tasks(self) -> None:
        tasks = self.data.get("tasks")
        if not isinstance(tasks, list) or not tasks:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "tasks must be a non-empty list",
                "roadmap.yml:tasks",
                "Add at least one task object",
            )
            return

        required = {
            "id",
            "title",
            "description",
            "status",
            "effort",
            "key_files",
            "depends_on",
        }

        seen_ids: Set[str] = set()
        active_ids: List[str] = []

        for idx, task in enumerate(tasks):
            location = f"roadmap.yml:tasks[{idx}]"
            if not isinstance(task, dict):
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Task at index {idx} must be a dictionary",
                    location,
                    "Replace with a valid task object",
                )
                continue

            missing = [key for key in sorted(required) if key not in task]
            if missing:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Task missing required fields: {', '.join(missing)}",
                    location,
                    "Add all required fields to each task",
                )

            extra = set(task.keys()) - required - {"notes"}
            if extra:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Task has unknown fields: {', '.join(sorted(extra))}",
                    location,
                    "Remove unsupported task fields",
                )

            task_id = task.get("id")
            if isinstance(task_id, str):
                if task_id in seen_ids:
                    self._add_error(
                        Severity.CRITICAL,
                        "ID Format",
                        f"Duplicate task id '{task_id}'",
                        f"{location}.id",
                        "Use unique task IDs",
                    )
                seen_ids.add(task_id)
                if not self.TASK_ID_PATTERN.match(task_id):
                    self._add_error(
                        Severity.CRITICAL,
                        "ID Format",
                        f"Invalid task id '{task_id}'",
                        f"{location}.id",
                        "Use task-N-M format",
                    )
            else:
                self._add_error(
                    Severity.CRITICAL,
                    "ID Format",
                    "Task id must be a string",
                    f"{location}.id",
                    "Use task-N-M format",
                )

            status = task.get("status")
            if status not in self.VALID_STATUSES:
                self._add_error(
                    Severity.CRITICAL,
                    "Status Value",
                    f"Invalid task status '{status}'",
                    f"{location}.status",
                    "Use pending|active|completed|blocked",
                )
            elif status == "active" and isinstance(task_id, str):
                active_ids.append(task_id)

            effort = task.get("effort")
            if effort not in self.VALID_EFFORTS:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Invalid effort '{effort}'",
                    f"{location}.effort",
                    "Use low|medium|high",
                )

            key_files = task.get("key_files")
            if not isinstance(key_files, list) or not key_files:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    "key_files must be a non-empty list",
                    f"{location}.key_files",
                    "List at least one file or directory path",
                )
            elif not all(isinstance(path, str) and path.strip() for path in key_files):
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    "key_files entries must be non-empty strings",
                    f"{location}.key_files",
                    "Remove empty or non-string entries",
                )

            depends_on = task.get("depends_on")
            if not isinstance(depends_on, list):
                self._add_error(
                    Severity.CRITICAL,
                    "Dependencies",
                    "depends_on must be a list",
                    f"{location}.depends_on",
                    "Use [] when task has no prerequisites",
                )
            else:
                for dep_idx, dep in enumerate(depends_on):
                    if not isinstance(dep, str) or not dep.strip():
                        self._add_error(
                            Severity.CRITICAL,
                            "Dependencies",
                            f"Invalid task dependency '{dep}'",
                            f"{location}.depends_on[{dep_idx}]",
                            "Task dependencies must reference task IDs",
                        )

            if not isinstance(task.get("title"), str) or not task["title"].strip():
                self._add_error(
                    Severity.CRITICAL,
                    "Description Quality",
                    "Task title must be a non-empty string",
                    f"{location}.title",
                    "Provide a specific task title",
                )

            if (
                not isinstance(task.get("description"), str)
                or not task["description"].strip()
            ):
                self._add_error(
                    Severity.CRITICAL,
                    "Description Quality",
                    "Task description must be a non-empty string",
                    f"{location}.description",
                    "Describe objective, constraints, and acceptance criteria",
                )

            notes = task.get("notes")
            if notes is not None and not isinstance(notes, str):
                self._add_error(
                    Severity.CRITICAL,
                    "Description Quality",
                    "Task notes must be a string when present",
                    f"{location}.notes",
                    "Convert notes to plain text",
                )

        if len(active_ids) > 1:
            self._add_error(
                Severity.CRITICAL,
                "Task Focus",
                f"Multiple active tasks found: {', '.join(active_ids)}",
                "roadmap.yml:tasks",
                "Keep exactly one active task per active phase",
            )

    def _validate_focus(self) -> None:
        focus = self.data.get("focus")
        if not isinstance(focus, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "focus must be a dictionary",
                "roadmap.yml:focus",
                "Use focus.current_task and focus.notes",
            )
            return

        required = {"current_task", "notes"}
        for key in sorted(required):
            if key not in focus:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing focus key '{key}'",
                    "roadmap.yml:focus",
                    f"Add focus.{key}",
                )

        current_task = focus.get("current_task")
        if current_task is not None and not isinstance(current_task, str):
            self._add_error(
                Severity.CRITICAL,
                "Task Focus",
                "focus.current_task must be null or task id",
                "roadmap.yml:focus.current_task",
                "Set to null or a valid task id",
            )

        notes = focus.get("notes")
        if notes is not None and not isinstance(notes, str):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "focus.notes must be a string",
                "roadmap.yml:focus.notes",
                "Use plain text notes",
            )

        tasks = (
            self.data.get("tasks") if isinstance(self.data.get("tasks"), list) else []
        )
        task_map = {
            task.get("id"): task
            for task in tasks
            if isinstance(task, dict) and isinstance(task.get("id"), str)
        }
        active_ids = [
            task_id
            for task_id, task in task_map.items()
            if task.get("status") == "active"
        ]

        if isinstance(current_task, str) and current_task not in task_map:
            self._add_error(
                Severity.CRITICAL,
                "Task Focus",
                f"focus.current_task '{current_task}' not found in tasks",
                "roadmap.yml:focus.current_task",
                "Point to an existing task id",
            )

        status = self.data.get("status", {})
        step_active = (
            bool(status.get("active", False)) if isinstance(status, dict) else False
        )
        step_blocked = (
            bool(status.get("blocked", False)) if isinstance(status, dict) else False
        )

        if step_active and not step_blocked:
            if not isinstance(current_task, str):
                self._add_error(
                    Severity.CRITICAL,
                    "Task Focus",
                    "Active phase requires focus.current_task",
                    "roadmap.yml:focus.current_task",
                    "Set focus.current_task to the active task",
                )
            if len(active_ids) != 1:
                self._add_error(
                    Severity.CRITICAL,
                    "Task Focus",
                    "Active phase requires exactly one active task",
                    "roadmap.yml:tasks",
                    "Set one task to active and all others to pending/completed/blocked",
                )
            if isinstance(current_task, str) and current_task in task_map:
                if task_map[current_task].get("status") != "active":
                    self._add_error(
                        Severity.CRITICAL,
                        "Task Focus",
                        "focus.current_task must point to the active task",
                        "roadmap.yml:focus.current_task",
                        "Align focus.current_task with task status",
                    )
        elif step_active and step_blocked:
            if len(active_ids) > 1:
                self._add_error(
                    Severity.CRITICAL,
                    "Task Focus",
                    "Blocked phase cannot have multiple active tasks",
                    "roadmap.yml:tasks",
                    "Keep at most one active task while blocked",
                )
            if isinstance(current_task, str) and current_task in task_map:
                if task_map[current_task].get("status") not in {"blocked", "active"}:
                    self._add_error(
                        Severity.CRITICAL,
                        "Task Focus",
                        "Blocked phase focus.current_task must reference blocked/active task",
                        "roadmap.yml:focus.current_task",
                        "Set focus.current_task to blocked task or null",
                    )
        else:
            if active_ids:
                self._add_error(
                    Severity.CRITICAL,
                    "Task Focus",
                    "Inactive phase cannot have active tasks",
                    "roadmap.yml:tasks",
                    "Clear active task status when phase is inactive",
                )

    def _validate_dependency_graph(self) -> None:
        tasks = self.data.get("tasks")
        if not isinstance(tasks, list):
            return

        task_ids = {
            task["id"]
            for task in tasks
            if isinstance(task, dict) and isinstance(task.get("id"), str)
        }

        graph: Dict[str, List[str]] = {}
        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_id = task.get("id")
            depends_on = task.get("depends_on")
            if not isinstance(task_id, str) or not isinstance(depends_on, list):
                continue
            clean_deps = [dep for dep in depends_on if isinstance(dep, str)]
            graph[task_id] = clean_deps
            for dep in clean_deps:
                if dep not in task_ids:
                    self._add_error(
                        Severity.CRITICAL,
                        "Dependencies",
                        f"Task '{task_id}' depends on unknown task '{dep}'",
                        f"roadmap.yml:tasks.{task_id}.depends_on",
                        "Reference existing task IDs only",
                    )
                if dep == task_id:
                    self._add_error(
                        Severity.CRITICAL,
                        "Dependencies",
                        f"Task '{task_id}' cannot depend on itself",
                        f"roadmap.yml:tasks.{task_id}.depends_on",
                        "Remove self dependency",
                    )

        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(node: str, trail: List[str]) -> None:
            if node in visited:
                return
            if node in visiting:
                start = trail.index(node) if node in trail else 0
                cycle = trail[start:] + [node]
                self._add_error(
                    Severity.CRITICAL,
                    "Dependencies",
                    "Dependency cycle detected: " + " -> ".join(cycle),
                    "roadmap.yml:tasks",
                    "Remove cyclical depends_on links",
                )
                return

            visiting.add(node)
            for dep in graph.get(node, []):
                dfs(dep, trail + [node])
            visiting.remove(node)
            visited.add(node)

        for task_id in list(graph.keys()):
            dfs(task_id, [])

    def _validate_quality_hints(self) -> None:
        tasks = self.data.get("tasks")
        if not isinstance(tasks, list):
            return

        for task in tasks:
            if not isinstance(task, dict):
                continue
            task_id = task.get("id", "unknown")
            title = task.get("title", "")

            if isinstance(title, str):
                title_words = title.lower().split()
                noisy = [
                    word for word in self.NON_ATOMIC_INDICATORS if word in title.lower()
                ]
                if noisy:
                    self._add_error(
                        Severity.WARNING,
                        "Task Atomicity",
                        f"Task '{task_id}' may be too broad ({', '.join(noisy)})",
                        f"roadmap.yml:tasks.{task_id}.title",
                        "Split into smaller atomic tasks",
                    )

                conjunctions = [
                    word for word in self.CONJUNCTION_WORDS if word in title_words
                ]
                if conjunctions:
                    self._add_error(
                        Severity.WARNING,
                        "Task Atomicity",
                        f"Task '{task_id}' may contain multiple actions ({', '.join(conjunctions)})",
                        f"roadmap.yml:tasks.{task_id}.title",
                        "Consider splitting into multiple tasks",
                    )

                if len(title) > 100:
                    self._add_error(
                        Severity.INFO,
                        "Description Quality",
                        f"Task '{task_id}' title is long ({len(title)} chars)",
                        f"roadmap.yml:tasks.{task_id}.title",
                        "Prefer concise titles and place detail in description",
                    )

            description = task.get("description", "")
            if isinstance(description, str) and len(description.strip()) < 30:
                self._add_error(
                    Severity.INFO,
                    "Description Quality",
                    f"Task '{task_id}' description is very short",
                    f"roadmap.yml:tasks.{task_id}.description",
                    "Add explicit acceptance criteria and constraints",
                )


def validate_phase_folder_structure(phase_dir: Path) -> List[ValidationError]:
    """Ensure the required phase files exist and declare the authority order."""

    errors: List[ValidationError] = []
    required_files = ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md")

    for name in required_files:
        target = phase_dir / name
        if not target.exists():
            errors.append(
                ValidationError(
                    severity=Severity.CRITICAL,
                    category="Phase Structure",
                    message=f"Missing required phase file '{name}'",
                    location=str(target),
                    remediation=(
                        "Re-run the roadmap creation template, or copy "
                        f".agents/scripts/roadmap/templates/{name} into this phase "
                        "and fill in placeholders."
                    ),
                )
            )

    sessions_dir = phase_dir / "sessions"
    if not sessions_dir.exists() or not sessions_dir.is_dir():
        errors.append(
            ValidationError(
                severity=Severity.CRITICAL,
                category="Phase Structure",
                message="Missing 'sessions/' directory for handoff files",
                location=str(sessions_dir),
                remediation="Create an empty sessions/ directory with a .gitkeep file",
            )
        )

    authority_tokens = (
        "INVARIANTS.md",
        "ROADMAP.md",
        "roadmap.yml",
        "sessions",
        "prompt.md",
    )
    for name in ("prompt.md", "INVARIANTS.md"):
        target = phase_dir / name
        if not target.exists():
            continue
        text = target.read_text(encoding="utf-8", errors="ignore")
        missing = [token for token in authority_tokens if token not in text]
        if missing:
            errors.append(
                ValidationError(
                    severity=Severity.CRITICAL,
                    category="Authority Order",
                    message=(
                        f"{name} is missing authority-order tokens: "
                        + ", ".join(missing)
                    ),
                    location=str(target),
                    remediation=(
                        "Declare repository-local precedence as INVARIANTS.md > "
                        "roadmap.yml > ROADMAP.md > sessions/ > prompt.md so "
                        "fresh sessions pick up the rule without guessing."
                    ),
                )
            )

    return errors


def validate_roadmap_file(roadmap_path: Path) -> List[ValidationError]:
    manager = RoadmapManager()
    try:
        data = manager.parse_roadmap_yml(roadmap_path)
    except ValueError as exc:
        return [
            ValidationError(
                severity=Severity.CRITICAL,
                category="YAML Parsing",
                message=str(exc),
                location=str(roadmap_path),
                remediation="Fix YAML syntax or file encoding",
            )
        ]

    validator = RoadmapSchemaValidator(data)
    errors = validator.validate()

    # Ensure shared runtime validator agrees with schema validator.
    try:
        manager._validate_roadmap_data(data)  # noqa: SLF001 - intentional consistency check
    except ValueError as exc:
        errors.append(
            ValidationError(
                severity=Severity.CRITICAL,
                category="Runtime Validation",
                message=str(exc),
                location=str(roadmap_path),
                remediation="Align roadmap.yml with runtime schema expectations",
            )
        )

    return errors


def print_validation_results(errors: List[ValidationError], roadmap_name: str) -> None:
    print("=" * 70)
    print(f"ROADMAP VALIDATION: {roadmap_name}")
    print("=" * 70)
    print()

    if not errors:
        print("No validation errors found")
        print()
        print("Roadmap is compliant with the dependency-aware schema.")
        return

    critical = [err for err in errors if err.severity == Severity.CRITICAL]
    warnings = [err for err in errors if err.severity == Severity.WARNING]
    info = [err for err in errors if err.severity == Severity.INFO]

    if critical:
        print(f"CRITICAL ERRORS: {len(critical)}")
        print("-" * 70)
        for err in critical:
            print(str(err))
            print()

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        print("-" * 70)
        for err in warnings:
            print(str(err))
            print()

    if info:
        print(f"SUGGESTIONS: {len(info)}")
        print("-" * 70)
        for err in info:
            print(str(err))
            print()

    print("=" * 70)
    print(
        f"Total issues: {len(errors)} "
        f"(Critical: {len(critical)}, Warnings: {len(warnings)}, Info: {len(info)})"
    )
    print("=" * 70)

    if critical:
        print()
        print("VALIDATION FAILED")
        print("Fix all CRITICAL errors before proceeding.")
    elif warnings:
        print()
        print("VALIDATION PASSED WITH WARNINGS")
        print("Consider fixing warnings for better roadmap quality.")
    else:
        print()
        print("VALIDATION PASSED")


def main() -> None:
    check_session_initialized("roadmap")

    if len(sys.argv) < 2:
        print("Usage: validate_schema.py <phase-folder>")
        print("Example: validate_schema.py <roadmap-folder>")
        sys.exit(1)

    roadmap_name = sys.argv[1]
    repo_root = Path.cwd()
    phase_dir = repo_root / "agent_roadmaps" / roadmap_name
    roadmap_path = phase_dir / "roadmap.yml"

    if not phase_dir.exists():
        print(f"ERROR: Phase folder not found: {phase_dir}")
        sys.exit(1)

    structure_errors = validate_phase_folder_structure(phase_dir)

    if not roadmap_path.exists():
        print_validation_results(structure_errors, roadmap_name)
        sys.exit(1)

    errors = structure_errors + validate_roadmap_file(roadmap_path)
    print_validation_results(errors, roadmap_name)

    critical_count = sum(1 for err in errors if err.severity == Severity.CRITICAL)
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
