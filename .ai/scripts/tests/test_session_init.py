#!/usr/bin/env python3
"""Unit tests for session_init module - constraint loading round-trip tests."""

import tempfile
from pathlib import Path

import pytest

# Import from parent directory
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from project_profile import Language, ProjectProfile, legacy_project_type_to_profile
from session_init import resolve_constraints


class TestConstraintLoadingRoundTrip:
    """Test that legacy project_type values produce identical constraint sets."""

    def test_python_legacy_roundtrip_no_modifications(self):
        """Legacy python project_type loads same constraints as equivalent profile."""
        # Create profile from legacy project_type
        profile = legacy_project_type_to_profile("python")

        # No modified files, no roadmap
        modified_files = []
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        # Expected constraints for pure Python project with no modifications
        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "python/dependencies",
            "python/forbidden-practices",
            "python/security",
            "python/error-handling",
        ]

        assert constraints == expected

    def test_python_legacy_roundtrip_with_py_files(self):
        """Legacy python with .py files loads formatting and type-checking."""
        profile = legacy_project_type_to_profile("python")

        # Modified .py files trigger additional constraints
        modified_files = ["src/main.py", "tests/test_main.py"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "python/dependencies",
            "python/forbidden-practices",
            "python/security",
            "python/error-handling",
            "python/formatting",
            "python/type-checking",
            "python/testing",
        ]

        assert constraints == expected

    def test_python_legacy_roundtrip_with_roadmap(self):
        """Legacy python with active roadmap loads roadmap-awareness."""
        profile = legacy_project_type_to_profile("python")

        modified_files = []
        has_roadmap = True

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "common/roadmap-awareness",
            "python/dependencies",
            "python/forbidden-practices",
            "python/security",
            "python/error-handling",
        ]

        assert constraints == expected

    def test_cpp_legacy_roundtrip_no_modifications(self):
        """Legacy cpp project_type loads same constraints as equivalent profile."""
        profile = legacy_project_type_to_profile("cpp")

        modified_files = []
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "cpp/dependencies",
            "cpp/forbidden-practices",
            "cpp/error-handling",
            "cpp/static-analysis",
        ]

        assert constraints == expected

    def test_cpp_legacy_roundtrip_with_cuda_files(self):
        """Legacy cpp with .cu files loads CUDA constraints."""
        profile = legacy_project_type_to_profile("cpp")

        modified_files = ["src/kernel.cu", "src/kernel.cuh"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "cpp/dependencies",
            "cpp/forbidden-practices",
            "cpp/error-handling",
            "cpp/static-analysis",
            "cpp/cuda",
            "cpp/cuda-modern",
            "cpp/kernel-correctness",
        ]

        assert constraints == expected

    def test_cpp_legacy_roundtrip_with_cmake(self):
        """Legacy cpp with CMakeLists.txt loads cmake constraints."""
        profile = legacy_project_type_to_profile("cpp")

        modified_files = ["CMakeLists.txt", "src/main.cpp"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        expected = [
            "common/instruction-hierarchy",
            "common/git-workflow",
            "common/session-discipline",
            "common/closure-discipline",
            "common/karpathy-guidelines",
            "common/mcp-integration",
            "common/ascii-only",
            "common/agentic-team",
            "cpp/dependencies",
            "cpp/forbidden-practices",
            "cpp/error-handling",
            "cpp/static-analysis",
            "cpp/formatting",
            "cpp/memory-safety",
            "cpp/cmake",
        ]

        assert constraints == expected

    def test_hybrid_profile_loads_both_language_constraints(self):
        """Hybrid profile with both Python and C++ loads both constraint sets."""
        from project_profile import BuildSystem, Distribution, ExternalDependencies

        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD_CORE,
            distribution=Distribution.PYPI_WHEEL,
            external_dependencies=ExternalDependencies.SYSTEM_CUDA,
        )

        modified_files = []
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        # Should have both Python and C++ always-loaded constraints
        assert "python/dependencies" in constraints
        assert "python/forbidden-practices" in constraints
        assert "python/security" in constraints
        assert "python/error-handling" in constraints
        assert "cpp/dependencies" in constraints
        assert "cpp/forbidden-practices" in constraints
        assert "cpp/error-handling" in constraints
        assert "cpp/static-analysis" in constraints
        assert "hybrid/ffi-boundary" in constraints
        assert "hybrid/python-cpp-build" in constraints
        assert "hybrid/system-deps" in constraints

    def test_constraint_deduplication(self):
        """Constraints are deduplicated when loaded multiple times."""
        profile = legacy_project_type_to_profile("python")

        # Multiple .py files should not duplicate constraints
        modified_files = ["a.py", "b.py", "c.py"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        # Check no duplicates
        assert len(constraints) == len(set(constraints))

        # python/formatting and python/type-checking should appear exactly once
        assert constraints.count("python/formatting") == 1
        assert constraints.count("python/type-checking") == 1

    def test_documentation_constraint_loading(self):
        """Documentation files trigger documentation constraints."""
        profile = legacy_project_type_to_profile("python")

        modified_files = ["README.md", "docs/guide.md"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        assert "python/documentation" in constraints

    def test_cpp_documentation_constraint_loading(self):
        """C++ documentation files trigger C++ documentation constraints."""
        profile = legacy_project_type_to_profile("cpp")

        modified_files = ["CONTRIBUTING.md"]
        has_roadmap = False

        constraints = resolve_constraints(profile, modified_files, has_roadmap)

        assert "cpp/documentation" in constraints


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
