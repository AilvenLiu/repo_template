#!/usr/bin/env python3
"""Tests for capability_audit.py selector evaluation and backward compatibility."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from capability_audit import _evaluate_when_selector, _entry_enabled_for_repo
from project_profile import (
    ProjectProfile,
    Language,
    BuildSystem,
    Bindings,
    Distribution,
    HardwareTarget,
    ExternalDependencies,
)


class TestWhenSelectorEvaluation:
    """Test the when selector parsing and evaluation logic."""

    def test_language_equality_match(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("language=python", profile) is True

    def test_language_equality_no_match(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("language=cpp", profile) is False

    def test_language_in_list_match(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("language in [python, cpp]", profile) is True

    def test_language_in_list_no_match(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("language in [cpp, rust]", profile) is False

    def test_hybrid_language_matches_either(self):
        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
        )
        assert _evaluate_when_selector("language=python", profile) is True
        assert _evaluate_when_selector("language=cpp", profile) is True

    def test_hybrid_language_in_list(self):
        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
        )
        assert _evaluate_when_selector("language in [python, cpp]", profile) is True
        assert _evaluate_when_selector("language in [python]", profile) is True
        assert _evaluate_when_selector("language in [cpp]", profile) is True
        assert _evaluate_when_selector("language in [rust]", profile) is False

    def test_build_system_equality(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("build_system=poetry", profile) is True
        assert _evaluate_when_selector("build_system=cmake", profile) is False

    def test_build_system_in_list(self):
        profile = ProjectProfile(
            language=[Language.CPP],
            build_system=BuildSystem.CMAKE,
        )
        assert _evaluate_when_selector("build_system in [cmake, bazel]", profile) is True
        assert _evaluate_when_selector("build_system in [poetry, scikit-build]", profile) is False

    def test_bindings_equality(self):
        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD,
            bindings=Bindings.NANOBIND,
        )
        assert _evaluate_when_selector("bindings=nanobind", profile) is True
        assert _evaluate_when_selector("bindings=pybind11", profile) is False

    def test_bindings_none(self):
        profile = ProjectProfile(
            language=[Language.CPP],
            build_system=BuildSystem.CMAKE,
            bindings=None,
        )
        assert _evaluate_when_selector("bindings=none", profile) is True
        assert _evaluate_when_selector("bindings=nanobind", profile) is False

    def test_hardware_targets_equality(self):
        profile = ProjectProfile(
            language=[Language.CPP],
            build_system=BuildSystem.CMAKE,
            hardware_targets=[HardwareTarget.CUDA, HardwareTarget.CPU],
        )
        assert _evaluate_when_selector("hardware_targets=cuda", profile) is True
        assert _evaluate_when_selector("hardware_targets=cpu", profile) is True
        assert _evaluate_when_selector("hardware_targets=rocm", profile) is False

    def test_hardware_targets_in_list(self):
        profile = ProjectProfile(
            language=[Language.CPP],
            build_system=BuildSystem.CMAKE,
            hardware_targets=[HardwareTarget.CUDA],
        )
        assert _evaluate_when_selector("hardware_targets in [cuda, rocm]", profile) is True
        assert _evaluate_when_selector("hardware_targets in [rocm, webgpu]", profile) is False

    def test_empty_selector_returns_true(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("", profile) is True
        assert _evaluate_when_selector("   ", profile) is True

    def test_invalid_selector_returns_false(self):
        profile = ProjectProfile(
            language=[Language.PYTHON],
            build_system=BuildSystem.POETRY,
        )
        assert _evaluate_when_selector("invalid syntax", profile) is False
        assert _evaluate_when_selector("unknown_axis=value", profile) is False


class TestBackwardCompatibility:
    """Test that legacy project_types field still works via profile detection."""

    def test_entry_with_when_selector_python(self, tmp_path):
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        entry = {"id": "python-env-setup", "when": "language=python"}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is True

    def test_entry_with_when_selector_cpp_no_match(self, tmp_path):
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        entry = {"id": "cpp-tool", "when": "language=cpp"}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is False

    def test_entry_with_legacy_project_types_python(self, tmp_path):
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        entry = {"id": "python-env-setup", "project_types": ["python"]}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is True

    def test_entry_with_legacy_project_types_cpp_no_match(self, tmp_path):
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        entry = {"id": "cpp-tool", "project_types": ["cpp"]}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is False

    def test_when_selector_takes_precedence_over_project_types(self, tmp_path):
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        # when selector should be evaluated, project_types ignored
        entry = {
            "id": "test-skill",
            "when": "language=python",
            "project_types": ["cpp"],  # This should be ignored
        }
        assert _entry_enabled_for_repo(entry, False, tmp_path) is True

    def test_template_only_filtering(self, tmp_path):
        # Non-template repo
        entry = {"id": "create-project", "template_only": True}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is False

        # Template repo
        assert _entry_enabled_for_repo(entry, True, tmp_path) is True

    def test_no_selector_always_enabled(self, tmp_path):
        # Entry with no when or project_types should always be enabled
        entry = {"id": "common-skill"}
        assert _entry_enabled_for_repo(entry, False, tmp_path) is True


class TestAuditFixtures:
    """Fixture tests: verify legacy project_types produce identical audit results."""

    def test_python_project_audit_equivalence(self, tmp_path):
        """Verify that when=language=python and project_types=[python] produce same results."""
        # Create a Python project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        # Test with when selector
        entry_when = {"id": "python-env-setup", "when": "language=python"}
        result_when = _entry_enabled_for_repo(entry_when, False, tmp_path)

        # Test with legacy project_types
        entry_legacy = {"id": "python-env-setup", "project_types": ["python"]}
        result_legacy = _entry_enabled_for_repo(entry_legacy, False, tmp_path)

        assert result_when == result_legacy == True

    def test_cpp_project_audit_equivalence(self, tmp_path):
        """Verify that when=language=cpp and project_types=[cpp] produce same results."""
        # Create a C++ project
        cmake = tmp_path / "CMakeLists.txt"
        cmake.write_text("project(test)\n")

        # Test with when selector
        entry_when = {"id": "cpp-tool", "when": "language=cpp"}
        result_when = _entry_enabled_for_repo(entry_when, False, tmp_path)

        # Test with legacy project_types
        entry_legacy = {"id": "cpp-tool", "project_types": ["cpp"]}
        result_legacy = _entry_enabled_for_repo(entry_legacy, False, tmp_path)

        assert result_when == result_legacy == True

    def test_hybrid_project_enables_both_languages(self, tmp_path):
        """Verify that hybrid projects enable skills for both languages."""
        # Create a project with explicit hybrid profile in .ai/project.yml
        ai_dir = tmp_path / ".ai"
        ai_dir.mkdir()
        project_yml = ai_dir / "project.yml"
        project_yml.write_text(
            "project_profile:\n"
            "  language: [python, cpp]\n"
            "  build_system: scikit-build\n"
        )

        # Python skill should be enabled
        python_entry = {"id": "python-env-setup", "when": "language=python"}
        assert _entry_enabled_for_repo(python_entry, False, tmp_path) is True

        # C++ skill should be enabled
        cpp_entry = {"id": "cpp-tool", "when": "language=cpp"}
        assert _entry_enabled_for_repo(cpp_entry, False, tmp_path) is True

    def test_common_skills_always_enabled(self, tmp_path):
        """Verify that skills without selectors are always enabled."""
        # Create any project
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.poetry]\nname = 'test'\n")

        common_entry = {"id": "roadmap"}
        assert _entry_enabled_for_repo(common_entry, False, tmp_path) is True
