#!/usr/bin/env python3
"""Portable Poetry package-source policy tests."""

from __future__ import annotations

import sys
from pathlib import Path

from pytest import MonkeyPatch

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "scripts" / "python-env-setup"))

from diagnose import (  # type: ignore[import-not-found]  # noqa: E402
    EnvironmentDiagnostics,
    Issue,
    parent_virtual_env,
)


def test_hybrid_scikit_build_still_requires_poetry_toml(tmp_path: Path) -> None:
    (tmp_path / ".agents").mkdir()
    (tmp_path / ".agents" / "project.yml").write_text(
        "project_profile:\n  language: [python, cpp]\n  build_system: scikit-build-core\n"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[build-system]\nbuild-backend = "scikit_build_core.build"\n'
    )
    diagnostics = EnvironmentDiagnostics(tmp_path)
    diagnostics.check_poetry_toml_in_project()
    assert any(issue.severity == Issue.CRITICAL for issue in diagnostics.issues)


def source_issues(tmp_path: Path, source_block: str = "") -> list[Issue]:
    (tmp_path / "pyproject.toml").write_text(
        '[tool.poetry]\nname = "example"\nversion = "0.1.0"\n' + source_block
    )
    diagnostics = EnvironmentDiagnostics(tmp_path)
    diagnostics.check_package_sources()
    return diagnostics.issues


def test_default_pypi_needs_no_forced_regional_mirror(tmp_path: Path) -> None:
    issues = source_issues(tmp_path)
    assert not any(issue.severity == Issue.CRITICAL for issue in issues)
    assert "default PyPI" in issues[0].message


def test_custom_source_requires_https_and_priority(tmp_path: Path) -> None:
    issues = source_issues(
        tmp_path,
        '\n[[tool.poetry.source]]\nname = "unsafe"\nurl = "http://index.example/"\n',
    )
    assert any(issue.severity == Issue.CRITICAL for issue in issues)
    assert any("HTTPS" in issue.message for issue in issues)


def test_custom_source_rejects_embedded_credentials(tmp_path: Path) -> None:
    issues = source_issues(
        tmp_path,
        '\n[[tool.poetry.source]]\nname = "unsafe"\n'
        'url = "https://user:token@index.example/simple/"\n'
        'priority = "explicit"\n',
    )
    assert any("embeds credentials" in issue.message for issue in issues)


def test_reviewed_custom_source_passes(tmp_path: Path) -> None:
    issues = source_issues(
        tmp_path,
        '\n[[tool.poetry.source]]\nname = "internal"\n'
        'url = "https://index.example/simple/"\n'
        'priority = "supplemental"\n',
    )
    assert not any(issue.severity == Issue.CRITICAL for issue in issues)


def test_parent_virtual_env_ignores_poetry_child_environment(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")
    monkeypatch.setenv("AGENT_PARENT_VIRTUAL_ENV_SET", "0")

    assert parent_virtual_env() is None

    diagnostics = EnvironmentDiagnostics()
    diagnostics.check_virtual_env_variable()

    assert diagnostics.issues[0].severity == Issue.OK
