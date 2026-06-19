#!/usr/bin/env python3
"""Project profile detection and schema reader.

Replaces the binary project_type enum with a composable profile that captures
multiple independent axes: language, build_system, bindings, distribution,
hardware_targets, and external_dependencies.

See ADR 0001 for the full design rationale.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore[import-untyped]
except ImportError:
    yaml = None

_IGNORE_DIRS = frozenset(
    {
        ".claude",
        ".codex",
        ".ai",
        ".git",
        ".github",
        ".vscode",
        ".idea",
        "agent_roadmaps",
        ".venv",
        "venv",
        "__pycache__",
        "build",
        "dist",
        "cmake-build-debug",
        "cmake-build-release",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)


class Language(Enum):
    """Supported programming languages."""

    PYTHON = "python"
    CPP = "cpp"


class BuildSystem(Enum):
    """Supported build systems."""

    POETRY = "poetry"
    CMAKE = "cmake"
    SCIKIT_BUILD = "scikit-build"
    SCIKIT_BUILD_CORE = "scikit-build-core"  # Alias for scikit-build
    BAZEL = "bazel"
    MIXED = "mixed"


class Bindings(Enum):
    """FFI/binding layer options."""

    NONE = "none"
    NANOBIND = "nanobind"
    PYBIND11 = "pybind11"
    TVM_FFI = "tvm-ffi"
    CTYPES = "ctypes"


class Distribution(Enum):
    """Distribution target options."""

    NONE = "none"
    PYPI = "pypi"
    PYPI_WHEEL = "pypi-wheel"
    CONDA = "conda"
    SYSTEM = "system"
    HEADER_ONLY = "header-only"


class HardwareTarget(Enum):
    """Hardware backend options."""

    CPU = "cpu"
    CUDA = "cuda"
    ROCM = "rocm"
    METAL = "metal"
    VULKAN = "vulkan"


class ExternalDependencies(Enum):
    """External dependency strategy options."""

    NONE = "none"
    SYSTEM_CUDA = "system_cuda"
    SYSTEM_NVIDIA = "system_nvidia"
    VENDORED = "vendored"


@dataclass
class ProjectProfile:
    """Composable project profile with multiple independent axes."""

    language: List[Language]
    build_system: BuildSystem
    bindings: Optional[Bindings] = None
    distribution: Optional[Distribution] = None
    hardware_targets: List[HardwareTarget] = field(default_factory=list)
    external_dependencies: Optional[ExternalDependencies] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary representation."""
        result: Dict[str, Any] = {
            "language": [lang.value for lang in self.language],
            "build_system": self.build_system.value,
        }
        if self.bindings:
            result["bindings"] = self.bindings.value
        if self.distribution:
            result["distribution"] = self.distribution.value
        if self.hardware_targets:
            result["hardware_targets"] = [hw.value for hw in self.hardware_targets]
        if self.external_dependencies:
            result["external_dependencies"] = self.external_dependencies.value
        return result

    def has_language(self, lang: Language) -> bool:
        """Check if profile includes a specific language."""
        return lang in self.language

    def is_hybrid(self) -> bool:
        """Check if profile is a hybrid multi-language project."""
        return len(self.language) > 1


def _read_profile_from_yml(repo_root: Path) -> Optional[ProjectProfile]:
    """Read project_profile from .ai/project.yml."""
    yml_path = repo_root / ".ai" / "project.yml"
    if not yml_path.exists():
        return None

    try:
        content = yml_path.read_text()
    except OSError:
        return None

    # Try YAML parsing if available
    if yaml is not None:
        try:
            data = yaml.safe_load(content)
            if not isinstance(data, dict):
                return None

            profile_data = data.get("project_profile")
            if profile_data and isinstance(profile_data, dict):
                return _parse_profile_dict(profile_data)
        except yaml.YAMLError:
            pass

    # Fallback: simple line-by-line parsing for project_profile
    lines = content.splitlines()
    in_profile = False
    profile_lines = []

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("project_profile:"):
            in_profile = True
            continue
        if in_profile:
            if stripped and not stripped.startswith("#"):
                if not line.startswith(" ") and not line.startswith("\t"):
                    # End of profile block
                    break
                profile_lines.append(stripped)

    if profile_lines:
        # Simple key-value parsing
        profile_dict: Dict[str, Any] = {}
        for line in profile_lines:
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()
                # Handle list syntax [a, b]
                if value.startswith("[") and value.endswith("]"):
                    value = [v.strip() for v in value[1:-1].split(",") if v.strip()]
                profile_dict[key] = value

        if profile_dict:
            return _parse_profile_dict(profile_dict)

    return None


