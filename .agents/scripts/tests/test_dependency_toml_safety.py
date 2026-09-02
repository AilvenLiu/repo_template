"""`agent-dependency` must never leave `pyproject.toml` unreadable.

On 2026-09-01 it did exactly that. Asked to add a dev dependency to a project
whose `dev` array is written on ONE line, it appended a second `dev = [...]`
entry to `[project.optional-dependencies]`, printed `[OK]`, and exited 0 --
leaving a duplicate key that no TOML parser accepts. The damage surfaced at
the next Poetry command rather than at the one that caused it:

    Invalid TOML file pyproject.toml: Key "dev" already exists.

The wrapper is the only sanctioned way to change dependencies in this
repository (`.agents/constraints/python/dependencies.md`), so a wrapper that
corrupts the manifest leaves no compliant path forward at all.

These tests drive the REAL `.agents/scripts/dependency/add.py`, following the
same path generated projects use. They live with the canonical agent scripts,
so every generated project carries the regression guard with the wrapper.
"""

from __future__ import annotations

import importlib.util
import sys
import tomllib
import types
from pathlib import Path
from typing import Any

import pytest

REPO = Path(__file__).resolve().parents[3]
ADD_SCRIPT = REPO / ".agents" / "scripts" / "dependency" / "add.py"

SINGLE_LINE = """\
[project]
name = "example"
requires-python = ">=3.11"
dependencies = ["numpy>=1.23", "pandas>=2.0"]

[project.optional-dependencies]
agents = ["openai>=1.30"]
dev = ["pytest>=8.0", "ruff>=0.5"]

[tool.poetry]
package-mode = false
"""

MULTI_LINE = """\
[project]
name = "example"
requires-python = ">=3.11"
dependencies = [
  "numpy>=1.23",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.0",
]

[tool.poetry]
package-mode = false
"""

EMPTY_AND_COMMENTED = """\
[project]
name = "example"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]  # the quality gate needs these

[tool.poetry]
package-mode = false
"""

NO_OPTIONAL_SECTION = """\
[project]
name = "example"
requires-python = ">=3.11"
dependencies = ["numpy>=1.23"]

[tool.poetry]
package-mode = false
"""


class StubManager:
    """Stands in for `DependencyManager`: a root, and a `poetry lock` recorder.

    The real one would shell out to Poetry against a throwaway directory that
    has no lock file and no resolvable project, so the lock call is recorded
    rather than performed.
    """

    def __init__(self, repo_root: Path, lock_returncode: int = 0) -> None:
        self.repo_root = repo_root
        self.lock_returncode = lock_returncode
        self.locked: list[list[str]] = []

    def run_command(
        self, cmd: list[str], cwd: Path | None = None
    ) -> tuple[int, str, str]:
        self.locked.append(cmd)
        if self.lock_returncode == 0:
            (self.repo_root / "poetry.lock").write_text("locked\n")
        error = "resolution failed" if self.lock_returncode else ""
        return self.lock_returncode, "", error


@pytest.fixture(scope="module")
def add_module() -> Any:
    """Load the real script without tripping its import-time session gate.

    `add.py` calls `check_session_initialized` at import, which `sys.exit(1)`s
    when `.agents/session_state.json` is absent -- true on any CI runner that
    has not run the init workflow. Stubbing that one import is what lets the
    rest of the real module be exercised as written.
    """
    stub = types.ModuleType("check_session")
    stub.check_session_initialized = lambda _skill: {}  # type: ignore[attr-defined]

    saved_modules = dict(sys.modules)
    saved_path = list(sys.path)
    sys.modules["check_session"] = stub
    sys.modules.pop("utils", None)
    try:
        spec = importlib.util.spec_from_file_location(
            "_agent_dependency_add", ADD_SCRIPT
        )
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.clear()
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path


def _add(
    module: Any, tmp_path: Path, body: str, package: str, version: str, dev: bool
) -> Any:
    (tmp_path / "pyproject.toml").write_text(body)
    manager = StubManager(tmp_path)
    module.add_dependency_scikit_build(manager, package, version, dev)
    return manager


def _document(tmp_path: Path) -> dict[str, Any]:
    """Parse the result -- which is the whole point, so never skip it."""
    return tomllib.loads((tmp_path / "pyproject.toml").read_text())


def test_a_single_line_dev_array_is_extended_in_place(
    add_module: Any, tmp_path: Path
) -> None:
    """The exact shape that produced a duplicate key."""
    _add(add_module, tmp_path, SINGLE_LINE, "duckdb", "==1.5.5", dev=True)

    document = _document(tmp_path)
    assert document["project"]["optional-dependencies"]["dev"] == [
        "pytest>=8.0",
        "ruff>=0.5",
        "duckdb==1.5.5",
    ]
    # The other keys in the same table are untouched.
    assert document["project"]["optional-dependencies"]["agents"] == ["openai>=1.30"]
    assert (tmp_path / "pyproject.toml").read_text().count("dev = [") == 1


