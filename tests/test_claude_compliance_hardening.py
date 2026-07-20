#!/usr/bin/env python3
"""Regression tests for Claude/Codex instruction parity hardening."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / ".agents" / "scripts"))

from constraints_check import check_constraints  # type: ignore[import-not-found]  # noqa: E402
from project_profile import (  # type: ignore[import-not-found]  # noqa: E402
    BuildSystem,
    Language,
    ProjectProfile,
)


ROOT = Path(__file__).parent.parent


def _text(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_root_agents_contains_cross_agent_mandatory_contract() -> None:
    content = _text("AGENTS.md")
    required = [
        "Mandatory Cross-Agent Contract",
        ".agents/project.yml",
        ".agents/capabilities.yml",
        ".agents/constraints/common/",
        ".agents/constraints/hybrid/",
        ".agents/bin/agent-check-constraints",
        "Python packaging must not define or replace the native build graph",
    ]
    for needle in required:
        assert needle in content


def test_root_claude_contains_claude_specific_loading_instructions() -> None:
    content = _text("CLAUDE.md")
    required = [
        "Claude Code MUST NOT edit files until it has completed this read-and-load sequence",
        "Read root `AGENTS.md`",
        "Read `.agents/project.yml`",
        "Read `.agents/capabilities.yml`",
        ".agents/constraints/cpp/",
        ".agents/constraints/hybrid/",
        "bounded constraint manifest",
        "does not supersede",
        "Do not silently bypass hooks",
    ]
    for needle in required:
        assert needle in content


def test_cpp_and_hybrid_templates_enforce_cpp_first_python_does_not() -> None:
    cpp_text = _text("templates/cpp/AGENTS.md") + _text("templates/cpp/CLAUDE.md")
    hybrid_text = _text("templates/hybrid/AGENTS.md") + _text(
        "templates/hybrid/CLAUDE.md"
    )
    python_text = _text("templates/python/AGENTS.md") + _text(
        "templates/python/CLAUDE.md"
    )

    assert "C++ First" in cpp_text
    assert "C++ First" in hybrid_text
    assert "Python is the binding" in hybrid_text
    assert "C++ First" not in python_text


def test_template_project_yml_contains_project_profile_metadata() -> None:
    expectations = {
        "templates/python/project.yml": ["project_type: python", "language: [python]"],
        "templates/cpp/project.yml": ["project_type: cpp", "language: [cpp]"],
        "templates/hybrid/project.yml": [
            "project_type: hybrid",
            "language: [python, cpp]",
            "build_system: scikit-build-core",
        ],
    }
    for rel_path, needles in expectations.items():
        content = _text(rel_path)
        assert "project_profile:" in content
        for needle in needles:
            assert needle in content


def test_hybrid_entrypoints_match_the_generated_profile_schema() -> None:
    expected_profile = [
        "language: [python, cpp]",
        "build_system: scikit-build-core",
        "bindings: pybind11",
        "distribution: pypi-wheel",
        "hardware_targets: [cuda]",
        "external_dependencies: system_cuda",
    ]
    for rel_path in ("templates/hybrid/AGENTS.md", "templates/hybrid/CLAUDE.md"):
        content = _text(rel_path)
        for field in expected_profile:
            assert field in content, f"{rel_path} missing profile field: {field}"
        assert "language: [python, cpp, cuda]" not in content
        assert "external_dependencies:\n    system_cuda: true" not in content


def test_native_build_ownership_detects_setup_py_extension(tmp_path: Path) -> None:
    (tmp_path / "CMakeLists.txt").write_text(
        "cmake_minimum_required(VERSION 3.24)\n",
        encoding="utf-8",
    )
    (tmp_path / "cmake").mkdir()
    (tmp_path / "cmake" / "CPM.cmake").write_text("", encoding="utf-8")
    (tmp_path / "cmake" / "Dependencies.cmake").write_text("", encoding="utf-8")
    (tmp_path / "cmake" / "Options.cmake").write_text("", encoding="utf-8")
    (tmp_path / "3rdparty" / "cpm-cache").mkdir(parents=True)
    (tmp_path / "3rdparty" / "cpm-cache" / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "setup.py").write_text(
        "from setuptools import setup, Extension\n"
        "setup(ext_modules=[Extension('pkg._core', ['src/core.cpp'])])\n",
        encoding="utf-8",
    )

    profile = ProjectProfile(
        language=[Language.PYTHON, Language.CPP],
        build_system=BuildSystem.SCIKIT_BUILD_CORE,
    )
    violations = check_constraints(tmp_path, profile)

    assert any(
        v.category == "Native Build Ownership"
        and "setup.py" in v.message
        and v.severity == "CRITICAL"
        for v in violations
    )