def _parse_profile_dict(data: Dict[str, Any]) -> Optional[ProjectProfile]:
    """Parse a profile dictionary into a ProjectProfile object."""
    try:
        # Parse language (required, can be list or single value)
        lang_raw = data.get("language")
        if not lang_raw:
            return None

        if isinstance(lang_raw, str):
            lang_list = [lang_raw]
        elif isinstance(lang_raw, list):
            lang_list = lang_raw
        else:
            return None

        languages = []
        for lang_str in lang_list:
            try:
                languages.append(Language(lang_str))
            except ValueError:
                return None

        if not languages:
            return None

        # Parse build_system (required)
        build_sys_raw = data.get("build_system")
        if not build_sys_raw:
            return None

        try:
            build_system = BuildSystem(build_sys_raw)
        except ValueError:
            return None

        # Parse optional fields
        bindings = None
        bindings_raw = data.get("bindings")
        if bindings_raw:
            try:
                bindings = Bindings(bindings_raw)
            except ValueError:
                pass

        distribution = None
        dist_raw = data.get("distribution")
        if dist_raw:
            try:
                distribution = Distribution(dist_raw)
            except ValueError:
                pass

        hardware_targets = []
        hw_raw = data.get("hardware_targets")
        if hw_raw:
            if isinstance(hw_raw, str):
                hw_list = [hw_raw]
            elif isinstance(hw_raw, list):
                hw_list = hw_raw
            else:
                hw_list = []

            for hw_str in hw_list:
                try:
                    hardware_targets.append(HardwareTarget(hw_str))
                except ValueError:
                    pass

        external_deps = None
        ext_deps_raw = data.get("external_dependencies")
        if ext_deps_raw:
            try:
                external_deps = ExternalDependencies(ext_deps_raw)
            except ValueError:
                pass

        return ProjectProfile(
            language=languages,
            build_system=build_system,
            bindings=bindings,
            distribution=distribution,
            hardware_targets=hardware_targets,
            external_dependencies=external_deps,
        )
    except Exception:
        return None


def _read_legacy_project_type(repo_root: Path) -> Optional[str]:
    """Read legacy project_type from .ai/project.yml."""
    yml = repo_root / ".ai" / "project.yml"
    if not yml.exists():
        return None

    try:
        for line in yml.read_text().splitlines():
            stripped = line.strip()
            if stripped.startswith("project_type:"):
                value = stripped.split(":", 1)[1].strip()
                if value in ("python", "cpp"):
                    return value
    except Exception:
        return None

    return None


def legacy_project_type_to_profile(project_type: str) -> ProjectProfile:
    """Convert legacy project_type value to equivalent ProjectProfile.

    Args:
        project_type: Legacy project type ("python" or "cpp")

    Returns:
        Equivalent ProjectProfile

    Raises:
        ValueError: If project_type is not a recognized legacy value
    """
    if project_type == "python":
        return ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
    elif project_type == "cpp":
        return ProjectProfile(
            language=[Language.CPP],
            build_system=BuildSystem.CMAKE,
            hardware_targets=[HardwareTarget.CUDA, HardwareTarget.CPU],
            external_dependencies=ExternalDependencies.SYSTEM_CUDA,
        )
    else:
        raise ValueError(f"Unknown legacy project_type: {project_type}")


def _heuristic_detect(repo_root: Path) -> Optional[ProjectProfile]:
    """Heuristic detection when no explicit configuration exists."""
    python_score = 0
    cpp_score = 0

    for entry in repo_root.iterdir():
        if entry.name in _IGNORE_DIRS:
            continue

        if entry.is_file():
            name = entry.name
            if name in (
                "pyproject.toml",
                "setup.py",
                "setup.cfg",
                "requirements.txt",
                "poetry.lock",
                "Pipfile",
            ):
                python_score += 3
            elif name.endswith(".py"):
                python_score += 1
            elif name in (
                "CMakeLists.txt",
                "Makefile",
            ):
                cpp_score += 3
            elif name.endswith((".cpp", ".hpp", ".cu", ".cuh", ".h")):
                cpp_score += 1

        elif entry.is_dir():
            if entry.name in ("cmake", "cpp", "cuda", "3rdparty"):
                cpp_score += 2
            try:
                children = list(entry.iterdir())
            except PermissionError:
                continue

            for child in children:
                if not child.is_file():
                    continue
                if child.suffix == ".py":
                    python_score += 1
                elif child.suffix in (".cpp", ".hpp", ".cu", ".cuh", ".h"):
                    cpp_score += 1

    if python_score == 0 and cpp_score == 0:
        return None

    # Map heuristic result to legacy profile
    if python_score >= cpp_score:
        return legacy_project_type_to_profile("python")
    else:
        return legacy_project_type_to_profile("cpp")


def detect(repo_root: Optional[Path] = None) -> Optional[ProjectProfile]:
    """Detect project profile from configuration or heuristics.

    Args:
        repo_root: Repository root path (defaults to current directory)

    Returns:
        ProjectProfile if detected, None if unknown
    """
    root = repo_root or Path.cwd()

    # Try reading new project_profile first
    profile = _read_profile_from_yml(root)
    if profile:
        return profile

    # Try reading legacy project_type and converting
    legacy_type = _read_legacy_project_type(root)
    if legacy_type:
        return legacy_project_type_to_profile(legacy_type)

    # Fall back to heuristic detection
    return _heuristic_detect(root)
