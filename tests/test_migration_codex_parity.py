#!/usr/bin/env python3
"""Tests for migration script that upgrades existing repos to Codex parity."""

import subprocess
import tempfile
from pathlib import Path


def _migrate(target: Path, template_root: Path, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    args = [
        "python3",
        str(template_root / "scripts" / "migrate_codex_parity.py"),
        str(target),
    ]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True)


def test_migration_script_upgrades_legacy_repo() -> None:
    template_root = Path(__file__).parent.parent

    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "legacy_repo"
        target.mkdir(parents=True, exist_ok=True)

        (target / ".ai").mkdir(exist_ok=True)
        (target / ".ai" / "project.yml").write_text("project_type: python\n")
        (target / ".ai" / "capabilities.yml").write_text(
            "project_skills:\n  - id: init\n    required: true\n"
        )

        result = _migrate(target, template_root, ["--backup"])
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

        assert (target / ".ai" / "tools" / "session_init.py").exists()
        assert (target / ".ai" / "constraints" / "common" / "karpathy-guidelines.md").exists()
        assert (target / ".claude" / "settings.json").exists()
        assert (target / ".claude" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
        assert (target / ".codex" / "skills" / "init" / "SKILL.md").exists()
        assert (target / ".codex" / "skills" / "karpathy-guidelines" / "SKILL.md").exists()
        assert (target / "bin" / "agent-init").exists()
        assert (target / ".claude" / "skills" / "pre-commit" / "scripts" / "validate.py").exists()
        assert (target / "CODEX.md").exists()
        assert (target / ".ai" / "capabilities.yml.bak").exists()
        assert not any(target.rglob("__pycache__"))
        assert not any(target.rglob("*.pyc"))


def test_migration_propagates_agentic_team_constraint() -> None:
    """A legacy repo upgraded via the migration script must pick up the new
    agentic-team constraint + the updated session_init.py that loads it."""

    template_root = Path(__file__).parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "legacy_repo"
        target.mkdir()
        (target / ".ai").mkdir()
        (target / ".ai" / "project.yml").write_text("project_type: python\n")
        (target / ".ai" / "capabilities.yml").write_text(
            "project_skills:\n  - id: init\n    required: true\n"
        )

        result = _migrate(target, template_root)
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

        agentic = target / ".ai" / "constraints" / "common" / "agentic-team.md"
        assert agentic.exists(), "agentic-team constraint not propagated by migration"
        body = agentic.read_text()
        assert "Agentic Team" in body and "MUST" in body

        init_py = target / ".ai" / "tools" / "session_init.py"
        assert init_py.exists()
        assert '"common/agentic-team"' in init_py.read_text(), (
            "Upgraded session_init.py must load the new agentic-team constraint"
        )


def test_migration_propagates_roadmap_template_updates() -> None:
    """Migration must propagate the reinforced roadmap templates so legacy
    repos inherit the authority-order declarations automatically."""

    template_root = Path(__file__).parent.parent
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "legacy_repo"
        target.mkdir()
        (target / ".ai").mkdir()
        (target / ".ai" / "project.yml").write_text("project_type: python\n")
        (target / ".ai" / "capabilities.yml").write_text(
            "project_skills:\n  - id: init\n    required: true\n"
        )

        result = _migrate(target, template_root)
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

        templates = target / ".claude" / "skills" / "roadmap" / "templates"
        for name in ("prompt.md", "INVARIANTS.md", "ROADMAP.md"):
            body = (templates / name).read_text()
            for token in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"):
                assert token in body, f"{name} missing authority token {token} after migration"
