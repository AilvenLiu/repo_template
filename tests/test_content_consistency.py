#!/usr/bin/env python3
"""Content consistency checks for constraints and docs."""

from pathlib import Path


def test_python_testing_does_not_recommend_direct_pip_install() -> None:
    content = (Path(__file__).parent.parent / ".ai" / "constraints" / "python" / "testing.md").read_text()
    assert "pip install pytest" not in content


def test_readme_no_missing_codex_integration_doc_reference() -> None:
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "CODEX_INTEGRATION.md" not in readme


def test_codex_entrypoint_files_removed() -> None:
    """The CODEX axis was deleted in favour of AGENTS.md as the sole codex entrypoint."""
    root = Path(__file__).parent.parent
    assert not (root / "CODEX_PYTHON.md").exists()
    assert not (root / "CODEX_CPP.md").exists()
    assert not (root / "CODEX.md").exists()


def test_codex_check_constraints_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".codex" / "skills" / "check-constraints" / "SKILL.md").read_text()
    assert "bin/agent-check-constraints" in skill


def test_codex_build_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".codex" / "skills" / "build" / "SKILL.md").read_text()
    assert "bin/agent-build" in skill


def test_codex_python_env_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".codex" / "skills" / "python-env-setup" / "SKILL.md").read_text()
    assert "bin/agent-python-env-setup" in skill


def test_repo_contains_no_removed_legacy_behavior_references() -> None:
    root = Path(__file__).parent.parent
    blocked = (
        "p" "ua",
        "p" "ua-en",
        "tanweai/" "p" "ua",
        "p" "ua-skills",
    )

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or ".git" in path.parts:
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue

        content = path.read_text(errors="ignore")
        assert not any(token in content for token in blocked), str(path)
