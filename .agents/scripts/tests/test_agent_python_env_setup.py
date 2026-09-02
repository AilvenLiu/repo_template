"""Tests for caller environment capture in Python setup wrappers."""

import runpy
import sys
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATHS = (
    PROJECT_ROOT / ".agents" / "scripts" / "python-env-setup" / "verify.py",
    PROJECT_ROOT / ".agents" / "scripts" / "python-env-setup" / "diagnose.py",
    PROJECT_ROOT / ".agents" / "scripts" / "python-env-setup" / "fix.py",
)


def _load_caller_virtual_env(path: Path) -> Callable[[], str | None]:
    """Load a setup module's caller-environment helper without running its CLI."""
    sys.path.insert(0, str(path.parent))
    try:
        namespace = runpy.run_path(str(path), run_name=f"test_{path.stem}")
    finally:
        sys.path.pop(0)
    return cast(Callable[[], str | None], namespace["_caller_virtual_env"])


def _load_constraint_matcher() -> Callable[[str, str], bool]:
    """Load the shared bounded Python-constraint matcher."""
    path = MODULE_PATHS[0].parent / "version_constraints.py"
    namespace = runpy.run_path(str(path), run_name="test_version_constraints")
    return cast(Callable[[str, str], bool], namespace["matches_python_constraint"])


@pytest.mark.parametrize("module_path", MODULE_PATHS)
def test_poetry_virtual_env_is_ignored_when_caller_was_unset(
    monkeypatch: pytest.MonkeyPatch,
    module_path: Path,
) -> None:
    """Poetry's wrapper environment must not be mistaken for caller activation."""
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")
    monkeypatch.setenv("AGENT_CALLER_VIRTUAL_ENV_SET", "0")
    monkeypatch.delenv("AGENT_CALLER_VIRTUAL_ENV", raising=False)

    caller_virtual_env = _load_caller_virtual_env(module_path)

    assert caller_virtual_env() is None


@pytest.mark.parametrize("module_path", MODULE_PATHS)
def test_external_caller_virtual_env_is_preserved(
    monkeypatch: pytest.MonkeyPatch,
    module_path: Path,
) -> None:
    """A genuine caller activation must remain a verification failure signal."""
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")
    monkeypatch.setenv("AGENT_CALLER_VIRTUAL_ENV_SET", "1")
    monkeypatch.setenv("AGENT_CALLER_VIRTUAL_ENV", "/external/.venv")

    caller_virtual_env = _load_caller_virtual_env(module_path)

    assert caller_virtual_env() == "/external/.venv"


@pytest.mark.parametrize("module_path", MODULE_PATHS)
def test_direct_execution_falls_back_to_runtime_virtual_env(
    monkeypatch: pytest.MonkeyPatch,
    module_path: Path,
) -> None:
    """Direct script execution must retain the legacy runtime check."""
    monkeypatch.delenv("AGENT_CALLER_VIRTUAL_ENV_SET", raising=False)
    monkeypatch.delenv("AGENT_CALLER_VIRTUAL_ENV", raising=False)
    monkeypatch.setenv("VIRTUAL_ENV", "/direct/.venv")

    caller_virtual_env = _load_caller_virtual_env(module_path)

    assert caller_virtual_env() == "/direct/.venv"


@pytest.mark.parametrize("module_path", MODULE_PATHS)
def test_empty_caller_virtual_env_is_treated_as_unset(
    monkeypatch: pytest.MonkeyPatch,
    module_path: Path,
) -> None:
    """An empty caller marker is not an activated virtual environment."""
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")
    monkeypatch.setenv("AGENT_CALLER_VIRTUAL_ENV_SET", "1")
    monkeypatch.setenv("AGENT_CALLER_VIRTUAL_ENV", "")

    caller_virtual_env = _load_caller_virtual_env(module_path)

    assert caller_virtual_env() is None


@pytest.mark.parametrize("module_path", MODULE_PATHS)
def test_legacy_parent_marker_remains_supported(
    monkeypatch: pytest.MonkeyPatch,
    module_path: Path,
) -> None:
    """Older generated callers must retain the original marker contract."""
    monkeypatch.delenv("AGENT_CALLER_VIRTUAL_ENV_SET", raising=False)
    monkeypatch.delenv("AGENT_CALLER_VIRTUAL_ENV", raising=False)
    monkeypatch.setenv("VIRTUAL_ENV", "/project/.venv")
    monkeypatch.setenv("AGENT_PARENT_VIRTUAL_ENV_SET", "0")
    monkeypatch.delenv("AGENT_PARENT_VIRTUAL_ENV", raising=False)

    caller_virtual_env = _load_caller_virtual_env(module_path)

    assert caller_virtual_env() is None


def test_wrapper_captures_caller_environment_before_dispatch() -> None:
    """The shell wrapper must snapshot caller state before Poetry dispatch."""
    wrapper = (PROJECT_ROOT / ".agents" / "bin" / "agent-python-env-setup").read_text(
        encoding="utf-8"
    )

    capture_offset = wrapper.index("AGENT_CALLER_VIRTUAL_ENV_SET")

    assert capture_offset < wrapper.index("main()")
    assert 'AGENT_CALLER_VIRTUAL_ENV="$VIRTUAL_ENV"' in wrapper


@pytest.mark.parametrize(
    "version,constraint,expected",
    [
        ("3.14.4", ">=3.14.4,<3.15", True),
        ("3.14.3", ">=3.14.4,<3.15", False),
        ("3.15.0", ">=3.14.4,<3.15", False),
        ("3.14.4", "^3.14", True),
        ("4.0.0", "^3.14", False),
        ("0.9.0", "^0", True),
        ("1.0.0", "^0", False),
        ("0.0.9", "^0.0", True),
        ("0.1.0", "^0.0", False),
        ("3.14.9", "~3.14.4", True),
        ("3.15.0", "~3.14.4", False),
        ("3.14.4", ">=3.14.4,<invalid", False),
    ],
)
def test_python_constraint_matcher_is_fail_closed(
    version: str,
    constraint: str,
    expected: bool,
) -> None:
    """Environment checks must understand bounded ranges and reject malformed input."""
    assert _load_constraint_matcher()(version, constraint) is expected


def test_roadmap_wrapper_uses_the_poetry_aware_python_dispatch() -> None:
    """Roadmap commands must import locked project dependencies through Poetry."""
    wrapper = (PROJECT_ROOT / ".agents" / "bin" / "agent-roadmap").read_text(
        encoding="utf-8"
    )

    assert "exec python3" not in wrapper
    for script_name in (
        "check.py",
        "create.py",
        "status.py",
        "update.py",
        "handoff.py",
        "complete.py",
        "validate_schema.py",
    ):
        assert (
            f'run_agent_python "$REPO_ROOT" "$ROADMAP_SCRIPTS/{script_name}" "$@"'
            in wrapper
        )


def test_precommit_runs_application_and_agent_infrastructure_tests() -> None:
    """The authoritative develop gate must collect both test ownership trees."""
    validator = (
        PROJECT_ROOT / ".agents" / "scripts" / "pre-commit" / "validate.py"
    ).read_text(encoding="utf-8")

    assert '"tests"' in validator
    assert '".agents/scripts/tests"' in validator
