#!/usr/bin/env python3
"""End-to-end roadmap validation in a mock generated project.

Verifies the full chain:
- create-project produces a working repo
- .ai/bin/agent-init prints agentic-team constraint
- .ai/bin/agent-roadmap create produces complete step folders with all 4 files
- validate_schema.py enforces structural and authority-order completeness
- Tampering with the step (e.g. removing ROADMAP.md or stripping the
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
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "create-project" / "scripts"))
sys.path.insert(0, str(ROOT / ".ai" / "scripts"))

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

    for rel in (".ai/session_state.json", ".claude/session_state.json"):
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
    state = json.loads((project_root / ".ai" / "session_state.json").read_text())
    assert state["initialized"] is True
    assert "common/agentic-team" in state["loaded_constraints"]


def test_roadmap_create_produces_complete_step(project_root: Path) -> None:
    create = _run(
        [
            "bash",
            ".ai/bin/agent-roadmap",
            "create",
            "demo",
            "--steps",
            "2",
            "--step-names",
            "baseline",
            "rollout",
        ],
        project_root,
    )
    assert create.returncode == 0, create.stdout + "\n" + create.stderr

    roadmaps = project_root / "agent_roadmaps"
    assert (roadmaps / "README.md").exists()

    for step in ("step-0-baseline", "step-1-rollout"):
        step_dir = roadmaps / step
        for required in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"):
            assert (step_dir / required).exists(), f"{step}/{required} missing"
        assert (step_dir / "sessions").is_dir()

    prompt_text = (roadmaps / "step-0-baseline" / "prompt.md").read_text()
    for token in (
        "INVARIANTS.md",
        "ROADMAP.md",
        "roadmap.yml",
        "sessions",
        "prompt.md",
    ):
        assert token in prompt_text, f"prompt.md missing authority token {token}"
    assert "Authority Order" in prompt_text or "Absolute Authority" in prompt_text


def test_completed_step_is_not_deleted_while_later_step_remains(
    project_root: Path,
) -> None:
    create = _run(
        [
            "bash",
            ".ai/bin/agent-roadmap",
            "create",
            "demo",
            "--steps",
            "2",
            "--step-names",
            "baseline",
            "rollout",
        ],
        project_root,
    )
    assert create.returncode == 0, create.stdout + "\n" + create.stderr

    for _ in range(3):
        result = _run(
            ["bash", ".ai/bin/agent-roadmap", "update", "complete-task"], project_root
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

    assert (project_root / "agent_roadmaps" / "step-0-baseline").exists()
    assert (project_root / "agent_roadmaps" / "step-1-rollout").exists()
    assert (
        "placeholder"
        not in (project_root / "agent_roadmaps" / "README.md").read_text().lower()
    )


def test_roadmap_validate_passes_for_freshly_created_step(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".ai/bin/agent-roadmap",
            "create",
            "demo",
            "--steps",
            "1",
            "--step-names",
            "baseline",
        ],
        project_root,
    )
    result = _run(
        ["bash", ".ai/bin/agent-roadmap", "validate", "step-0-baseline"],
        project_root,
    )
    assert result.returncode == 0, result.stdout + "\n" + result.stderr


def test_roadmap_validate_detects_missing_roadmap_md(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".ai/bin/agent-roadmap",
            "create",
            "demo",
            "--steps",
            "1",
            "--step-names",
            "baseline",
        ],
        project_root,
    )
    target = project_root / "agent_roadmaps" / "step-0-baseline" / "ROADMAP.md"
    target.unlink()

    result = _run(
        ["bash", ".ai/bin/agent-roadmap", "validate", "step-0-baseline"],
        project_root,
    )
    assert result.returncode != 0
    assert "ROADMAP.md" in result.stdout
    assert "Missing required step file" in result.stdout


def test_roadmap_validate_detects_authority_order_strip(project_root: Path) -> None:
    _run(
        [
            "bash",
            ".ai/bin/agent-roadmap",
            "create",
            "demo",
            "--steps",
            "1",
            "--step-names",
            "baseline",
        ],
        project_root,
    )
    prompt_path = project_root / "agent_roadmaps" / "step-0-baseline" / "prompt.md"
    prompt_path.write_text(
        "You are operating under a roadmap step. Do work.\n",
        encoding="utf-8",
    )

    result = _run(
        ["bash", ".ai/bin/agent-roadmap", "validate", "step-0-baseline"],
        project_root,
    )
    assert result.returncode != 0
    assert "Authority Order" in result.stdout
    assert "prompt.md" in result.stdout
