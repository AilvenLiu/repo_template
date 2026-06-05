#!/usr/bin/env python3
"""Tests for shared policy gate (.ai/scripts/policy_gate.py)."""

import json
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "scripts"))

import policy_gate


def _write_state(repo: Path, passed: bool = True) -> None:
    state = {
        "initialized": True,
        "capability_audit": {"passed": passed},
    }
    state_path = repo / ".ai" / "session_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state))


def test_mutate_blocked_without_session() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        allowed, _ = policy_gate.gate_mutate(repo, {})
        assert not allowed


def test_bash_preinit_allows_only_init() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)

        allowed, _ = policy_gate.gate_bash(repo, {"command": "bin/agent-init"})
        assert allowed

        allowed, _ = policy_gate.gate_bash(repo, {"command": "bin/agent-init --platform claude"})
        assert allowed

        allowed, _ = policy_gate.gate_bash(repo, {"command": "ls -la"})
        assert not allowed


def test_commit_blocked_on_protected_branch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_state(repo, passed=True)

        allowed, message = policy_gate.gate_commit(
            repo,
            {"branch": "main", "message": "feat(core): add command"},
        )
        assert not allowed
        assert "protected branch" in message.lower()


def test_commit_blocks_ai_attribution() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_state(repo, passed=True)

        allowed, message = policy_gate.gate_commit(
            repo,
            {"branch": "feat/demo", "message": "feat(x): update\n\nCo-Authored-By: Bot"},
        )
        assert not allowed
        assert "attribution" in message.lower()


def test_dependency_blocks_direct_pip_for_python_repo() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        _write_state(repo, passed=True)

        (repo / ".ai").mkdir(exist_ok=True)
        (repo / ".ai" / "project.yml").write_text("project_type: python\n")

        allowed, _ = policy_gate.gate_dependency(repo, {"command": "pip install requests"})
        assert not allowed


# ---------------------------------------------------------------------------
# Extended Python pattern tests (venv paths + version-suffixed interpreters)
# ---------------------------------------------------------------------------

def _python_repo(tmp: str) -> Path:
    repo = Path(tmp)
    _write_state(repo, passed=True)
    (repo / ".ai").mkdir(exist_ok=True)
    (repo / ".ai" / "project.yml").write_text("project_type: python\n")
    return repo


def test_bash_blocks_venv_pip_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": ".venv/bin/pip install requests"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_venv_pip3_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": ".venv/bin/pip3 install requests"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_versioned_pip_install() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": "pip3.10 install requests"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_venv_python_direct() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": ".venv/bin/python script.py"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_venv_python3_direct() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": ".venv/bin/python3 script.py"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_versioned_python_direct() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(repo, {"command": "python3.10 script.py"})
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_blocks_versioned_python_m_pip() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, msg = policy_gate.gate_bash(
            repo, {"command": "python3.10 -m pip install requests"}
        )
        assert not allowed
        assert "BLOCKED" in msg


def test_bash_allows_poetry_run_python() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, _ = policy_gate.gate_bash(
            repo, {"command": "poetry run python script.py"}
        )
        assert allowed


def test_bash_allows_python_version_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        for cmd in ("python3 --version", "python3.10 --version", "python3.10 -V"):
            allowed, _ = policy_gate.gate_bash(repo, {"command": cmd})
            assert allowed, f"version check should be allowed: {cmd}"


def test_bash_allows_ai_script_python() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = _python_repo(tmp)
        allowed, _ = policy_gate.gate_bash(
            repo, {"command": "python3 .ai/scripts/session_init.py --platform codex"}
        )
        assert allowed
