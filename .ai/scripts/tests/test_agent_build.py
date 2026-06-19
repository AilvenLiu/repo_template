"""Tests for .ai/bin/agent-build build system dispatch logic."""

import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


def run_agent_build(
    project_yml_content: str,
    command: str = "setup",
    *,
    extra_files: dict[str, str] | None = None,
    extra_path_scripts: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    """Run .ai/bin/agent-build in a temporary directory with given project.yml content.

    Returns:
        Tuple of (exit_code, stdout, stderr)
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        ai_dir = tmpdir_path / ".ai"
        ai_dir.mkdir()

        (ai_dir / "project.yml").write_text(project_yml_content)

        if extra_files:
            for rel_path, content in extra_files.items():
                target = tmpdir_path / rel_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)

        # Copy entire .ai/bin directory to get all dependencies
        repo_root = Path(__file__).parent.parent.parent.parent
        src_bin_dir = repo_root / ".ai" / "bin"
        dst_bin_dir = tmpdir_path / ".ai" / "bin"
        dst_bin_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_bin_dir, dst_bin_dir)

        env = None
        if extra_path_scripts:
            tool_dir = tmpdir_path / "tool-bin"
            tool_dir.mkdir()
            for name, content in extra_path_scripts.items():
                script = tool_dir / name
                script.write_text(content)
                script.chmod(0o755)
            env = dict(os.environ)
            env["PATH"] = f"{tool_dir}:{env['PATH']}"

        result = subprocess.run(
            [str(dst_bin_dir / "agent-build"), command],
            cwd=tmpdir,
            capture_output=True,
            text=True,
            env=env,
        )

        return result.returncode, result.stdout, result.stderr


class TestBuildSystemDispatch:
    """Test that .ai/bin/agent-build correctly dispatches based on build_system."""

    def test_poetry_build_system(self):
        """Test that build_system: poetry uses poetry branch."""
        project_yml = """
project_profile:
  language: [python]
  build_system: poetry
"""
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "Poetry" in combined or "pyproject.toml" in combined

    def test_cmake_build_system(self):
        """Test that build_system: cmake uses cmake branch."""
        project_yml = """
project_profile:
  language: [cpp]
  build_system: cmake
"""
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "CMake" in combined or "CMakeLists.txt" in combined

    def test_scikit_build_doctor(self):
        """Test that scikit-build projects dispatch to the hybrid branch."""
        project_yml = """
project_profile:
  language: [python, cpp]
  build_system: scikit-build-core
"""
        exit_code, stdout, stderr = run_agent_build(project_yml, command="doctor")

        combined = stdout + stderr
        assert "scikit-build-core Environment" in combined
        assert exit_code == 0

    def test_bazel_doctor(self):
        """Test that build_system: bazel uses the Bazel branch."""
        project_yml = """
project_profile:
  language: [cpp]
  build_system: bazel
"""
        exit_code, stdout, stderr = run_agent_build(
            project_yml,
            command="doctor",
            extra_files={"WORKSPACE": "workspace(name = 'demo')\n"},
            extra_path_scripts={"bazel": "#!/bin/sh\necho 'bazel 7.0.0'\n"},
        )

        combined = stdout + stderr
        assert "bazel 7.0.0" in combined
        assert "Bazel workspace detected." in combined
        assert exit_code == 0

    def test_mixed_stub(self):
        """Test that build_system: mixed shows not-yet-implemented message."""
        project_yml = """
project_profile:
  language: [python, cpp]
  build_system: mixed
"""
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "not yet implemented" in combined.lower()
        assert exit_code != 0


class TestBackwardCompatibility:
    """Test that legacy project_type field still works."""

    def test_legacy_python_maps_to_poetry(self):
        """Test that project_type: python uses poetry branch."""
        project_yml = "project_type: python\n"
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "Poetry" in combined or "pyproject.toml" in combined

    def test_legacy_cpp_maps_to_cmake(self):
        """Test that project_type: cpp uses cmake branch."""
        project_yml = "project_type: cpp\n"
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "CMake" in combined or "CMakeLists.txt" in combined

    def test_profile_takes_precedence_over_legacy(self):
        """Test that project_profile.build_system takes precedence over project_type."""
        project_yml = """
project_type: python
project_profile:
  language: [cpp]
  build_system: cmake
"""
        exit_code, stdout, stderr = run_agent_build(project_yml)

        combined = stdout + stderr
        assert "CMake" in combined or "CMakeLists.txt" in combined
