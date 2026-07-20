#!/usr/bin/env python3
"""End-to-end roadmap validation in a mock generated project.

Verifies the full chain:
- create-project produces a working repo
- .agents/bin/agent-init prints agentic-team constraint
- .agents/bin/agent-roadmap create produces complete phase folders with all 4 files
- validate_schema.py enforces structural and authority-order completeness
- Tampering with the phase (e.g. removing ROADMAP.md or stripping the
  authority-order tokens from prompt.md) is detected
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "create-project" / "scripts"))
sys.path.insert(0, str(ROOT / ".agents" / "scripts"))

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


def _run(
    cmd: list[str], cwd: Path, env: dict | None = None
) -> subprocess.CompletedProcess:
    real_env = os.environ.copy()
    real_env.setdefault("AGENT_MCP_HEALTH_TIMEOUT_SEC", "1")
    if env:
        real_env.update(env)
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=real_env)


def _force_audit_pass(project_root: Path) -> None:
    """Simulate a properly-configured workstation so downstream skills can run."""

    for rel in (".agents/session_state.json", ".claude/session_state.json"):
        path = project_root / rel
        if path.exists():
            data = json.loads(path.read_text())
        else:
            data = {
                "initialized": True,
                "timestamp": datetime.now().isoformat(),
                "platform": "claude",
                "loaded_constraints": ["common/agentic-team"],
                "active_roadmap": None,
                "capability_audit": {"passed": True, "entries": []},
            }
        audit = data.get("capability_audit")
        if isinstance(audit, dict):
            audit["passed"] = True
            for entry in audit.get("entries", []):
                if entry.get("required"):
                    entry["available"] = True
        data["capability_audit"] = audit
        path.write_text(json.dumps(data, indent=2))


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    target = tmp_path / "mockproj"
    create_project(ROOT, target, "python")
    _run(["git", "checkout", "-b", "feat/e2e", "-q"], target)
    _force_audit_pass(target)
    return target


def test_init_loads_agentic_team_constraint(project_root: Path) -> None:
    state = json.loads((project_root / ".agents" / "session_state.json").read_text())
    assert state["initialized"] is True
    assert "common/agentic-team" in state["loaded_constraints"]


def test_roadmap_create_produces_complete_phase(project_root: Path) -> None:
    create = _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "demo",
            "--phases",
            "2",
            "--phase-names",
            "baseline",
            "rollout",
        ],
        project_root,
    )
    assert create.returncode == 0, create.stdout + "\n" + create.stderr

    roadmaps = project_root / "agent_roadmaps"
    assert (roadmaps / "README.md").exists()

    for phase in ("phase-0-baseline", "phase-1-rollout"):
        phase_dir = roadmaps / phase
        for required in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"):
            assert (phase_dir / required).exists(), f"{phase}/{required} missing"
        assert (phase_dir / "sessions").is_dir()

    prompt_text = (roadmaps / "phase-0-baseline" / "prompt.md").read_text()
    for token in (
        "INVARIANTS.md",
        "ROADMAP.md",
        "roadmap.yml",
        "sessions",
        "prompt.md",
    ):
        assert token in prompt_text, f"prompt.md missing authority token {token}"
    assert "Repository-Local Precedence" in prompt_text
    assert "does not supersede" in prompt_text


def test_completed_phase_is_not_deleted_while_later_phase_remains(
    project_root: Path,
) -> None:
    create = _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "demo",
            "--phases",
            "2",
            "--phase-names",
            "baseline",
            "rollout",
        ],
        project_root,
    )
    assert create.returncode == 0, create.stdout + "\n" + create.stderr

    for _ in range(3):
        result = _run(
            ["bash", ".agents/bin/agent-roadmap", "update", "complete-task"],
            project_root,
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

    assert (project_root / "agent_roadmaps" / "phase-0-baseline").exists()
    assert (project_root / "agent_roadmaps" / "phase-1-rollout").exists()
    assert (
        "placeholder"
        not in (project_root / "agent_roadmaps" / "README.md").read_text().lower()
    )


def test_roadmap_validate_passes_for_freshly_created_phase(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "demo",
            "--phases",
            "1",
            "--phase-names",
            "baseline",
        ],
        project_root,
    )
    result = _run(
        ["bash", ".agents/bin/agent-roadmap", "validate", "phase-0-baseline"],
        project_root,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def test_roadmap_validate_detects_missing_roadmap_md(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "demo",
            "--phases",
            "1",
            "--phase-names",
            "baseline",
        ],
        project_root,
    )
    target = project_root / "agent_roadmaps" / "phase-0-baseline" / "ROADMAP.md"
    target.unlink()

    result = _run(
        ["bash", ".agents/bin/agent-roadmap", "validate", "phase-0-baseline"],
        project_root,
    )
    assert result.returncode != 0
    assert "ROADMAP.md" in result.stdout
    assert "Missing required phase file" in result.stdout


def test_roadmap_validate_detects_authority_order_strip(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "demo",
            "--phases",
            "1",
            "--phase-names",
            "baseline",
        ],
        project_root,
    )
    prompt_path = project_root / "agent_roadmaps" / "phase-0-baseline" / "prompt.md"
    prompt_path.write_text(
        "You are operating under a roadmap phase. Do work.\n",
        encoding="utf-8",
    )

    result = _run(
        ["bash", ".agents/bin/agent-roadmap", "validate", "phase-0-baseline"],
        project_root,
    )
    assert result.returncode != 0
    assert "Authority Order" in result.stdout
    assert "prompt.md" in result.stdout
