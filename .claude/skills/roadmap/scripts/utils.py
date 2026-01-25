#!/usr/bin/env python3
"""Shared utilities for roadmap skill operations."""

import yaml
from pathlib import Path
from typing import Dict, Optional, List, Any


class RoadmapManager:
    """Manager for roadmap operations including YAML parsing and validation."""

    def __init__(self, repo_root: Optional[Path] = None):
        """Initialise roadmap manager.

        Args:
            repo_root: Repository root path. If None, uses current directory.
        """
        self.repo_root = repo_root or Path.cwd()
        self.roadmaps_dir = self.repo_root / "agent_roadmaps"

    def find_active_roadmap(self) -> Optional[Dict[str, Any]]:
        """Scan for active roadmap and return metadata.

        Returns:
            Dictionary with roadmap metadata if active roadmap found, None otherwise.
            Metadata includes: name, path, current_phase, current_task, status
        """
        if not self.roadmaps_dir.exists():
            return None

        for roadmap_dir in self.roadmaps_dir.iterdir():
            # Skip template directory and non-directories
            if not roadmap_dir.is_dir() or roadmap_dir.name == "template":
                continue

            roadmap_yml = roadmap_dir / "roadmap.yml"
            if not roadmap_yml.exists():
                continue

            try:
                data = self.parse_roadmap_yml(roadmap_yml)
                if data.get("status", {}).get("active", False):
                    current_focus = data.get("current_focus", {})
                    return {
                        "name": data.get("roadmap", {}).get("name", roadmap_dir.name),
                        "path": str(roadmap_dir.relative_to(self.repo_root)),
                        "current_phase": current_focus.get("phase", "unknown"),
                        "current_task": current_focus.get("task", "unknown"),
                        "status": "active",
                        "roadmap_dir": roadmap_dir,
                    }
            except Exception:
                # Skip malformed roadmaps
                continue

        return None

    def parse_roadmap_yml(self, roadmap_path: Path) -> Dict[str, Any]:
        """Parse and validate roadmap.yml structure.

        Args:
            roadmap_path: Path to roadmap.yml file

        Returns:
            Parsed YAML data as dictionary

        Raises:
            ValueError: If YAML is malformed or invalid
        """
        try:
            with open(roadmap_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if not isinstance(data, dict):
                    raise ValueError("roadmap.yml must contain a dictionary")
                return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {roadmap_path}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading {roadmap_path}: {e}")

    def update_roadmap_yml(self, roadmap_path: Path, updates: Dict[str, Any]) -> None:
        """Atomically update roadmap.yml with validation.

        Args:
            roadmap_path: Path to roadmap.yml file
            updates: Dictionary of updates to apply (deep merge)

        Raises:
            ValueError: If update would create invalid state
        """
        # Read current data
        current_data = self.parse_roadmap_yml(roadmap_path)

        # Apply updates (deep merge)
        updated_data = self._deep_merge(current_data, updates)

        # Validate updated data
        self._validate_roadmap_data(updated_data)

        # Write atomically (write to temp file, then rename)
        temp_path = roadmap_path.with_suffix(".yml.tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(updated_data, f, default_flow_style=False, sort_keys=False)
            temp_path.replace(roadmap_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise ValueError(f"Error updating {roadmap_path}: {e}")

    def validate_roadmap_structure(self, roadmap_path: Path) -> List[str]:
        """Validate all required files exist and are well-formed.

        Args:
            roadmap_path: Path to roadmap directory

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required files
        required_files = ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]
        for filename in required_files:
            file_path = roadmap_path / filename
            if not file_path.exists():
                errors.append(f"Missing required file: {filename}")
            elif not file_path.is_file():
                errors.append(f"{filename} is not a file")

        # Check sessions directory
        sessions_dir = roadmap_path / "sessions"
        if not sessions_dir.exists():
            errors.append("Missing required directory: sessions/")
        elif not sessions_dir.is_dir():
            errors.append("sessions/ is not a directory")

        # Validate roadmap.yml structure
        roadmap_yml = roadmap_path / "roadmap.yml"
        if roadmap_yml.exists():
            try:
                data = self.parse_roadmap_yml(roadmap_yml)
                self._validate_roadmap_data(data)
            except ValueError as e:
                errors.append(f"Invalid roadmap.yml: {e}")

        return errors

    def _deep_merge(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two dictionaries.

        Args:
            base: Base dictionary
            updates: Updates to apply

        Returns:
            Merged dictionary
        """
        result = base.copy()
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _validate_roadmap_data(self, data: Dict[str, Any]) -> None:
        """Validate roadmap.yml data structure.

        Args:
            data: Parsed roadmap.yml data

        Raises:
            ValueError: If data structure is invalid
        """
        # Check required top-level keys
        required_keys = ["roadmap", "status", "current_focus", "phases"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")

        # Validate roadmap section
        roadmap = data["roadmap"]
        if not isinstance(roadmap, dict):
            raise ValueError("'roadmap' must be a dictionary")
        if "name" not in roadmap:
            raise ValueError("'roadmap' must have 'name' field")

        # Validate status section
        status = data["status"]
        if not isinstance(status, dict):
            raise ValueError("'status' must be a dictionary")
        for key in ["active", "blocked", "completed"]:
            if key not in status:
                raise ValueError(f"'status' must have '{key}' field")
            if not isinstance(status[key], bool):
                raise ValueError(f"'status.{key}' must be boolean")

        # Validate current_focus section
        current_focus = data["current_focus"]
        if not isinstance(current_focus, dict):
            raise ValueError("'current_focus' must be a dictionary")

        # Validate phases section
        phases = data["phases"]
        if not isinstance(phases, list):
            raise ValueError("'phases' must be a list")
        for phase in phases:
            if not isinstance(phase, dict):
                raise ValueError("Each phase must be a dictionary")
            if "id" not in phase:
                raise ValueError("Each phase must have 'id' field")
            if "tasks" in phase and not isinstance(phase["tasks"], list):
                raise ValueError("Phase 'tasks' must be a list")
