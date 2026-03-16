#!/usr/bin/env python3
"""Tests for capability audit system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".claude" / "skills" / "common"))

from capability_audit import run_audit, AuditResult


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)

        # Create basic structure
        (repo / ".ai").mkdir()
        (repo / ".claude" / "skills").mkdir(parents=True)

        yield repo


@pytest.fixture
def minimal_manifest(temp_repo):
    """Create a minimal capabilities.yml manifest."""
    manifest = {
        "claude_plugins": [
            {"id": "test-plugin@test-source", "required": True}
        ],
        "project_skills": [
            {"id": "test-skill", "required": True}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)
    return temp_repo


def test_audit_missing_manifest(temp_repo):
    """Test audit fails when capabilities.yml is missing."""
    result = run_audit(temp_repo, is_claude=True, verbose=False)
    assert not result.passed
    assert any("manifest not found" in e.lower() for e in result.errors)


def test_audit_missing_plugin(minimal_manifest):
    """Test audit detects missing required plugin."""
    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        # Mock `claude plugins list` returning empty list
        mock_run.return_value = "Installed plugins:\n\n(none)\n"
        result = run_audit(minimal_manifest, is_claude=True, verbose=False)

    assert not result.passed
    plugin_entries = [e for e in result.entries if e.category == "claude_plugin"]
    assert len(plugin_entries) == 1
    assert not plugin_entries[0].available
    assert plugin_entries[0].required


def test_audit_missing_project_skill(minimal_manifest):
    """Test audit detects missing required project skill."""
    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        # Mock `claude plugins list` returning the required plugin
        mock_run.return_value = (
            "Installed plugins:\n\n"
            "  ❯ test-plugin@test-source\n"
            "    Status: ✔ enabled\n"
        )
        result = run_audit(minimal_manifest, is_claude=True, verbose=False)

    assert not result.passed
    skill_entries = [e for e in result.entries if e.category == "project_skill"]
    assert len(skill_entries) == 1
    assert not skill_entries[0].available
    assert skill_entries[0].required


def test_audit_template_only_skill_in_template(temp_repo):
    """Test template-only skills are required in template repo."""
    # Create create-project skill to mark this as template
    (temp_repo / ".claude" / "skills" / "create-project").mkdir(parents=True)
    (temp_repo / ".claude" / "skills" / "create-project" / "SKILL.md").write_text("# Test")

    manifest = {
        "project_skills": [
            {"id": "create-project", "required": True, "template_only": True}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    result = run_audit(temp_repo, is_claude=False, verbose=False)
    assert result.passed  # Skill exists, so audit passes


def test_audit_template_only_skill_in_generated_project(temp_repo):
    """Test template-only skills are skipped in generated projects."""
    # No create-project skill = generated project
    manifest = {
        "project_skills": [
            {"id": "create-project", "required": True, "template_only": True}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    result = run_audit(temp_repo, is_claude=False, verbose=False)
    # Should pass because template_only skills are skipped in generated projects
    assert result.passed
    # Should have no entries for the template-only skill
    skill_entries = [e for e in result.entries if e.capability_id == "create-project"]
    assert len(skill_entries) == 0


def test_audit_all_capabilities_present(temp_repo):
    """Test audit passes when all required capabilities are present."""
    # Create project skill
    skill_dir = temp_repo / ".claude" / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Test Skill")

    manifest = {
        "claude_plugins": [
            {"id": "test-plugin@test-source", "required": True}
        ],
        "project_skills": [
            {"id": "test-skill", "required": True}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    # Need to patch the _run function in capability_audit module
    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        # Mock `claude plugins list` returning the required plugin
        mock_run.return_value = (
            "Installed plugins:\n\n"
            "  ❯ test-plugin@test-source\n"
            "    Status: ✔ enabled\n"
        )
        result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert result.passed
    assert len(result.errors) == 0
