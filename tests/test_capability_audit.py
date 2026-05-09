#!/usr/bin/env python3
"""Tests for shared capability audit runtime (.ai/scripts/capability_audit.py)."""

import tempfile
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))

import capability_audit
from capability_audit import run_audit


def _write_manifest(repo: Path, data: dict) -> None:
    manifest_path = repo / ".ai" / "capabilities.yml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as fh:
        yaml.dump(data, fh)


def _create_common_layout(repo: Path) -> None:
    (repo / ".ai" / "skills").mkdir(parents=True, exist_ok=True)
    (repo / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    (repo / "bin").mkdir(parents=True, exist_ok=True)


def _create_skill(repo: Path, skill_id: str, *, with_claude_stub: bool = True) -> None:
    """Create the .ai/skills/<id>/SKILL.md body and (optionally) the Claude stub."""
    (repo / ".ai" / "skills" / skill_id).mkdir(parents=True, exist_ok=True)
    (repo / ".ai" / "skills" / skill_id / "SKILL.md").write_text(f"# {skill_id}")
    if with_claude_stub:
        (repo / ".claude" / "skills" / skill_id).mkdir(parents=True, exist_ok=True)
        (repo / ".claude" / "skills" / skill_id / "SKILL.md").write_text(f"# {skill_id}")


def test_missing_manifest_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        result = run_audit(repo, platform="codex")
        assert not result.passed
        assert any("manifest" in err.lower() for err in result.errors)


def test_v1_manifest_backward_compatibility() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        # Legacy v1 shape.
        _write_manifest(
            repo,
            {
                "project_skills": [{"id": "init", "required": True}],
                "claude_plugins": [{"id": "dummy@source", "required": True}],
            },
        )

        # Make project skill available (both .ai body and Claude stub).
        _create_skill(repo, "init")

        # Claude plugin check will fail because CLI isn't available, but loader should parse.
        result = run_audit(repo, platform="claude")
        assert result is not None
        assert any(e.category == "project_skill" for e in result.entries)


def test_codex_audit_passes_with_required_skills_and_commands() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        manifest = {
            "common_requirements": {
                "project_skills": [{"id": "init", "required": True}],
                "repo_commands": [
                    {
                        "id": "agent-init",
                        "path": "bin/agent-init",
                        "required": True,
                        "executable": True,
                    }
                ],
            },
            "platform_requirements": {"codex": {"integrations": []}},
        }
        _write_manifest(repo, manifest)

        # Codex audit only requires the .ai/skills body (no Claude stub needed).
        _create_skill(repo, "init", with_claude_stub=False)

        cmd = repo / "bin" / "agent-init"
        cmd.write_text("#!/bin/sh\nexit 0\n")
        cmd.chmod(0o755)

        result = run_audit(repo, platform="codex")
        assert result.passed, [e.to_dict() for e in result.entries if not e.available]


def test_codex_audit_fails_when_command_missing() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "common_requirements": {
                    "repo_commands": [
                        {
                            "id": "agent-precommit",
                            "path": "bin/agent-precommit",
                            "required": True,
                            "executable": True,
                        }
                    ]
                },
                "platform_requirements": {"codex": {}},
            },
        )

        result = run_audit(repo, platform="codex")
        assert not result.passed
        assert any(e.category == "repo_command" and not e.available for e in result.entries)


def test_claude_plugin_skill_discovery(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "platform_requirements": {
                    "claude": {
                        "claude_plugins": [
                            {"id": "example-plugin@example-marketplace", "required": True}
                        ],
                        "claude_plugin_skills": [
                            {
                                "id": "example-plugin:brainstorming",
                                "required": True,
                                "plugin": "example-plugin@example-marketplace",
                            }
                        ],
                    }
                }
            },
        )

        # Mock plugin inventory and discovered skills.
        monkeypatch.setattr(
            capability_audit,
            "_claude_plugins_list",
            lambda: "example-plugin@example-marketplace\nStatus: enabled\n",
        )
        monkeypatch.setattr(
            capability_audit,
            "_claude_plugins_list_json",
            lambda: [
                {
                    "id": "example-plugin@example-marketplace",
                    "enabled": True,
                    "installPath": "/fake/path",
                }
            ],
        )
        monkeypatch.setattr(
            capability_audit,
            "_discover_plugin_skills",
            lambda plugin_id, install_path: ["example-plugin:brainstorming"],
        )

        result = run_audit(repo, platform="claude")
        assert result.passed


