#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".agents" / "scripts" / "pre-commit"),
)
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".agents" / "scripts"),
)
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".agents" / "scripts" / "common"),
)

from utils import PreCommitManager  # type: ignore[import-not-found]
from validate_constraints import check_python_dependency_constraints  # type: ignore[import-not-found]


def test_find_python_files_excludes_agent_infrastructure_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("print('ok')\n")
        (root / ".claude" / "skills").mkdir(parents=True)
        (root / ".claude" / "skills" / "tool.py").write_text("print('agent')\n")
        (root / ".agents" / "scripts").mkdir(parents=True)
        (root / ".agents" / "scripts" / "gate.py").write_text("print('agent')\n")

        manager = PreCommitManager(root)
        files = [str(path.relative_to(root)) for path in manager.find_python_files()]

        assert "src/app.py" in files
        assert ".claude/skills/tool.py" not in files
        assert ".agents/scripts/gate.py" not in files


def test_find_mypy_targets_falls_back_to_python_files_outside_git() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "src" / "pkg.py").write_text("x = 1\n")
        (root / "tests" / "test_pkg.py").write_text("def test_x():\n    assert True\n")

        manager = PreCommitManager(root)
        assert manager.find_mypy_targets() == ["src/pkg.py", "tests/test_pkg.py"]


def test_describe_project_type_reports_hybrid() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".agents").mkdir()
        (root / ".agents" / "project.yml").write_text(
            "project_profile:\n"
            "  language: [python, cpp]\n"
            "  build_system: scikit-build-core\n"
            "  distribution: pypi-wheel\n"
            "  hardware_targets: [cuda]\n"
            "  external_dependencies: system_cuda\n"
        )

        manager = PreCommitManager(root)
        assert manager.describe_project_type() == "hybrid"


def test_scikit_build_python_environment_and_manifest_are_accepted() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".agents").mkdir()
        (root / ".agents" / "project.yml").write_text(
            "project_profile:\n"
            "  language: [python, cpp]\n"
            "  build_system: scikit-build-core\n"
        )
        (root / "pyproject.toml").write_text(
            "[build-system]\n"
            'requires = ["scikit-build-core>=0.8.0"]\n'
            'build-backend = "scikit_build_core.build"\n'
        )

        manager = PreCommitManager(root)
        profile = manager.detect_project_profile()

        env_ok, env_message = manager.python_environment_status(profile)
        manifest_ok, manifest_message = manager.python_dependency_manifest_status(
            profile
        )

        assert env_ok is True
        assert "scikit-build-core" in env_message
        assert manifest_ok is True
        assert "pyproject.toml" in manifest_message


def test_scikit_build_constraints_do_not_require_poetry_lock(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / ".agents").mkdir()
        (root / ".agents" / "project.yml").write_text(
            "project_profile:\n"
            "  language: [python, cpp]\n"
            "  build_system: scikit-build-core\n"
        )
        (root / "pyproject.toml").write_text(
            "[build-system]\n"
            'requires = ["scikit-build-core>=0.8.0"]\n'
            'build-backend = "scikit_build_core.build"\n'
        )

        monkeypatch.chdir(root)
        manager = PreCommitManager(root)
        profile = manager.detect_project_profile()
        violations = check_python_dependency_constraints(profile)

        assert violations == []


def test_find_cpp_files_excludes_non_first_party_trees() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        sources = {
            "src/app.cpp": "int main() { return 0; }\n",
            "include/app.hpp": "#pragma once\n",
            ".agents/tool.cpp": "// agent infrastructure\n",
            ".venv/pkg.cpp": "// environment\n",
            "3rdparty/lib.cpp": "// vendored\n",
            "build/generated.cpp": "// generated\n",
            "_deps/lib-src/upstream.cpp": "// fetched dependency\n",
            "cmake-build-debug/generated.cpp": "// IDE build\n",
        }
        for relative, content in sources.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)

        manager = PreCommitManager(root)
        files = {str(path.relative_to(root)) for path in manager.find_cpp_files()}

        assert files == {
            "include/app.hpp",
            "src/app.cpp",
        }
