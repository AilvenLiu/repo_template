#!/usr/bin/env python3
"""Tests for shared capability audit runtime (.ai/tools/capability_audit.py)."""

import tempfile
from pathlib import Path

import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "tools"))

import capability_audit
from capability_audit import run_audit


def _write_manifest(repo: Path, data: dict) -> None:
    manifest_path = repo / ".ai" / "capabilities.yml"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest_path, "w") as fh:
        yaml.dump(data, fh)


def _create_common_layout(repo: Path) -> None:
    (repo / ".claude" / "skills").mkdir(parents=True, exist_ok=True)
    (repo / ".codex" / "skills").mkdir(parents=True, exist_ok=True)
    (repo / "bin").mkdir(parents=True, exist_ok=True)


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

        # Make project skill available.
        (repo / ".claude" / "skills" / "init").mkdir(parents=True, exist_ok=True)
        (repo / ".claude" / "skills" / "init" / "SKILL.md").write_text("# init")

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
            "platform_requirements": {
                "codex": {
                    "codex_skills": [{"id": "init", "required": True}],
                }
            },
        }
        _write_manifest(repo, manifest)

        (repo / ".claude" / "skills" / "init").mkdir(parents=True, exist_ok=True)
        (repo / ".claude" / "skills" / "init" / "SKILL.md").write_text("# init")

        (repo / ".codex" / "skills" / "init").mkdir(parents=True, exist_ok=True)
        (repo / ".codex" / "skills" / "init" / "SKILL.md").write_text("# init")

        cmd = repo / "bin" / "agent-init"
        cmd.write_text("#!/bin/sh\nexit 0\n")
        cmd.chmod(0o755)

        result = run_audit(repo, platform="codex")
        assert result.passed


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
                            {"id": "superpowers@claude-plugins-official", "required": True}
                        ],
                        "claude_plugin_skills": [
                            {
                                "id": "superpowers:brainstorming",
                                "required": True,
                                "plugin": "superpowers@claude-plugins-official",
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
            lambda: "superpowers@claude-plugins-official\nStatus: enabled\n",
        )
        monkeypatch.setattr(
            capability_audit,
            "_claude_plugins_list_json",
            lambda: [
                {
                    "id": "superpowers@claude-plugins-official",
                    "enabled": True,
                    "installPath": "/fake/path",
                }
            ],
        )
        monkeypatch.setattr(
            capability_audit,
            "_discover_plugin_skills",
            lambda plugin_id, install_path: ["superpowers:brainstorming"],
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
