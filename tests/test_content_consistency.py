#!/usr/bin/env python3
"""Content consistency checks for constraints and docs."""

from pathlib import Path


def test_python_testing_does_not_recommend_direct_pip_install() -> None:
    content = (Path(__file__).parent.parent / ".ai" / "constraints" / "python" / "testing.md").read_text()
    assert "pip install pytest" not in content


def test_readme_no_missing_codex_integration_doc_reference() -> None:
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "CODEX_INTEGRATION.md" not in readme


def test_codex_entrypoint_files_exist() -> None:
    root = Path(__file__).parent.parent
    assert (root / "CODEX_PYTHON.md").exists()
    assert (root / "CODEX_CPP.md").exists()
    assert (root / "CODEX.md").exists()


def test_codex_check_constraints_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".codex" / "skills" / "check-constraints" / "SKILL.md").read_text()
    assert "bin/agent-check-constraints" in skill
