#!/usr/bin/env python3
"""Shared utilities for roadmap skill operations."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import yaml


class RoadmapManager:
    """Manager for roadmap operations including YAML parsing and validation."""

    TASK_STATUSES = {"pending", "active", "completed", "blocked"}
    EFFORT_VALUES = {"low", "medium", "high"}
    PHASE_FOLDER_PATTERN = re.compile(r"^phase-\d+-[a-z0-9]+(?:-[a-z0-9]+)*$")
    DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    def __init__(self, repo_root: Optional[Path] = None):
        self.repo_root = repo_root or Path.cwd()
        self.roadmaps_dir = self.repo_root / "agent_roadmaps"

    def _iter_phase_dirs(self):
        if not self.roadmaps_dir.exists():
            return
        for phase_dir in sorted(self.roadmaps_dir.iterdir()):
            if not phase_dir.is_dir():
                continue
            if phase_dir.name in {"template", "archive"}:
                continue
            if not phase_dir.name.startswith("phase-"):
                continue
            if not (phase_dir / "roadmap.yml").exists():
                continue
            yield phase_dir

    @staticmethod
    def derive_branch_name(phase_folder_name: str) -> str:
        return f"roadmap/{phase_folder_name}"

    def parse_roadmap_yml(self, roadmap_path: Path) -> Dict[str, Any]:
        try:
            with open(roadmap_path, "r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle)
        except yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in {roadmap_path}: {exc}") from exc
        except OSError as exc:
            raise ValueError(f"Error reading {roadmap_path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("roadmap.yml must contain a dictionary")
        return data

    def update_roadmap_yml(self, roadmap_path: Path, updates: Dict[str, Any]) -> None:
        current_data = self.parse_roadmap_yml(roadmap_path)
        updated_data = self._deep_merge(current_data, updates)
        self._validate_roadmap_data(updated_data)

        temp_path = roadmap_path.with_suffix(".yml.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                yaml.safe_dump(updated_data, handle, default_flow_style=False, sort_keys=False)
            temp_path.replace(roadmap_path)
        except OSError as exc:
            if temp_path.exists():
                temp_path.unlink()
            raise ValueError(f"Error updating {roadmap_path}: {exc}") from exc

    def find_active_roadmaps(self) -> List[Dict[str, Any]]:
        phases = self.find_all_phases()
        return [phase for phase in phases if phase["status"] == "active"]

    def find_active_roadmap(self) -> Optional[Dict[str, Any]]:
        active = self.find_active_roadmaps()
        return active[0] if active else None

    def find_all_phases(self) -> List[Dict[str, Any]]:
        loaded: List[Tuple[Path, Dict[str, Any]]] = []
        for phase_dir in self._iter_phase_dirs() or []:
            try:
                data = self.parse_roadmap_yml(phase_dir / "roadmap.yml")
            except ValueError:
                continue
            loaded.append((phase_dir, data))

        completion_map: Dict[str, bool] = {}
        for phase_dir, data in loaded:
            completion_map[phase_dir.name] = self.is_phase_completed(data)

        phases: List[Dict[str, Any]] = []
        for phase_dir, data in loaded:
            deps = self.get_phase_dependencies(data)
            unresolved = [dep for dep in deps if not completion_map.get(dep, False)]
            metadata = self._build_phase_metadata(phase_dir, data)
            metadata["depends_on_phases"] = deps
            metadata["unresolved_phase_dependencies"] = unresolved
            metadata["ready"] = len(unresolved) == 0
            phases.append(metadata)

        phases.sort(key=lambda item: item["phase_number"])
        return phases

    def get_phase_dependencies(self, roadmap_data: Dict[str, Any]) -> List[str]:
        deps = roadmap_data.get("depends_on_phases", [])
        if not isinstance(deps, list):
            return []
        result: List[str] = []
        for dep in deps:
            if isinstance(dep, str) and dep.strip():
                result.append(dep.strip())
        return result

    def get_task_map(self, roadmap_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        task_map: Dict[str, Dict[str, Any]] = {}
        for task in roadmap_data.get("tasks", []):
            if isinstance(task, dict) and isinstance(task.get("id"), str):
                task_map[task["id"]] = task
        return task_map

    def get_active_task_id(self, roadmap_data: Dict[str, Any]) -> Optional[str]:
        for task in roadmap_data.get("tasks", []):
            if isinstance(task, dict) and task.get("status") == "active":
                task_id = task.get("id")
                if isinstance(task_id, str):
                    return task_id
        return None

    def get_current_task_id(self, roadmap_data: Dict[str, Any]) -> Optional[str]:
        focus = roadmap_data.get("focus", {})
        if isinstance(focus, dict):
            value = focus.get("current_task")
            if isinstance(value, str) and value:
                return value
        return self.get_active_task_id(roadmap_data)

    def is_phase_completed(self, roadmap_data: Dict[str, Any]) -> bool:
        status = roadmap_data.get("status", {})
        if isinstance(status, dict):
            completed_at = status.get("completed_at")
            if isinstance(completed_at, str) and completed_at.strip():
                return True
        tasks = roadmap_data.get("tasks", [])
        if not isinstance(tasks, list) or not tasks:
            return False
        return all(isinstance(task, dict) and task.get("status") == "completed" for task in tasks)

    def get_ready_task_ids(self, roadmap_data: Dict[str, Any]) -> List[str]:
        task_map = self.get_task_map(roadmap_data)
        completed = {task_id for task_id, task in task_map.items() if task.get("status") == "completed"}

        ready: List[str] = []
        for task in roadmap_data.get("tasks", []):
            if not isinstance(task, dict):
                continue
            if task.get("status") != "pending":
                continue
            task_id = task.get("id")
            if not isinstance(task_id, str):
                continue
            depends_on = task.get("depends_on", [])
            if not isinstance(depends_on, list):
                continue
            if all(dep in completed for dep in depends_on if isinstance(dep, str)):
                ready.append(task_id)
        return ready

    def validate_roadmap_structure(self, roadmap_path: Path) -> List[str]:
        errors: List[str] = []

        required_files = ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]
        for filename in required_files:
            file_path = roadmap_path / filename
            if not file_path.exists():
                errors.append(f"Missing required file: {filename}")
            elif not file_path.is_file():
                errors.append(f"{filename} is not a file")

        sessions_dir = roadmap_path / "sessions"
        if not sessions_dir.exists():
            errors.append("Missing required directory: sessions/")
        elif not sessions_dir.is_dir():
            errors.append("sessions/ is not a directory")

        roadmap_yml = roadmap_path / "roadmap.yml"
        if roadmap_yml.exists():
            try:
                data = self.parse_roadmap_yml(roadmap_yml)
                self._validate_roadmap_data(data)
            except ValueError as exc:
                errors.append(f"Invalid roadmap.yml: {exc}")

        return errors

    def _build_phase_metadata(self, phase_dir: Path, data: Dict[str, Any]) -> Dict[str, Any]:
        status_section = data.get("status", {}) if isinstance(data.get("status", {}), dict) else {}
        active = bool(status_section.get("active", False))
        blocked = bool(status_section.get("blocked", False))

        if active:
            phase_status = "active"
        elif self.is_phase_completed(data):
            phase_status = "completed"
        elif blocked:
            phase_status = "blocked"
        else:
            phase_status = "pending"

        task_count = 0
        completed_count = 0
        for task in data.get("tasks", []):
            if not isinstance(task, dict):
                continue
            task_count += 1
            if task.get("status") == "completed":
                completed_count += 1

        return {
            "name": phase_dir.name,
            "display_name": data.get("name", phase_dir.name),
            "path": str(phase_dir.relative_to(self.repo_root)),
            "status": phase_status,
            "phase_number": self._extract_phase_number(phase_dir.name),
            "roadmap_dir": phase_dir,
            "phase_id": data.get("phase"),
            "current_task": self.get_current_task_id(data),
            "expected_branch": self.derive_branch_name(phase_dir.name),
            "tasks_total": task_count,
            "tasks_completed": completed_count,
            "started_at": status_section.get("started_at"),
            "completed_at": status_section.get("completed_at"),
        }

    def _extract_phase_number(self, folder_name: str) -> int:
        parts = folder_name.split("-")
        if len(parts) < 2:
            return 10**9
        try:
            return int(parts[1])
        except ValueError:
            return 10**9

    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        merged = dict(base)
        for key, value in updates.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged

    def _validate_roadmap_data(self, data: Dict[str, Any]) -> None:
        required_top = {"phase", "name", "status", "depends_on_phases", "tasks", "focus"}
        missing = [key for key in required_top if key not in data]
        if missing:
            raise ValueError(f"Missing required top-level keys: {', '.join(missing)}")

        extra = set(data.keys()) - required_top
        if extra:
            raise ValueError(f"Unknown top-level keys: {', '.join(sorted(extra))}")

        self._validate_phase_id(data["phase"])

        if not isinstance(data["name"], str) or not data["name"].strip():
            raise ValueError("'name' must be a non-empty string")

        self._validate_status(data["status"])
        self._validate_phase_dependencies(data["depends_on_phases"])
        self._validate_tasks(data["tasks"])
        self._validate_focus(data["focus"], data)

    def _validate_phase_id(self, phase_value: Any) -> None:
        if isinstance(phase_value, int):
            if phase_value < 0:
                raise ValueError("'phase' must be >= 0")
            return
        raise ValueError("'phase' must be an integer (e.g., 7)")

    def _validate_status(self, status: Any) -> None:
        if not isinstance(status, dict):
            raise ValueError("'status' must be a dictionary")

        required = {"active", "blocked", "started_at", "completed_at"}
        missing = [key for key in required if key not in status]
        if missing:
            raise ValueError(f"Missing status keys: {', '.join(missing)}")

        if not isinstance(status["active"], bool):
            raise ValueError("'status.active' must be boolean")
        if not isinstance(status["blocked"], bool):
            raise ValueError("'status.blocked' must be boolean")

        for key in ("started_at", "completed_at"):
            value = status[key]
            if value is not None and not isinstance(value, str):
                raise ValueError(f"'status.{key}' must be null or YYYY-MM-DD string")
            if isinstance(value, str) and not self.DATE_PATTERN.match(value):
                raise ValueError(f"'status.{key}' must match YYYY-MM-DD")

    def _validate_phase_dependencies(self, deps: Any) -> None:
        if not isinstance(deps, list):
            raise ValueError("'depends_on_phases' must be a list")

        seen: Set[str] = set()
        for dep in deps:
            if not isinstance(dep, str) or not dep.strip():
                raise ValueError("'depends_on_phases' entries must be non-empty strings")
            dep_name = dep.strip()
            if not self.PHASE_FOLDER_PATTERN.match(dep_name):
                raise ValueError(
                    "Phase dependency must use folder format 'phase-N-name' "
                    f"(got '{dep_name}')"
                )
            if dep_name in seen:
                raise ValueError(f"Duplicate phase dependency: '{dep_name}'")
            seen.add(dep_name)

    def _validate_tasks(self, tasks: Any) -> None:
        if not isinstance(tasks, list) or not tasks:
            raise ValueError("'tasks' must be a non-empty list")

        task_ids: List[str] = []
        active_ids: List[str] = []

        for idx, task in enumerate(tasks):
            if not isinstance(task, dict):
                raise ValueError(f"Task at index {idx} must be a dictionary")

            required = {
                "id",
                "title",
                "description",
                "status",
                "effort",
                "key_files",
                "depends_on",
            }
            missing = [key for key in required if key not in task]
            if missing:
                raise ValueError(f"Task at index {idx} missing keys: {', '.join(missing)}")

            extra = set(task.keys()) - required - {"notes"}
            if extra:
                raise ValueError(f"Task '{task.get('id', idx)}' has unknown keys: {', '.join(sorted(extra))}")

            task_id = task["id"]
            if not isinstance(task_id, str) or not re.match(r"^task-\d+-\d+$", task_id):
                raise ValueError(f"Invalid task id format at index {idx}: '{task_id}'")
            if task_id in task_ids:
                raise ValueError(f"Duplicate task id: '{task_id}'")
            task_ids.append(task_id)

            if not isinstance(task["title"], str) or not task["title"].strip():
                raise ValueError(f"Task '{task_id}' title must be non-empty string")
            if not isinstance(task["description"], str) or not task["description"].strip():
                raise ValueError(f"Task '{task_id}' description must be non-empty string")

            if task["status"] not in self.TASK_STATUSES:
                raise ValueError(
                    f"Task '{task_id}' invalid status '{task['status']}'. "
                    f"Use one of: {', '.join(sorted(self.TASK_STATUSES))}"
                )
            if task["status"] == "active":
                active_ids.append(task_id)

            if task["effort"] not in self.EFFORT_VALUES:
                raise ValueError(
                    f"Task '{task_id}' invalid effort '{task['effort']}'. "
                    f"Use one of: {', '.join(sorted(self.EFFORT_VALUES))}"
                )

            key_files = task["key_files"]
            if not isinstance(key_files, list) or not key_files:
                raise ValueError(f"Task '{task_id}' key_files must be a non-empty list")
            if not all(isinstance(path, str) and path.strip() for path in key_files):
                raise ValueError(f"Task '{task_id}' key_files entries must be non-empty strings")

            depends_on = task["depends_on"]
            if not isinstance(depends_on, list):
                raise ValueError(f"Task '{task_id}' depends_on must be a list")
            for dep in depends_on:
                if not isinstance(dep, str) or not dep.strip():
                    raise ValueError(f"Task '{task_id}' has invalid dependency entry '{dep}'")
                if dep == task_id:
                    raise ValueError(f"Task '{task_id}' cannot depend on itself")

            notes = task.get("notes")
            if notes is not None and not isinstance(notes, str):
                raise ValueError(f"Task '{task_id}' notes must be a string when provided")

        task_id_set = set(task_ids)
        for task in tasks:
            task_id = task["id"]
            for dep in task["depends_on"]:
                if dep not in task_id_set:
                    raise ValueError(
                        f"Task '{task_id}' depends on unknown task '{dep}'"
                    )

        if len(active_ids) > 1:
            raise ValueError(
                "Exactly one active task is allowed; found: " + ", ".join(active_ids)
            )

        self._validate_task_dependency_cycles(tasks)

    def _validate_task_dependency_cycles(self, tasks: List[Dict[str, Any]]) -> None:
        graph: Dict[str, List[str]] = {task["id"]: list(task["depends_on"]) for task in tasks}
        visiting: Set[str] = set()
        visited: Set[str] = set()

        def dfs(task_id: str, trail: List[str]) -> None:
            if task_id in visited:
                return
            if task_id in visiting:
                cycle_start = trail.index(task_id) if task_id in trail else 0
                cycle = trail[cycle_start:] + [task_id]
                raise ValueError("Dependency cycle detected: " + " -> ".join(cycle))

            visiting.add(task_id)
            for dep in graph.get(task_id, []):
                dfs(dep, trail + [task_id])
            visiting.remove(task_id)
            visited.add(task_id)

        for task_id in graph:
            dfs(task_id, [])

    def _validate_focus(self, focus: Any, roadmap: Dict[str, Any]) -> None:
        if not isinstance(focus, dict):
            raise ValueError("'focus' must be a dictionary")

        required = {"current_task", "notes"}
        missing = [key for key in required if key not in focus]
        if missing:
            raise ValueError(f"Missing focus keys: {', '.join(missing)}")

        current_task = focus["current_task"]
        if current_task is not None and not isinstance(current_task, str):
            raise ValueError("'focus.current_task' must be null or task id string")

        notes = focus["notes"]
        if notes is not None and not isinstance(notes, str):
            raise ValueError("'focus.notes' must be a string")

        task_map = self.get_task_map(roadmap)
        active_task_ids = [task_id for task_id, task in task_map.items() if task.get("status") == "active"]

        if current_task and current_task not in task_map:
            raise ValueError(f"focus.current_task '{current_task}' not found in tasks")

        status = roadmap.get("status", {})
        active_phase = bool(status.get("active", False)) if isinstance(status, dict) else False
        blocked_phase = bool(status.get("blocked", False)) if isinstance(status, dict) else False

        if active_phase and not blocked_phase:
            if not current_task:
                raise ValueError("Active and unblocked phase requires focus.current_task")
            if current_task and task_map[current_task].get("status") != "active":
                raise ValueError("focus.current_task must point to the active task")
            if len(active_task_ids) != 1:
                raise ValueError("Active and unblocked phase requires exactly one active task")
        elif active_phase and blocked_phase:
            if len(active_task_ids) > 1:
                raise ValueError("Blocked phase must not have multiple active tasks")
            if current_task and task_map[current_task].get("status") not in {"blocked", "active"}:
                raise ValueError("Blocked phase focus.current_task must point to blocked/active task")
        else:
            if active_task_ids:
                raise ValueError("Inactive phase cannot have active tasks")

        completed_at = status.get("completed_at") if isinstance(status, dict) else None
        if completed_at is not None:
            if not self.is_phase_completed(roadmap):
                raise ValueError("status.completed_at set but not all tasks are completed")
            if active_phase:
                raise ValueError("Completed phase cannot be marked active")
