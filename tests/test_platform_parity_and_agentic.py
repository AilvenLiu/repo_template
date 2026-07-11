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
    body = _read(".ai/scripts/session_init.py")
    assert '"common/agentic-team"' in body, (
        "session_init.py must include common/agentic-team in its always-on list "
        "so the constraint appears in the session manifest."
    )


def test_agents_files_reference_agentic_team_constraint() -> None:
    for name in ("templates/python/AGENTS.md", "templates/cpp/AGENTS.md"):
        body = _read(name)
        assert "agentic-team.md" in body, f"{name} must reference agentic-team constraint"
        assert "Agentic Team" in body, f"{name} must have an Agentic Team section"


def test_claude_entrypoints_reference_agentic_team() -> None:
    for name in ("templates/python/CLAUDE.md", "templates/cpp/CLAUDE.md"):
        body = _read(name)
        assert "agentic-team.md" in body
        assert "Agent` tool" in body or "`Agent`" in body


def test_agents_entrypoints_reference_agentic_team_with_parallel() -> None:
    """Agents.md (codex-native) entrypoints must mention parallel sub-agents."""
    for name in ("templates/python/AGENTS.md", "templates/cpp/AGENTS.md"):
        body = _read(name)
        assert "agentic-team.md" in body
        assert "parallel" in body.lower()


def _required_prohibitions(body: str, items: list[str]) -> list[str]:
    return [item for item in items if item.lower() not in body.lower()]


def test_agents_python_critical_rules_parity() -> None:
    """templates/python/AGENTS.md must enforce every critical rule (was previously in CODEX_PYTHON.md)."""
    body = _read("templates/python/AGENTS.md")
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
    assert not missing, f"templates/python/AGENTS.md missing parity items: {missing}"


def test_agents_cpp_critical_rules_parity() -> None:
    """templates/cpp/AGENTS.md must enforce every critical rule (was previously in CODEX_CPP.md)."""
    body = _read("templates/cpp/AGENTS.md")
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
        "CMake",
        "CPM",
        "smart pointer",
        "static_cast",
        "CUDA",
        "Werror",
    ]
    missing = _required_prohibitions(body, required)
    assert not missing, f"templates/cpp/AGENTS.md missing parity items: {missing}"


def test_agents_entrypoints_declare_scoped_repository_precedence() -> None:
    for name in (
        "templates/python/AGENTS.md",
        "templates/cpp/AGENTS.md",
        "templates/hybrid/AGENTS.md",
    ):
        body = _read(name)
        assert "Platform and Repository-Local Policy" in body
        assert "does not supersede" in body
        assert "INVARIANTS.md" in body
        assert "ROADMAP.md" in body
        assert "roadmap.yml" in body
        assert "sessions/" in body
        assert "prompt.md" in body


def test_agents_entrypoints_have_procedures_table() -> None:
    """The procedures table replaces the old 'Codex Skill Mappings' table."""
    for name in ("templates/python/AGENTS.md", "templates/cpp/AGENTS.md"):
        body = _read(name)
        assert "Procedures and Wrappers" in body
        assert "| Procedure |" in body
        assert ".ai/bin/agent-init --platform" in body
        assert ".ai/bin/agent-precommit" in body


def test_codex_axis_files_are_gone() -> None:
    """The CODEX*.md files were intentionally removed; agents.md spec replaces them."""
    for name in ("CODEX.md", "CODEX_PYTHON.md", "CODEX_CPP.md"):
        assert not (ROOT / name).exists(), f"{name} should not exist after CODEX axis removal"


def test_roadmap_prompt_template_declares_authority_order() -> None:
    body = _read(".ai/scripts/roadmap/templates/prompt.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"prompt.md template missing token: {token}"
    assert "Repository-Local Precedence" in body
    assert "does not supersede" in body


def test_roadmap_invariants_template_declares_full_authority_order() -> None:
    body = _read(".ai/scripts/roadmap/templates/INVARIANTS.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"INVARIANTS.md template missing token: {token}"


def test_roadmap_roadmap_template_declares_authority_order() -> None:
    body = _read(".ai/scripts/roadmap/templates/ROADMAP.md")
    for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
        assert token in body, f"ROADMAP.md template missing token: {token}"