def test_a_multi_line_dev_array_still_works(add_module: Any, tmp_path: Path) -> None:
    """The shape that already worked must keep working."""
    _add(add_module, tmp_path, MULTI_LINE, "duckdb", "==1.5.5", dev=True)

    assert _document(tmp_path)["project"]["optional-dependencies"]["dev"] == [
        "pytest>=8.0",
        "duckdb==1.5.5",
    ]


def test_an_empty_inline_array_gains_no_leading_comma(
    add_module: Any, tmp_path: Path
) -> None:
    _add(add_module, tmp_path, EMPTY_AND_COMMENTED, "numpy", "1.23", dev=False)

    assert _document(tmp_path)["project"]["dependencies"] == ["numpy>=1.23"]


def test_a_trailing_comment_survives_the_edit(add_module: Any, tmp_path: Path) -> None:
    _add(add_module, tmp_path, EMPTY_AND_COMMENTED, "duckdb", "==1.5.5", dev=True)

    text = (tmp_path / "pyproject.toml").read_text()
    assert "# the quality gate needs these" in text
    assert _document(tmp_path)["project"]["optional-dependencies"]["dev"] == [
        "pytest>=8.0",
        "duckdb==1.5.5",
    ]


def test_a_single_line_runtime_array_is_extended_in_place(
    add_module: Any, tmp_path: Path
) -> None:
    """The same latent defect on the runtime path."""
    _add(add_module, tmp_path, SINGLE_LINE, "scipy", "1.11", dev=False)

    document = _document(tmp_path)
    assert document["project"]["dependencies"] == [
        "numpy>=1.23",
        "pandas>=2.0",
        "scipy>=1.11",
    ]
    assert (tmp_path / "pyproject.toml").read_text().count("dependencies = [") == 1


def test_a_multi_line_runtime_array_still_works(
    add_module: Any, tmp_path: Path
) -> None:
    _add(add_module, tmp_path, MULTI_LINE, "scipy", "1.11", dev=False)

    assert _document(tmp_path)["project"]["dependencies"] == [
        "numpy>=1.23",
        "scipy>=1.11",
    ]


def test_a_missing_optional_dependencies_section_is_created(
    add_module: Any, tmp_path: Path
) -> None:
    _add(add_module, tmp_path, NO_OPTIONAL_SECTION, "duckdb", "==1.5.5", dev=True)

    assert _document(tmp_path)["project"]["optional-dependencies"]["dev"] == [
        "duckdb==1.5.5"
    ]


def test_the_lock_file_is_refreshed_with_the_manifest(
    add_module: Any, tmp_path: Path
) -> None:
    """`pyproject.toml` and `poetry.lock` move together, or neither is trusted."""
    manager = _add(add_module, tmp_path, SINGLE_LINE, "duckdb", "==1.5.5", dev=True)

    assert manager.locked == [["poetry", "lock"]]
    assert (tmp_path / "poetry.lock").read_text() == "locked\n"


def test_lock_failure_restores_manifest_and_lock(
    add_module: Any, tmp_path: Path
) -> None:
    """A failed resolution must leave neither dependency file half-updated."""
    manifest = tmp_path / "pyproject.toml"
    lock = tmp_path / "poetry.lock"
    manifest.write_text(SINGLE_LINE)
    lock.write_text("original lock\n")
    manager = StubManager(tmp_path, lock_returncode=1)

    with pytest.raises(SystemExit) as excinfo:
        add_module.add_dependency_scikit_build(manager, "duckdb", "==1.5.5", dev=True)
    assert lock.read_text() == "original lock\n"

    assert excinfo.value.code == 1
    assert manifest.read_text() == SINGLE_LINE


def test_an_edit_that_would_corrupt_the_file_is_refused(
    add_module: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The guard, proven against a deliberately broken insertion.

    This reproduces the original defect's SHAPE -- a second `dev` key -- by
    forcing the insertion helper to misbehave, and asserts the file is left
    exactly as it was rather than written unreadable.
    """

    def corrupt(lines: list[str], index: int, dep_string: str) -> bool:
        lines.insert(index + 1, f'dev = ["{dep_string}"]\n')
        return True

    monkeypatch.setattr(add_module, "_append_to_inline_array", corrupt)

    target = tmp_path / "pyproject.toml"
    target.write_text(SINGLE_LINE)
    with pytest.raises(SystemExit) as excinfo:
        add_module.add_dependency_scikit_build(
            StubManager(tmp_path), "duckdb", "==1.5.5", True
        )

    assert excinfo.value.code == 1
    assert target.read_text() == SINGLE_LINE
    assert tomllib.loads(target.read_text())


def test_a_dependency_already_present_is_not_added_twice(
    add_module: Any, tmp_path: Path
) -> None:
    (tmp_path / "pyproject.toml").write_text(SINGLE_LINE)
    with pytest.raises(SystemExit):
        add_module.add_dependency_scikit_build(
            StubManager(tmp_path), "ruff", ">=0.5", True
        )

    assert (tmp_path / "pyproject.toml").read_text() == SINGLE_LINE
