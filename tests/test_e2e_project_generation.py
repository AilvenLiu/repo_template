#!/usr/bin/env python3
"""End-to-end test for project generation and capability audit."""

import shutil
import sys
import tempfile
from pathlib import Path

import pytest

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "common"))
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "create-project" / "scripts"))

from capability_audit import run_audit
from init import create_project


@pytest.fixture
def template_root():
    """Get the template repository root."""
    return Path(__file__).parent.parent


def test_e2e_python_project_generation_and_audit(template_root):
    """End-to-end test: generate Python project and verify audit works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_project"

        # Call create_project directly
        create_project(template_root, target, "python")

        # Verify key files exist
        assert (target / ".ai" / "capabilities.yml").exists(), "capabilities.yml missing"
        assert (target / ".ai" / "project.yml").exists(), "project.yml missing"
        assert (target / "AGENTS.md").exists(), "AGENTS.md missing"
        assert (target / "CLAUDE.md").exists(), "CLAUDE.md missing"

        # Verify template-only files are removed
        assert not (target / "AGENTS_PYTHON.md").exists(), "Template file not removed"
        assert not (target / "AGENTS_CPP.md").exists(), "Template file not removed"
        assert not (target / ".claude" / "skills" / "create-project").exists(), \
            "create-project skill not removed"

        # Run capability audit on generated project
        # Note: This will fail because plugins aren't installed, but we're testing
        # that the audit runs without errors (no missing manifest, etc.)
        audit_result = run_audit(target, is_claude=False, verbose=False)

        # Verify audit ran (even if it failed due to missing plugins)
        assert audit_result is not None
        assert hasattr(audit_result, "passed")
        assert hasattr(audit_result, "entries")

        # Verify create-project skill is NOT in the audit (template_only)
        create_project_entries = [
            e for e in audit_result.entries
            if e.capability_id == "create-project"
        ]
        assert len(create_project_entries) == 0, \
            "create-project skill should be skipped in generated projects"


def test_e2e_cpp_project_generation_and_audit(template_root):
    """End-to-end test: generate C++ project and verify audit works."""
    with tempfile.TemporaryDirectory() as tmpdir:
        target = Path(tmpdir) / "test_cpp_project"

        # Call create_project directly
        create_project(template_root, target, "cpp")

        # Verify key files exist
        assert (target / ".ai" / "capabilities.yml").exists(), "capabilities.yml missing"
        assert (target / ".ai" / "project.yml").exists(), "project.yml missing"
        assert (target / "CMakeLists.txt").exists(), "CMakeLists.txt missing"

        # Run capability audit
        audit_result = run_audit(target, is_claude=False, verbose=False)

        # Verify audit ran
        assert audit_result is not None
        assert hasattr(audit_result, "passed")

        # Verify create-project skill is NOT in the audit
        create_project_entries = [
            e for e in audit_result.entries
            if e.capability_id == "create-project"
        ]
        assert len(create_project_entries) == 0
