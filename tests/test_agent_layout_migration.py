#!/usr/bin/env python3
"""Regression coverage for the canonical .agents architecture."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).parent.parent
sys.path.insert(
    0,
    str(ROOT / ".agents" / "skills" / "create-project" / "scripts"),
)

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


def _run_codex_hook(
    repo: Path,
    tool_name: str,
    tool_input: dict[str, str],
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(repo / ".codex" / "hooks" / "pre_tool_use.py")],
        cwd=repo,
        input=json.dumps({"tool_name": tool_name, "tool_input": tool_input}),
        capture_output=True,
        text=True,
    )


def test_template_uses_agents_as_the_only_canonical_hidden_tree() -> None:
    assert not (ROOT / ".ai").exists()
    assert (ROOT / ".agents" / "skills").is_dir()
    assert (ROOT / ".agents" / "constraints").is_dir()
    assert (ROOT / ".agents" / "scripts").is_dir()
    assert (ROOT / ".agents" / "hooks").is_dir()
    assert not (ROOT / ".codex" / "skills").exists()


def test_every_canonical_skill_has_metadata_and_a_claude_delegate() -> None:
    for skill_dir in sorted((ROOT / ".agents" / "skills").iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_id = skill_dir.name
        assert (skill_dir / "SKILL.md").is_file()

        metadata_path = skill_dir / "agents" / "openai.yaml"
        metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        interface = metadata["interface"]
        assert 25 <= len(interface["short_description"]) <= 64
        assert f"${skill_id}" in interface["default_prompt"]

        delegate = ROOT / ".claude" / "skills" / skill_id / "SKILL.md"
        assert delegate.is_file()
        assert f".agents/skills/{skill_id}/SKILL.md" in delegate.read_text(
            encoding="utf-8"
        )


def test_platform_directories_contain_registration_adapters() -> None:
    assert json.loads((ROOT / ".codex" / "hooks.json").read_text())["hooks"][
        "PreToolUse"
    ]
    assert (ROOT / ".codex" / "hooks" / "pre_tool_use.py").is_file()
    assert (ROOT / ".claude" / "hooks" / "pre_tool_use.sh").is_file()

    for skill_dir in (ROOT / ".claude" / "skills").iterdir():
        if skill_dir.is_dir():
            assert {path.name for path in skill_dir.iterdir()} == {"SKILL.md"}


def test_codex_hook_fails_closed_before_init_and_uses_shared_policy(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    create_project(ROOT, project, "python")

    denied = _run_codex_hook(project, "Bash", {"command": "git status"})
    assert denied.returncode == 2
    assert "Session not initialized" in denied.stderr

    init_allowed = _run_codex_hook(
        project,
        "Bash",
        {"command": ".agents/bin/agent-init --platform codex"},
    )
    assert init_allowed.returncode == 0

    write_denied = _run_codex_hook(
        project,
        "apply_patch",
        {"command": "*** Begin Patch\n*** End Patch"},
    )
    assert write_denied.returncode == 2
    assert "Session not initialized" in write_denied.stderr

    initialized = subprocess.run(
        ["bash", ".agents/bin/agent-init", "--platform", "codex"],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr

    allowed = _run_codex_hook(project, "Bash", {"command": "git status"})
    assert allowed.returncode == 0

    policy_denied = _run_codex_hook(
        project,
        "Bash",
        {"command": "python3 application.py"},
    )
    assert policy_denied.returncode == 2
    assert "poetry run" in policy_denied.stderr
