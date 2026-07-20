#!/usr/bin/env python3
"""Unit tests for project_type backward compatibility shim."""

import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from project_type import ProjectType, detect


class TestProjectTypeShim:
    """Test backward compatibility of project_type module."""

    def test_detect_returns_project_type_enum(self):
        """detect() returns ProjectType enum."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("project_type: python\n")

            result = detect(repo_root)
            assert isinstance(result, ProjectType)
            assert result == ProjectType.PYTHON

    def test_detect_legacy_python(self):
        """Shim correctly detects legacy Python project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("project_type: python\n")

            result = detect(repo_root)
            assert result == ProjectType.PYTHON

    def test_detect_legacy_cpp(self):
        """Shim correctly detects legacy C++ project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("project_type: cpp\n")

            result = detect(repo_root)
            assert result == ProjectType.CPP

    def test_detect_new_python_profile(self):
        """Shim correctly maps new Python profile to PYTHON."""
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

            result = detect(repo_root)
            assert result == ProjectType.PYTHON

    def test_detect_new_cpp_profile(self):
        """Shim correctly maps new C++ profile to CPP."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [cpp]
  build_system: cmake
""")

            result = detect(repo_root)
            assert result == ProjectType.CPP

    def test_detect_hybrid_profile_prefers_python(self):
        """Shim maps hybrid profile with Python to PYTHON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            ai_dir = repo_root / ".agents"
            ai_dir.mkdir()

            project_yml = ai_dir / "project.yml"
            project_yml.write_text("""
project_profile:
  language: [python, cpp]
  build_system: scikit-build
""")

            result = detect(repo_root)
            # Hybrid projects with Python default to PYTHON
            assert result == ProjectType.PYTHON

    def test_detect_unknown(self):
        """Shim returns UNKNOWN when detection fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)

            result = detect(repo_root)
            assert result == ProjectType.UNKNOWN

    def test_project_type_enum_values(self):
        """ProjectType enum has expected values."""
        assert ProjectType.PYTHON.value == "python"
        assert ProjectType.CPP.value == "cpp"
        assert ProjectType.UNKNOWN.value == "unknown"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
