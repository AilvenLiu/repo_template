#!/usr/bin/env python3
"""Tests for constraint selection in session init."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / ".ai" / "tools"))

from project_type import ProjectType
from session_init import resolve_constraints


def test_python_docs_and_tests_constraints_load_precisely() -> None:
    keys = resolve_constraints(
        ProjectType.PYTHON,
        ["README.md", "tests/test_api.py", "src/app.py"],
        has_roadmap=False,
    )

    assert "python/testing" in keys
    assert "python/documentation" in keys
    assert "python/formatting" in keys
    assert "python/type-checking" in keys


def test_cpp_docs_and_cmake_constraints_load_precisely() -> None:
    keys = resolve_constraints(
        ProjectType.CPP,
        ["docs/design.md", "cmake/toolchains/linux.cmake", "src/kernel.cu"],
        has_roadmap=False,
    )

    assert "cpp/documentation" in keys
    assert "cpp/cmake" in keys
    assert "cpp/cuda" in keys
