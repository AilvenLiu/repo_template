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


def test_audit_plugin_skill_discovery_with_json(temp_repo):
    """Test plugin-skill discovery using JSON metadata."""
    manifest = {
        "claude_plugins": [
            {"id": "superpowers@claude-plugins-official", "required": True}
        ],
        "claude_plugin_skills": [
            {
                "id": "superpowers:brainstorming",
                "plugin": "superpowers@claude-plugins-official",
                "required": True,
            }
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_claude_plugins_list_json") as mock_json:
        # Mock JSON response with install path
        mock_json.return_value = [
            {
                "id": "superpowers@claude-plugins-official",
                "enabled": True,
                "installPath": "/fake/path/superpowers/5.0.2",
            }
        ]

        # Mock filesystem scan to find the skill
        with patch.object(capability_audit, "_discover_plugin_skills") as mock_discover:
            mock_discover.return_value = ["superpowers:brainstorming", "superpowers:other-skill"]
            result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert result.passed
    plugin_skill_entries = [e for e in result.entries if e.category == "claude_plugin_skill"]
    assert len(plugin_skill_entries) == 1
    assert plugin_skill_entries[0].available
    assert "filesystem scan" in plugin_skill_entries[0].method


def test_audit_plugin_skill_missing_from_plugin(temp_repo):
    """Test detection when plugin is installed but skill is not provided."""
    manifest = {
        "claude_plugins": [
            {"id": "superpowers@claude-plugins-official", "required": True}
        ],
        "claude_plugin_skills": [
            {
                "id": "superpowers:nonexistent-skill",
                "plugin": "superpowers@claude-plugins-official",
                "required": True,
            }
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_claude_plugins_list_json") as mock_json:
        mock_json.return_value = [
            {
                "id": "superpowers@claude-plugins-official",
                "enabled": True,
                "installPath": "/fake/path/superpowers/5.0.2",
            }
        ]

        with patch.object(capability_audit, "_discover_plugin_skills") as mock_discover:
            # Plugin exists but doesn't provide the requested skill
            mock_discover.return_value = ["superpowers:brainstorming", "superpowers:other-skill"]
            result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert not result.passed
    plugin_skill_entries = [e for e in result.entries if e.category == "claude_plugin_skill"]
    assert len(plugin_skill_entries) == 1
    assert not plugin_skill_entries[0].available
    assert "not provided by plugin" in plugin_skill_entries[0].message


def test_generated_project_has_capabilities_manifest():
    """Test that create-project generator copies capabilities.yml to generated projects."""
    # This test verifies the template generator includes capabilities.yml
    # We check the generator's _COPY_DIRS includes .ai/ directory
    generator_path = Path(__file__).parent.parent / ".claude" / "skills" / "create-project" / "scripts" / "init.py"

    if not generator_path.exists():
        pytest.skip("create-project skill not found (template-only)")

    generator_code = generator_path.read_text()

    # Verify that .ai/ is in the copy list
    assert '".ai"' in generator_code or "'.ai'" in generator_code, \
        "Generator must copy .ai/ directory to include capabilities.yml"


def test_generated_project_audit_excludes_template_only_skills():
    """Test that generated projects skip template_only skills during audit."""
    # Create a mock generated project (no create-project skill)
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        (repo / ".ai").mkdir()
        (repo / ".claude" / "skills").mkdir(parents=True)

        # Create manifest with template_only skill
        manifest = {
            "project_skills": [
                {"id": "init", "required": True},
                {"id": "create-project", "required": True, "template_only": True},
            ],
        }
        manifest_path = repo / ".ai" / "capabilities.yml"
        with open(manifest_path, "w") as f:
            yaml.dump(manifest, f)

        # Create init skill (but NOT create-project)
        init_dir = repo / ".claude" / "skills" / "init"
        init_dir.mkdir(parents=True)
        (init_dir / "SKILL.md").write_text("# Init Skill")

        # Run audit
        result = run_audit(repo, is_claude=False, verbose=False)

        # Should pass because template_only skills are skipped in generated projects
        # and init skill exists
        assert result.passed

        # Verify create-project was skipped
        create_project_entries = [e for e in result.entries if e.capability_id == "create-project"]
        assert len(create_project_entries) == 0


def test_audit_context7_plugin_backed_mcp(temp_repo):
    """Test Context7 audit with plugin-backed MCP (primary method)."""
    manifest = {
        "integrations": [
            {"id": "context7-mcp", "required": True, "check": "mcp"}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        def mock_command(cmd):
            if "plugins list" in " ".join(cmd):
                return (
                    "Installed plugins:\n\n"
                    "  ❯ context7@claude-plugins-official\n"
                    "    Status: ✔ enabled\n"
                )
            elif "mcp list" in " ".join(cmd):
                return "plugin:context7:context7: npx -y @upstash/context7-mcp - ✓ Connected\n"
            return ""

        mock_run.side_effect = mock_command
        result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert result.passed
    integration_entries = [e for e in result.entries if e.category == "integration"]
    assert len(integration_entries) == 1
    assert integration_entries[0].available
    assert "plugin-backed MCP" in integration_entries[0].method


def test_audit_context7_manual_mcp_server(temp_repo):
    """Test Context7 audit with manual MCP server (fallback method)."""
    manifest = {
        "integrations": [
            {"id": "context7-mcp", "required": True, "check": "mcp"}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        def mock_command(cmd):
            if "plugins list" in " ".join(cmd):
                # Plugin not installed
                return "Installed plugins:\n\n(none)\n"
            elif "mcp list" in " ".join(cmd):
                # But manual MCP server is configured
                return "context7: http://mcp.context7.com/mcp - ✓ Connected\n"
            return ""

        mock_run.side_effect = mock_command
        result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert result.passed
    integration_entries = [e for e in result.entries if e.category == "integration"]
    assert len(integration_entries) == 1
    assert integration_entries[0].available
    assert "manual MCP server" in integration_entries[0].method


def test_audit_context7_plugin_not_enabled(temp_repo):
    """Test Context7 audit fails when plugin is installed but not enabled."""
    manifest = {
        "integrations": [
            {"id": "context7-mcp", "required": True, "check": "mcp"}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        def mock_command(cmd):
            if "plugins list" in " ".join(cmd):
                return (
                    "Installed plugins:\n\n"
                    "  ❯ context7@claude-plugins-official\n"
                    "    Status: ✘ disabled\n"
                )
            elif "mcp list" in " ".join(cmd):
                return ""
            return ""

        mock_run.side_effect = mock_command
        result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert not result.passed
    integration_entries = [e for e in result.entries if e.category == "integration"]
    assert len(integration_entries) == 1
    assert not integration_entries[0].available
    assert "not enabled" in integration_entries[0].message.lower()


def test_audit_context7_missing(temp_repo):
    """Test Context7 audit fails when neither plugin nor manual MCP is configured."""
    manifest = {
        "integrations": [
            {"id": "context7-mcp", "required": True, "check": "mcp"}
        ],
    }
    manifest_path = temp_repo / ".ai" / "capabilities.yml"
    with open(manifest_path, "w") as f:
        yaml.dump(manifest, f)

    import capability_audit
    with patch.object(capability_audit, "_run") as mock_run:
        def mock_command(cmd):
            if "plugins list" in " ".join(cmd):
                return "Installed plugins:\n\n(none)\n"
            elif "mcp list" in " ".join(cmd):
                return ""
            return ""

        mock_run.side_effect = mock_command
        result = run_audit(temp_repo, is_claude=True, verbose=False)

    assert not result.passed
    integration_entries = [e for e in result.entries if e.category == "integration"]
    assert len(integration_entries) == 1
    assert not integration_entries[0].available
    assert "not installed" in integration_entries[0].message.lower()
