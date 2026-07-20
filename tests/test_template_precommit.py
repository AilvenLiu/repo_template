#!/usr/bin/env python3
"""Template-only pre-commit environment exception coverage."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "scripts" / "pre-commit"))
sys.path.insert(0, str(ROOT / ".agents" / "scripts"))
sys.path.insert(0, str(ROOT / ".agents" / "scripts" / "common"))

_PREVIOUS_UTILS = sys.modules.pop("utils", None)
from utils import PreCommitManager  # type: ignore[import-not-found]  # noqa: E402

if _PREVIOUS_UTILS is not None:
    sys.modules["utils"] = _PREVIOUS_UTILS
else:
    sys.modules.pop("utils", None)
from validate_constraints import (  # type: ignore[import-not-found]  # noqa: E402
    validate_all_constraints,
)


def _write_python_profile(root: Path) -> None:
    (root / ".agents").mkdir(parents=True)
    (root / ".agents" / "project.yml").write_text(
        "project_profile:\n  language: [python]\n  build_system: poetry\n"
    )


def test_template_infrastructure_needs_no_application_environment(
    tmp_path: Path, monkeypatch
) -> None:
    _write_python_profile(tmp_path)
    (tmp_path / ".agents" / "skills" / "create-project").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "requirements.txt").write_text("")

    manager = PreCommitManager(tmp_path)
    profile = manager.detect_project_profile()
    ok, message = manager.python_environment_status(profile)

    assert ok is True
    assert "Template infrastructure" in message

    monkeypatch.chdir(tmp_path)
    assert validate_all_constraints() == []


def test_generated_python_project_still_requires_managed_environment(
    tmp_path: Path,
) -> None:
    _write_python_profile(tmp_path)
    (tmp_path / "requirements.txt").write_text("")

    manager = PreCommitManager(tmp_path)
    profile = manager.detect_project_profile()
    ok, message = manager.python_environment_status(profile)

    assert ok is False
    assert "No supported Python environment" in message
