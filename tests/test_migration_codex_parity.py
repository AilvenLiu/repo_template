#!/usr/bin/env python3
"""Tests for migration script that upgrades existing repos to Codex parity."""

import subprocess
import tempfile
from pathlib import Path


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

        result = subprocess.run(
            [
                "python3",
                str(template_root / "scripts" / "migrate_codex_parity.py"),
                str(target),
                "--backup",
            ],
            capture_output=True,
            text=True,
        )
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
