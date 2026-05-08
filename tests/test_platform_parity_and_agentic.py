#!/usr/bin/env python3
"""Tests guaranteeing dual-platform (Claude/Codex via AGENTS.md) parity and agentic-team wiring.

After the CODEX axis was removed, AGENTS.md is the canonical Codex entrypoint
(per the agents.md spec). These tests assert that AGENTS_*.md carries every
critical rule and procedure mapping that the deleted CODEX_*.md used to carry.
"""

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


def test_agents_entrypoints_reference_agentic_team_with_parallel() -> None:
    """Agents.md (codex-native) entrypoints must mention parallel sub-agents."""
    for name in ("AGENTS_PYTHON.md", "AGENTS_CPP.md"):
        body = _read(name)
        assert "agentic-team.md" in body
        assert "parallel" in body.lower()


def _required_prohibitions(body: str, items: list[str]) -> list[str]:
    return [item for item in items if item.lower() not in body.lower()]


def test_agents_python_critical_rules_parity() -> None:
    """AGENTS_PYTHON.md must enforce every critical rule (was previously in CODEX_PYTHON.md)."""
    body = _read("AGENTS_PYTHON.md")
    required = [
        "master",
        "main",
        "develop",
        "release/*",
        "hotfix/*",
        "pre-commit",
        "secret",
        "bare `except",
        "mutable default",
        "eval()",
        "AI attribution",
        "capability audit",
    ]
    missing = _required_prohibitions(body, required)
    assert not missing, f"AGENTS_PYTHON.md missing parity items: {missing}"


def test_agents_cpp_critical_rules_parity() -> None:
    """AGENTS_CPP.md must enforce every critical rule (was previously in CODEX_CPP.md)."""
    body = _read("AGENTS_CPP.md")
    required = [
        "master",
        "main",
        "develop",
        "release/*",
        "hotfix/*",
        "pre-commit",
        "secret",
        "AI attribution",
        "capability audit",
        "Conan",
        "vcpkg",
        "smart pointer",
        "static_cast",
        "CUDA",
        "Werror",
    ]
    missing = _required_prohibitions(body, required)
    assert not missing, f"AGENTS_CPP.md missing parity items: {missing}"


def test_agents_entrypoints_declare_authority_hierarchy() -> None:
    for name in ("AGENTS_PYTHON.md", "AGENTS_CPP.md"):
        body = _read(name)
        assert "Authority Hierarchy" in body
        assert "INVARIANTS.md" in body
        assert "ROADMAP.md" in body
        assert "roadmap.yml" in body
        assert "sessions/" in body
        assert "prompt.md" in body


def test_agents_entrypoints_have_procedures_table() -> None:
    """The procedures table replaces the old 'Codex Skill Mappings' table."""
    for name in ("AGENTS_PYTHON.md", "AGENTS_CPP.md"):
        body = _read(name)
        assert "Procedures and Wrappers" in body
        assert "| Procedure |" in body
        assert "bin/agent-init --platform" in body
        assert "bin/agent-precommit" in body


def test_codex_axis_files_are_gone() -> None:
    """The CODEX*.md files were intentionally removed; agents.md spec replaces them."""
    for name in ("CODEX.md", "CODEX_PYTHON.md", "CODEX_CPP.md"):
        assert not (ROOT / name).exists(), f"{name} should not exist after CODEX axis removal"


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
