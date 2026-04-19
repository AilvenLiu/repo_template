#!/usr/bin/env python3
"""Tests guaranteeing dual-platform (Claude/Codex) parity and agentic-team wiring."""

from pathlib import Path

ROOT = Path(__file__).parent.parent


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_agentic_team_constraint_file_exists() -> None:
    path = ROOT / ".ai" / "constraints" / "common" / "agentic-team.md"
    assert path.exists(), "agentic-team constraint must exist"
    body = path.read_text()
    assert "Agentic Team" in body
    assert "MUST" in body
    assert "Claude Code" in body and "Codex" in body
    assert "MUST NOT" in body or "must not" in body.lower()


def test_session_init_loads_agentic_team_constraint() -> None:
    body = _read(".ai/tools/session_init.py")
    assert '"common/agentic-team"' in body, (
        "session_init.py must include common/agentic-team in its always-on list "
        "so the constraint is printed at session start."
    )


def test_agents_files_reference_agentic_team_constraint() -> None:
    for name in ("AGENTS_PYTHON.md", "AGENTS_CPP.md"):
        body = _read(name)
        assert "agentic-team.md" in body, f"{name} must reference agentic-team constraint"
        assert "Agentic Team" in body, f"{name} must have an Agentic Team section"


def test_claude_entrypoints_reference_agentic_team() -> None:
    for name in ("CLAUDE_PYTHON.md", "CLAUDE_CPP.md"):
        body = _read(name)
        assert "agentic-team.md" in body
        assert "Agent` tool" in body or "`Agent`" in body


def test_codex_entrypoints_reference_agentic_team() -> None:
    for name in ("CODEX_PYTHON.md", "CODEX_CPP.md"):
        body = _read(name)
        assert "agentic-team.md" in body
        assert "parallel" in body.lower()


def _required_prohibitions(body: str, items: list[str]) -> list[str]:
    return [item for item in items if item.lower() not in body.lower()]


def test_codex_python_parity_with_claude_python() -> None:
    body = _read("CODEX_PYTHON.md")
    required = [
        "master",
        "main",
        "develop",
        "release/*",
        "hotfix/*",
        "pre-commit",
        "secrets",
        "bare `except",
        "mutable default",
        "eval()",
        "AI attribution",
        "capability audit",
    ]
    missing = _required_prohibitions(body, required)
    assert not missing, f"CODEX_PYTHON.md missing parity items: {missing}"


def test_codex_cpp_parity_with_claude_cpp() -> None:
    body = _read("CODEX_CPP.md")
    required = [
        "master",
        "main",
        "develop",
        "release/*",
        "hotfix/*",
        "pre-commit",
        "secrets",
        "AI attribution",
        "capability audit",
        "Conan",
        "vcpkg",
        "smart pointers",
        "static_cast",
        "CUDA",
        "Werror",
    ]
    missing = _required_prohibitions(body, required)
    assert not missing, f"CODEX_CPP.md missing parity items: {missing}"


def test_codex_entrypoints_declare_authority_hierarchy() -> None:
    for name in ("CODEX_PYTHON.md", "CODEX_CPP.md"):
        body = _read(name)
        assert "Authority Hierarchy" in body
        assert "INVARIANTS.md" in body
        assert "ROADMAP.md" in body
        assert "roadmap.yml" in body
        assert "sessions/" in body
        assert "prompt.md" in body


def test_codex_entrypoints_have_skill_mapping_table() -> None:
    for name in ("CODEX_PYTHON.md", "CODEX_CPP.md"):
        body = _read(name)
        assert "Codex Skill Mappings" in body
        assert "| Procedure |" in body
        assert "bin/agent-init --platform codex" in body


def test_roadmap_prompt_template_declares_authority_order() -> None:
    body = _read(".claude/skills/roadmap/templates/prompt.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"prompt.md template missing token: {token}"
    assert "Authority Order" in body or "Absolute Authority" in body


def test_roadmap_invariants_template_declares_full_authority_order() -> None:
    body = _read(".claude/skills/roadmap/templates/INVARIANTS.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"INVARIANTS.md template missing token: {token}"


def test_roadmap_roadmap_template_declares_authority_order() -> None:
    body = _read(".claude/skills/roadmap/templates/ROADMAP.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"ROADMAP.md template missing token: {token}"
