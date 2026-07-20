#!/usr/bin/env python3
"""Unit tests for project_profile module."""

import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from project_profile import (
    Bindings,
    BuildSystem,
    Distribution,
    ExternalDependencies,
    HardwareTarget,
    Language,
    ProjectProfile,
    detect,
    legacy_project_type_to_profile,
)


class TestLegacyMapping:
    """Test legacy project_type to ProjectProfile mapping."""

    def test_legacy_python_mapping(self):
        """Legacy project_type: python maps to correct profile."""
        profile = legacy_project_type_to_profile("python")

        assert profile.language == [Language.PYTHON]
        assert profile.build_system == BuildSystem.POETRY
        assert profile.bindings is None
        assert profile.distribution is None
        assert profile.hardware_targets == []
        assert profile.external_dependencies is None

    def test_legacy_cpp_mapping(self):
        """Legacy project_type: cpp maps to correct profile."""
        profile = legacy_project_type_to_profile("cpp")

        assert profile.language == [Language.CPP]
        assert profile.build_system == BuildSystem.CMAKE
        assert profile.hardware_targets == [HardwareTarget.CUDA, HardwareTarget.CPU]
        assert profile.external_dependencies == ExternalDependencies.SYSTEM_CUDA

    def test_legacy_unknown_raises(self):
        """Unknown legacy project_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown legacy project_type"):
            legacy_project_type_to_profile("unknown")

    def test_legacy_invalid_raises(self):
        """Invalid legacy project_type raises ValueError."""
        with pytest.raises(ValueError, match="Unknown legacy project_type"):
            legacy_project_type_to_profile("javascript")


class TestProfileParsing:
    """Test parsing of new project_profile blocks."""

    def test_parse_python_profile(self):
        """Parse a pure Python profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [python]
  build_system: poetry
""")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.PYTHON]
            assert profile.build_system == BuildSystem.POETRY

    def test_parse_cpp_profile(self):
        """Parse a pure C++ profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [cpp]
  build_system: cmake
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
""")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.CPP]
            assert profile.build_system == BuildSystem.CMAKE
            assert HardwareTarget.CUDA in profile.hardware_targets
            assert HardwareTarget.CPU in profile.hardware_targets
            assert profile.external_dependencies == ExternalDependencies.SYSTEM_CUDA

    def test_parse_hybrid_profile(self):
        """Parse a hybrid Python+C++ profile."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [python, cpp]
  build_system: scikit-build-core
  bindings: nanobind
  distribution: pypi-wheel
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
""")

            profile = detect(repo_root)
            assert profile is not None
            assert Language.PYTHON in profile.language
            assert Language.CPP in profile.language
            assert profile.build_system == BuildSystem.SCIKIT_BUILD_CORE
            assert profile.bindings == Bindings.NANOBIND
            assert profile.distribution == Distribution.PYPI_WHEEL
            assert profile.is_hybrid()

    def test_parse_single_language_string(self):
        """Parse profile with language as single string (not list)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: python
  build_system: poetry
""")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.PYTHON]

    def test_parse_missing_required_field(self):
        """Profile missing required field returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            # Missing build_system
            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [python]
""")

            profile = detect(repo_root)
            # Should fall back to heuristic, which will detect nothing
            assert profile is None

    def test_parse_invalid_enum_value(self):
        """Profile with invalid enum value returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [javascript]
  build_system: npm
""")

            profile = detect(repo_root)
            assert profile is None


class TestLegacyProjectTypeDetection:
    """Test detection of legacy project_type values."""

    def test_detect_legacy_python(self):
        """Detect legacy project_type: python."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("project_type: python\n")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.PYTHON]
            assert profile.build_system == BuildSystem.POETRY

    def test_detect_legacy_cpp(self):
        """Detect legacy project_type: cpp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("project_type: cpp\n")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.CPP]
            assert profile.build_system == BuildSystem.CMAKE


class TestHeuristicDetection:
    """Test heuristic detection when no configuration exists."""

    def test_heuristic_python(self):
        """Heuristic detects Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create Python markers
            (repo_root / "pyproject.toml").write_text("[tool.poetry]\n")
            (repo_root / "main.py").write_text("print('hello')\n")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.PYTHON]
            assert profile.build_system == BuildSystem.POETRY

    def test_heuristic_cpp(self):
        """Heuristic detects C++ project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            # Create C++ markers
            (repo_root / "CMakeLists.txt").write_text("project(test)\n")
            (repo_root / "main.cpp").write_text("int main() {}\n")

            profile = detect(repo_root)
            assert profile is not None
            assert profile.language == [Language.CPP]
            assert profile.build_system == BuildSystem.CMAKE

    def test_heuristic_no_markers(self):
        """Heuristic returns None when no markers found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            profile = detect(repo_root)
            assert profile is None


class TestProfileMethods:
    """Test ProjectProfile helper methods."""

    def test_has_language(self):
        """Test has_language() method."""
        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
        )

        assert profile.has_language(Language.PYTHON)
        assert profile.has_language(Language.CPP)

    def test_is_hybrid(self):
        """Test is_hybrid() method."""
        hybrid = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
        )
        assert hybrid.is_hybrid()

        pure = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert not pure.is_hybrid()

    def test_to_dict(self):
        """Test to_dict() serialization."""
        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
            bindings=Bindings.NANOBIND,
            distribution=Distribution.PYPI,
            hardware_targets=[HardwareTarget.CUDA],
            external_dependencies=ExternalDependencies.SYSTEM_CUDA,
        )

        result = profile.to_dict()
        assert result["language"] == ["python", "cpp"]
        assert result["build_system"] == "scikit-build"
        assert result["bindings"] == "nanobind"
        assert result["distribution"] == "pypi"
        assert result["hardware_targets"] == ["cuda"]
        assert result["external_dependencies"] == "system_cuda"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