def test_context7_mcp_check_for_claude(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "platform_requirements": {
                    "claude": {
                        "integrations": [{"id": "context7-mcp", "required": True, "check": "mcp"}]
                    }
                }
            },
        )

        monkeypatch.setattr(
            capability_audit,
            "_claude_mcp_list",
            lambda: "plugin:context7:context7: connected",
        )

        result = run_audit(repo, platform="claude")
        assert result.passed


def test_context7_mcp_fallback_passes_when_health_probe_unavailable(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "platform_requirements": {
                    "claude": {
                        "integrations": [{"id": "context7-mcp", "required": True, "check": "mcp"}]
                    }
                }
            },
        )

        monkeypatch.setattr(capability_audit, "_claude_mcp_list", lambda: None)
        monkeypatch.setattr(
            capability_audit,
            "_claude_plugins_list_json",
            lambda: [
                {
                    "id": "context7@claude-plugins-official",
                    "enabled": True,
                    "mcpServers": {"context7": {"command": "npx", "args": ["-y", "@upstash/context7-mcp"]}},
                }
            ],
        )

        result = run_audit(repo, platform="claude")
        assert result.passed
        integration = next(e for e in result.entries if e.category == "integration")
        assert integration.available
        assert "fallback" in integration.method.lower()


def test_context7_mcp_fails_when_probe_and_plugin_fallback_both_fail(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "platform_requirements": {
                    "claude": {
                        "integrations": [{"id": "context7-mcp", "required": True, "check": "mcp"}]
                    }
                }
            },
        )

        monkeypatch.setattr(capability_audit, "_claude_mcp_list", lambda: None)
        monkeypatch.setattr(capability_audit, "_claude_plugins_list_json", lambda: None)

        result = run_audit(repo, platform="claude")
        assert not result.passed
        integration = next(e for e in result.entries if e.category == "integration")
        assert not integration.available


def test_codex_repo_commands_are_deduplicated_between_common_and_platform() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)

        _write_manifest(
            repo,
            {
                "common_requirements": {
                    "repo_commands": [
                        {
                            "id": "agent-init",
                            "path": "bin/agent-init",
                            "required": True,
                            "executable": True,
                        }
                    ]
                },
                "platform_requirements": {
                    "codex": {
                        "repo_commands": [
                            {
                                "id": "agent-init",
                                "path": "bin/agent-init",
                                "required": True,
                                "executable": True,
                            }
                        ]
                    }
                },
            },
        )

        cmd = repo / "bin" / "agent-init"
        cmd.write_text("#!/bin/sh\nexit 0\n")
        cmd.chmod(0o755)

        result = run_audit(repo, platform="codex")
        entries = [
            e for e in result.entries if e.category == "repo_command" and e.capability_id == "agent-init"
        ]
        assert len(entries) == 1


def test_project_skills_can_be_filtered_by_project_type() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _create_common_layout(repo)
        (repo / ".ai").mkdir(parents=True, exist_ok=True)
        (repo / ".ai" / "project.yml").write_text("project_type: cpp\n")

        _write_manifest(
            repo,
            {
                "common_requirements": {
                    "project_skills": [
                        {"id": "shared-skill", "required": True},
                        {
                            "id": "python-only-skill",
                            "required": True,
                            "project_types": ["python"],
                        },
                    ]
                },
                "platform_requirements": {"codex": {}},
            },
        )

        _create_skill(repo, "shared-skill", with_claude_stub=False)

        result = run_audit(repo, platform="codex")

        ids = [e.capability_id for e in result.entries if e.category == "project_skill"]
        assert "shared-skill" in ids
        assert "python-only-skill" not in ids
        assert result.passed
