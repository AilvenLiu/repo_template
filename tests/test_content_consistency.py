#!/usr/bin/env python3
"""Content consistency checks for constraints and docs."""

from pathlib import Path


def test_python_testing_does_not_recommend_direct_pip_install() -> None:
    content = (
        Path(__file__).parent.parent / ".ai" / "constraints" / "python" / "testing.md"
    ).read_text()
    assert "pip install pytest" not in content


def test_readme_no_missing_codex_integration_doc_reference() -> None:
    readme = (Path(__file__).parent.parent / "README.md").read_text()
    assert "CODEX_INTEGRATION.md" not in readme


def test_template_docs_cover_hybrid_projects() -> None:
    root = Path(__file__).parent.parent
    for rel_path in ["README.md", "AGENTS.md", "CLAUDE.md"]:
        content = (root / rel_path).read_text()
        assert "hybrid" in content.lower(), rel_path


def test_template_docs_do_not_reference_removed_codex_tree() -> None:
    root = Path(__file__).parent.parent
    checked = [
        root / "README.md",
        root / "AGENTS.md",
        root / ".ai" / "README.md",
        root / ".claude" / "skills" / "create-project" / "SKILL.md",
    ]
    for path in checked:
        content = path.read_text()
        assert ".codex/" not in content, str(path)


def test_codex_entrypoint_files_removed() -> None:
    """The CODEX axis was deleted in favour of AGENTS.md as the sole codex entrypoint."""
    root = Path(__file__).parent.parent
    assert not (root / "CODEX_PYTHON.md").exists()
    assert not (root / "CODEX_CPP.md").exists()
    assert not (root / "CODEX.md").exists()


def test_canonical_check_constraints_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".ai" / "skills" / "check-constraints" / "SKILL.md").read_text()
    assert ".ai/bin/agent-check-constraints" in skill


def test_canonical_build_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".ai" / "skills" / "build" / "SKILL.md").read_text()
    assert ".ai/bin/agent-build" in skill


def test_canonical_python_env_skill_uses_wrapper() -> None:
    root = Path(__file__).parent.parent
    skill = (root / ".ai" / "skills" / "python-env-setup" / "SKILL.md").read_text()
    assert ".ai/bin/agent-python-env-setup" in skill


def test_repo_contains_no_removed_legacy_behavior_references() -> None:
    root = Path(__file__).parent.parent
    blocked = (
        "pua",
        "pua-en",
        "tanweai/pua",
        "pua-skills",
    )

    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Skip machine-generated dirs and the tests dir (tests intentionally
        # reference blocked tokens as string literals in their own test code).
        skip_parts = {"__pycache__", ".git", ".pytest_cache", "tests"}
        if any(part in path.parts for part in skip_parts):
            continue
        if path.suffix in {".pyc", ".pyo"}:
            continue

        content = path.read_text(errors="ignore")
        assert not any(token in content for token in blocked), str(path)
