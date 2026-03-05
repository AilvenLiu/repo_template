#!/usr/bin/env python3
"""
Comprehensive roadmap schema validation.

This module enforces strict compliance with the roadmap template,
ensuring agents follow the exact schema and best practices.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import RoadmapManager


class Severity(Enum):
    """Validation error severity levels."""
    CRITICAL = "CRITICAL"  # Must be fixed before proceeding
    WARNING = "WARNING"    # Should be fixed, but not blocking
    INFO = "INFO"          # Suggestions for improvement


@dataclass
class ValidationError:
    """Represents a validation error with context."""
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
    """Validates roadmap.yml against template schema."""

    # Valid status values
    VALID_STATUSES = {"pending", "active", "completed", "blocked"}

    # Phase ID pattern: phase-0, phase-1, etc.
    PHASE_ID_PATTERN = re.compile(r'^phase-\d+$')

    # Task ID pattern: task-0-1, task-1-2, etc.
    TASK_ID_PATTERN = re.compile(r'^task-\d+-\d+$')

    # Words indicating non-atomic tasks
    NON_ATOMIC_INDICATORS = {
        "entire", "all", "complete", "full", "whole",
        "everything", "comprehensive", "total"
    }

    # Conjunction words suggesting multiple tasks
    CONJUNCTION_WORDS = {"and", "or", "then", "plus", "also"}

    def __init__(self, roadmap_data: Dict[str, Any]):
        """Initialize validator with roadmap data."""
        self.data = roadmap_data
        self.errors: List[ValidationError] = []

    def validate(self) -> List[ValidationError]:
        """Run all validations and return errors."""
        self.errors = []

        # Core schema validations
        self._validate_required_top_level_keys()
        self._validate_roadmap_section()
        self._validate_status_section()
        self._validate_current_focus()
        self._validate_phases()

        # Advanced validations
        self._validate_single_active_task()
        self._validate_task_atomicity()
        self._validate_description_quality()

        return self.errors

    def _add_error(self, severity: Severity, category: str,
                   message: str, location: str, remediation: str):
        """Add a validation error."""
        self.errors.append(ValidationError(
            severity=severity,
            category=category,
            message=message,
            location=location,
            remediation=remediation
        ))

    def _validate_required_top_level_keys(self):
        """Validate required top-level keys exist."""
        required_keys = ["roadmap", "status", "current_focus", "phases"]
        for key in required_keys:
            if key not in self.data:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing required top-level key: '{key}'",
                    "roadmap.yml (root)",
                    f"Add '{key}:' section to roadmap.yml following template"
                )

    def _validate_roadmap_section(self):
        """Validate roadmap metadata section."""
        if "roadmap" not in self.data:
            return

        roadmap = self.data["roadmap"]
        if not isinstance(roadmap, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'roadmap' must be a dictionary",
                "roadmap.yml:roadmap",
                "Change 'roadmap:' to a dictionary with 'name' and 'description'"
            )
            return

        # Validate required fields
        if "name" not in roadmap:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "Missing required field 'name' in roadmap section",
                "roadmap.yml:roadmap",
                "Add 'name: <roadmap-name>' to roadmap section"
            )

        if "description" not in roadmap:
            self._add_error(
                Severity.WARNING,
                "Schema Structure",
                "Missing recommended field 'description' in roadmap section",
                "roadmap.yml:roadmap",
                "Add 'description: <brief description>' to roadmap section"
            )

        # Check for extra fields
        allowed_fields = {"name", "description"}
        extra_fields = set(roadmap.keys()) - allowed_fields
        if extra_fields:
            self._add_error(
                Severity.CRITICAL,
                "Schema Compliance",
                f"Extra fields in roadmap section: {', '.join(extra_fields)}",
                "roadmap.yml:roadmap",
                f"Remove fields: {', '.join(extra_fields)}"
            )

    def _validate_status_section(self):
        """Validate status section."""
        if "status" not in self.data:
            return

        status = self.data["status"]
        if not isinstance(status, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'status' must be a dictionary",
                "roadmap.yml:status",
                "Change 'status:' to a dictionary with boolean fields"
            )
            return

        # Validate required boolean fields
        required_fields = ["active", "blocked", "completed"]
        for field in required_fields:
            if field not in status:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing required field '{field}' in status section",
                    "roadmap.yml:status",
                    f"Add '{field}: true/false' to status section"
                )
            elif not isinstance(status[field], bool):
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Field 'status.{field}' must be boolean (true/false)",
                    f"roadmap.yml:status.{field}",
                    f"Change to 'true' or 'false' (not string)"
                )

        # Check for extra fields
        allowed_fields = {"active", "blocked", "completed"}
        extra_fields = set(status.keys()) - allowed_fields
        if extra_fields:
            self._add_error(
                Severity.CRITICAL,
                "Schema Compliance",
                f"Extra fields in status section: {', '.join(extra_fields)}",
                "roadmap.yml:status",
                f"Remove fields: {', '.join(extra_fields)}"
            )

    def _validate_current_focus(self):
        """Validate current_focus section."""
        if "current_focus" not in self.data:
            return

        focus = self.data["current_focus"]
        if not isinstance(focus, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'current_focus' must be a dictionary",
                "roadmap.yml:current_focus",
                "Change to dictionary with 'phase' and 'task' fields"
            )
            return

        # Validate required fields
        if "phase" not in focus:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "Missing 'phase' in current_focus",
                "roadmap.yml:current_focus",
                "Add 'phase: phase-N' to current_focus"
            )

        if "task" not in focus:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "Missing 'task' in current_focus",
                "roadmap.yml:current_focus",
                "Add 'task: task-N-M' to current_focus"
            )

        # Check for extra fields
        allowed_fields = {"phase", "task"}
        extra_fields = set(focus.keys()) - allowed_fields
        if extra_fields:
            self._add_error(
                Severity.CRITICAL,
                "Schema Compliance",
                f"Extra fields in current_focus: {', '.join(extra_fields)}",
                "roadmap.yml:current_focus",
                f"Remove fields: {', '.join(extra_fields)}"
            )

    def _validate_phases(self):
        """Validate phases section."""
        if "phases" not in self.data:
            return

        phases = self.data["phases"]
        if not isinstance(phases, list):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "'phases' must be a list",
                "roadmap.yml:phases",
                "Change 'phases:' to a list of phase dictionaries"
            )
            return

        if not phases:
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "Phases list is empty",
                "roadmap.yml:phases",
                "Add at least one phase following template"
            )
            return

        for i, phase in enumerate(phases):
            self._validate_phase(phase, i)

    def _validate_phase(self, phase: Any, index: int):
        """Validate a single phase."""
        location = f"roadmap.yml:phases[{index}]"

        if not isinstance(phase, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                f"Phase at index {index} must be a dictionary",
                location,
                "Change to dictionary with required fields"
            )
            return

        # Validate required fields
        required_fields = ["id", "title", "status", "tasks"]
        for field in required_fields:
            if field not in phase:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing required field '{field}' in phase",
                    location,
                    f"Add '{field}:' to phase following template"
                )

        # Validate phase ID format
        if "id" in phase:
            phase_id = phase["id"]
            if not self.PHASE_ID_PATTERN.match(str(phase_id)):
                self._add_error(
                    Severity.CRITICAL,
                    "ID Format",
                    f"Invalid phase ID format: '{phase_id}'",
                    f"{location}.id",
                    f"Use format 'phase-N' (e.g., 'phase-{index}')"
                )

        # Validate status value
        if "status" in phase:
            status = phase["status"]
            if status not in self.VALID_STATUSES:
                self._add_error(
                    Severity.CRITICAL,
                    "Status Value",
                    f"Invalid phase status: '{status}'",
                    f"{location}.status",
                    f"Use one of: {', '.join(self.VALID_STATUSES)}"
                )

        # Check for extra fields
        allowed_fields = {"id", "title", "status", "tasks"}
        extra_fields = set(phase.keys()) - allowed_fields
        if extra_fields:
            self._add_error(
                Severity.CRITICAL,
                "Schema Compliance",
                f"Extra fields in phase: {', '.join(extra_fields)}",
                location,
                f"Remove fields: {', '.join(extra_fields)}"
            )

        # Validate tasks
        if "tasks" in phase:
            self._validate_tasks(phase["tasks"], phase.get("id", f"phase-{index}"))

    def _validate_tasks(self, tasks: Any, phase_id: str):
        """Validate tasks list."""
        location = f"roadmap.yml:phases.{phase_id}.tasks"

        if not isinstance(tasks, list):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                "Tasks must be a list",
                location,
                "Change 'tasks:' to a list of task dictionaries"
            )
            return

        if not tasks:
            self._add_error(
                Severity.WARNING,
                "Schema Structure",
                f"Phase '{phase_id}' has no tasks",
                location,
                "Add at least one task to this phase"
            )
            return

        for i, task in enumerate(tasks):
            self._validate_task(task, phase_id, i)

    def _validate_task(self, task: Any, phase_id: str, index: int):
        """Validate a single task."""
        location = f"roadmap.yml:phases.{phase_id}.tasks[{index}]"

        if not isinstance(task, dict):
            self._add_error(
                Severity.CRITICAL,
                "Schema Structure",
                f"Task at index {index} must be a dictionary",
                location,
                "Change to dictionary with required fields"
            )
            return

        # Validate required fields
        required_fields = ["id", "title", "status"]
        for field in required_fields:
            if field not in task:
                self._add_error(
                    Severity.CRITICAL,
                    "Schema Structure",
                    f"Missing required field '{field}' in task",
                    location,
                    f"Add '{field}:' to task following template"
                )

        # Validate task ID format
        if "id" in task:
            task_id = task["id"]
            if not self.TASK_ID_PATTERN.match(str(task_id)):
                self._add_error(
                    Severity.CRITICAL,
                    "ID Format",
                    f"Invalid task ID format: '{task_id}'",
                    f"{location}.id",
                    "Use format 'task-N-M' (e.g., 'task-0-1')"
                )

        # Validate status value
        if "status" in task:
            status = task["status"]
            if status not in self.VALID_STATUSES:
                self._add_error(
                    Severity.CRITICAL,
                    "Status Value",
                    f"Invalid task status: '{status}'",
                    f"{location}.status",
                    f"Use one of: {', '.join(self.VALID_STATUSES)}"
                )

        # Check for extra fields
        allowed_fields = {"id", "title", "status", "notes"}
        extra_fields = set(task.keys()) - allowed_fields
        if extra_fields:
            self._add_error(
                Severity.CRITICAL,
                "Schema Compliance",
                f"Extra fields in task: {', '.join(extra_fields)}",
                location,
                f"Remove fields: {', '.join(extra_fields)}"
            )

    def _validate_single_active_task(self):
        """Ensure exactly one task is active."""
        if "phases" not in self.data:
            return

        active_tasks = []
        for phase in self.data["phases"]:
            if not isinstance(phase, dict) or "tasks" not in phase:
                continue

            phase_id = phase.get("id", "unknown")
            for task in phase.get("tasks", []):
                if not isinstance(task, dict):
                    continue

                if task.get("status") == "active":
                    task_id = task.get("id", "unknown")
                    active_tasks.append(f"{phase_id}.{task_id}")

        if len(active_tasks) == 0:
            self._add_error(
                Severity.WARNING,
                "Task Focus",
                "No active task found",
                "roadmap.yml:phases",
                "Set exactly one task status to 'active'"
            )
        elif len(active_tasks) > 1:
            self._add_error(
                Severity.CRITICAL,
                "Task Focus",
                f"Multiple active tasks found: {', '.join(active_tasks)}",
                "roadmap.yml:phases",
                "Set only ONE task status to 'active', others to 'pending'"
            )

    def _validate_task_atomicity(self):
        """Check if tasks appear to be atomic."""
        if "phases" not in self.data:
            return

        for phase in self.data["phases"]:
            if not isinstance(phase, dict) or "tasks" not in phase:
                continue

            phase_id = phase.get("id", "unknown")
            for task in phase.get("tasks", []):
                if not isinstance(task, dict):
                    continue

                task_id = task.get("id", "unknown")
                title = task.get("title", "")

                # Check for non-atomic indicators
                title_lower = title.lower()
                found_indicators = [
                    word for word in self.NON_ATOMIC_INDICATORS
                    if word in title_lower
                ]

                if found_indicators:
                    self._add_error(
                        Severity.WARNING,
                        "Task Atomicity",
                        f"Task may not be atomic: '{title}'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}",
                        f"Consider splitting into smaller tasks. "
                        f"Found indicators: {', '.join(found_indicators)}"
                    )

                # Check for conjunctions
                words = title_lower.split()
                found_conjunctions = [
                    word for word in self.CONJUNCTION_WORDS
                    if word in words
                ]

                if found_conjunctions:
                    self._add_error(
                        Severity.WARNING,
                        "Task Atomicity",
                        f"Task may contain multiple actions: '{title}'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}",
                        f"Consider splitting at: {', '.join(found_conjunctions)}"
                    )

                # Check title length
                if len(title) > 80:
                    self._add_error(
                        Severity.WARNING,
                        "Task Atomicity",
                        f"Task title too long ({len(title)} chars): '{title[:50]}...'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}",
                        "Shorten title to <80 chars or split into multiple tasks"
                    )

    def _validate_description_quality(self):
        """Check quality of task descriptions."""
        if "phases" not in self.data:
            return

        for phase in self.data["phases"]:
            if not isinstance(phase, dict) or "tasks" not in phase:
                continue

            phase_id = phase.get("id", "unknown")
            for task in phase.get("tasks", []):
                if not isinstance(task, dict):
                    continue

                task_id = task.get("id", "unknown")
                title = task.get("title", "")
                notes = task.get("notes", "")

                # Check title length
                if len(title) < 10:
                    self._add_error(
                        Severity.WARNING,
                        "Description Quality",
                        f"Task title too short: '{title}'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}.title",
                        "Provide more specific, actionable title (10-80 chars)"
                    )

                # Check for vague titles
                vague_words = ["fix", "update", "change", "modify", "improve"]
                if any(word in title.lower() for word in vague_words) and len(title) < 30:
                    self._add_error(
                        Severity.INFO,
                        "Description Quality",
                        f"Task title may be too vague: '{title}'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}.title",
                        "Be more specific about what to fix/update/change"
                    )

                # Check for missing notes on complex tasks
                if not notes and len(title) > 40:
                    self._add_error(
                        Severity.INFO,
                        "Description Quality",
                        f"Complex task missing notes: '{title}'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}",
                        "Add 'notes:' with requirements, constraints, success criteria"
                    )

                # Check notes length
                if notes and len(notes.strip()) < 20:
                    self._add_error(
                        Severity.INFO,
                        "Description Quality",
                        f"Task notes too brief: '{notes[:30]}...'",
                        f"roadmap.yml:phases.{phase_id}.tasks.{task_id}.notes",
                        "Expand notes with requirements, constraints, acceptance criteria"
                    )


def validate_roadmap_file(roadmap_path: Path) -> List[ValidationError]:
    """Validate a roadmap.yml file.

    Args:
        roadmap_path: Path to roadmap.yml file

    Returns:
        List of validation errors
    """
    manager = RoadmapManager()

    try:
        data = manager.parse_roadmap_yml(roadmap_path)
    except ValueError as e:
        return [ValidationError(
            severity=Severity.CRITICAL,
            category="YAML Parsing",
            message=str(e),
            location=str(roadmap_path),
            remediation="Fix YAML syntax errors"
        )]

    validator = RoadmapSchemaValidator(data)
    return validator.validate()


def print_validation_results(errors: List[ValidationError], roadmap_name: str):
    """Print validation results in formatted output."""
    print("=" * 70)
    print(f"ROADMAP VALIDATION: {roadmap_name}")
    print("=" * 70)
    print()

    if not errors:
        print("✓ No validation errors found")
        print()
        print("Roadmap is compliant with template schema.")
        return

    # Group by severity
    critical = [e for e in errors if e.severity == Severity.CRITICAL]
    warnings = [e for e in errors if e.severity == Severity.WARNING]
    info = [e for e in errors if e.severity == Severity.INFO]

    if critical:
        print(f"CRITICAL ERRORS: {len(critical)}")
        print("-" * 70)
        for error in critical:
            print(str(error))
            print()

    if warnings:
        print(f"WARNINGS: {len(warnings)}")
        print("-" * 70)
        for error in warnings:
            print(str(error))
            print()

    if info:
        print(f"SUGGESTIONS: {len(info)}")
        print("-" * 70)
        for error in info:
            print(str(error))
            print()

    print("=" * 70)
    print(f"Total issues: {len(errors)} "
          f"(Critical: {len(critical)}, Warnings: {len(warnings)}, Info: {len(info)})")
    print("=" * 70)

    if critical:
        print()
        print("❌ VALIDATION FAILED")
        print("Fix all CRITICAL errors before proceeding.")
    elif warnings:
        print()
        print("⚠️  VALIDATION PASSED WITH WARNINGS")
        print("Consider fixing warnings for better roadmap quality.")
    else:
        print()
        print("✓ VALIDATION PASSED")


def main():
    """Main entry point for validation command."""
    if len(sys.argv) < 2:
        print("Usage: validate_schema.py <roadmap-name>")
        print("Example: validate_schema.py api-v2-migration")
        sys.exit(1)

    roadmap_name = sys.argv[1]
    repo_root = Path.cwd()
    roadmap_path = repo_root / "agent_roadmaps" / roadmap_name / "roadmap.yml"

    if not roadmap_path.exists():
        print(f"ERROR: Roadmap not found: {roadmap_path}")
        sys.exit(1)

    errors = validate_roadmap_file(roadmap_path)
    print_validation_results(errors, roadmap_name)

    # Exit with error code if critical errors found
    critical_count = sum(1 for e in errors if e.severity == Severity.CRITICAL)
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == "__main__":
    main()
