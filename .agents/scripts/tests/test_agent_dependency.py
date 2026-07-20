"""Tests for dependency management dispatch logic."""

import sys
from pathlib import Path


# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dependency.utils import DependencyManager, BuildSystem
from project_profile import Language


class TestDependencyManagerDispatch:
    """Test that DependencyManager correctly detects build systems from profiles."""

    def test_detect_poetry_from_profile(self, tmp_path):
        """Test detecting poetry build system from project_profile."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_profile:
  language: [python]
  build_system: poetry
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.POETRY
        assert Language.PYTHON in profile.language

    def test_detect_cmake_from_profile(self, tmp_path):
        """Test detecting cmake build system from project_profile."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_profile:
  language: [cpp]
  build_system: cmake
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.CMAKE
        assert Language.CPP in profile.language

    def test_detect_scikit_build_from_profile(self, tmp_path):
        """Test detecting scikit-build from project_profile."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_profile:
  language: [python, cpp]
  build_system: scikit-build
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.SCIKIT_BUILD
        assert Language.PYTHON in profile.language
        assert Language.CPP in profile.language

    def test_detect_bazel_from_profile(self, tmp_path):
        """Test detecting bazel from project_profile."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_profile:
  language: [cpp]
  build_system: bazel
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.BAZEL
        assert Language.CPP in profile.language

    def test_detect_mixed_from_profile(self, tmp_path):
        """Test detecting mixed build system from project_profile."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_profile:
  language: [python, cpp]
  build_system: mixed
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.MIXED


class TestDependencyBackwardCompatibility:
    """Test that legacy project_type field still works."""

    def test_legacy_python_maps_to_poetry(self, tmp_path):
        """Test that project_type: python maps to poetry build system."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("project_type: python\n")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.POETRY
        assert Language.PYTHON in profile.language

    def test_legacy_cpp_maps_to_cmake(self, tmp_path):
        """Test that project_type: cpp maps to cmake build system."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("project_type: cpp\n")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        assert profile.build_system == BuildSystem.CMAKE
        assert Language.CPP in profile.language

    def test_profile_takes_precedence_over_legacy(self, tmp_path):
        """Test that project_profile.build_system takes precedence over project_type."""
        ai_dir = tmp_path / ".agents"
        ai_dir.mkdir()

        project_yml = ai_dir / "project.yml"
        project_yml.write_text("""
project_type: python
project_profile:
  language: [cpp]
  build_system: cmake
""")

        manager = DependencyManager(tmp_path)
        profile = manager.detect_project_profile()

        # Profile should take precedence
        assert profile.build_system == BuildSystem.CMAKE
        assert Language.CPP in profile.language
