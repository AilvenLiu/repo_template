#!/usr/bin/env python3
"""Tests for profile-aware constraint checking."""

from __future__ import annotations

from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / ".agents" / "scripts"))

from constraints_check import check_constraints  # type: ignore[import-not-found]  # noqa: E402
from project_profile import (  # type: ignore[import-not-found]  # noqa: E402
    BuildSystem,
    Language,
    ProjectProfile,
)


def test_hybrid_scikit_build_project_does_not_require_poetry_lock() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir)
        (repo / "pyproject.toml").write_text(
            "[build-system]\n"
            'requires = ["scikit-build-core>=0.8.0"]\n'
            'build-backend = "scikit_build_core.build"\n',
            encoding="utf-8",
        )
        (repo / "CMakeLists.txt").write_text(
            "cmake_minimum_required(VERSION 3.24)\n", encoding="utf-8"
        )
        (repo / "cmake").mkdir()
        (repo / "cmake" / "CPM.cmake").write_text("", encoding="utf-8")
        (repo / "cmake" / "Dependencies.cmake").write_text("", encoding="utf-8")
        (repo / "cmake" / "Options.cmake").write_text("", encoding="utf-8")
        (repo / "3rdparty" / "cpm-cache").mkdir(parents=True)
        (repo / "3rdparty" / "cpm-cache" / ".gitkeep").write_text("", encoding="utf-8")

        profile = ProjectProfile(
            language=[Language.PYTHON, Language.CPP],
            build_system=BuildSystem.SCIKIT_BUILD_CORE,
        )

        violations = check_constraints(repo, profile)
        assert not any(
            v.message == "Poetry project missing poetry.lock" for v in violations
        )
