#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".ai" / "scripts" / "pre-commit"),
)
sys.path.insert(
    0,
    str(Path(__file__).parent.parent / ".ai" / "scripts"),
)

from utils import PreCommitManager  # type: ignore[import-not-found]


def test_find_python_files_excludes_agent_infrastructure_dirs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("print('ok')\n")
        (root / ".claude" / "skills").mkdir(parents=True)
        (root / ".claude" / "skills" / "tool.py").write_text("print('agent')\n")
        (root / ".ai" / "scripts").mkdir(parents=True)
        (root / ".ai" / "scripts" / "gate.py").write_text("print('agent')\n")

        manager = PreCommitManager(root)
        files = [str(path.relative_to(root)) for path in manager.find_python_files()]

        assert "src/app.py" in files
        assert ".claude/skills/tool.py" not in files
        assert ".ai/scripts/gate.py" not in files


def test_find_mypy_targets_falls_back_to_python_files_outside_git() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "src").mkdir()
        (root / "tests").mkdir()
        (root / "src" / "pkg.py").write_text("x = 1\n")
        (root / "tests" / "test_pkg.py").write_text("def test_x():\n    assert True\n")

        manager = PreCommitManager(root)
        assert manager.find_mypy_targets() == ["src/pkg.py", "tests/test_pkg.py"]
