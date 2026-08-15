#!/usr/bin/env python3
"""Tests for profile-aware constraint checking."""

from __future__ import annotations

import json
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


def _python_profile() -> ProjectProfile:
    return ProjectProfile(
        language=[Language.PYTHON],
        build_system=BuildSystem.POETRY,
    )


_FULL_SHA = "0" * 40


def _write_artifact_upload_workflow(repo: Path, retention_days: int) -> Path:
    workflow = repo / ".github" / "workflows" / "artifact-transfer.yml"
    workflow.parent.mkdir(parents=True, exist_ok=True)
    workflow.write_text(
        "\n".join(
            (
                "name: artifact transfer",
                "on: workflow_dispatch",
                "jobs:",
                "  build:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Upload handoff",
                f"        uses: actions/upload-artifact@{_FULL_SHA}",
                "        with:",
                "          name: handoff",
                "          path: dist",
                f"          retention-days: {retention_days}",
                "",
            )
        ),
        encoding="utf-8",
    )
    return workflow


def _action_line(workflow: Path, surface: str) -> int:
    needle = f"uses: {surface}@"
    for line_number, line in enumerate(workflow.read_text().splitlines(), start=1):
        if needle in line:
            return line_number
    raise AssertionError(f"missing {surface} in {workflow}")


def _valid_artifact_exception(
    *,
    action_line: int,
    artifact_name: str = "handoff",
    surface: str = "actions/upload-artifact",
) -> dict[str, object]:
    return {
        "workflow": ".github/workflows/artifact-transfer.yml",
        "surface": surface,
        "action_line": action_line,
        "technical_necessity": "The local store, direct transfer, and approved pull interface cannot serve this tested route.",
        "user_request": "The current user explicitly requested this one-day transfer.",
        "request_reference": "Current task request: tested temporary transfer only.",
        "producer": "build",
        "consumer": "deploy",
        "environment": "staging",
        "contents": "Non-secret signed release archive.",
        "artifact_name": artifact_name,
        "source_sha": "a" * 40,
        "digest": "sha256:" + "b" * 64,
        "size_limit_bytes": 1048576,
        "retention_days": 1,
        "non_secret": True,
        "release_or_rollback_authority": False,
        "reviewed": True,
    }


def _write_artifact_exceptions(repo: Path, exceptions: list[dict[str, object]]) -> None:
    policy = repo / ".agents" / "github-artifact-exceptions.json"
    policy.parent.mkdir(parents=True, exist_ok=True)
    policy.write_text(
        json.dumps({"version": 1, "exceptions": exceptions}),
        encoding="utf-8",
    )


def test_github_artifact_storage_fails_closed_without_exception(tmp_path: Path) -> None:
    _write_artifact_upload_workflow(tmp_path, retention_days=1)

    violations = check_constraints(tmp_path, _python_profile())

    assert any(
        violation.category == "GitHub Artifact Storage"
        and "default-deny" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_accepts_complete_one_day_exception(
    tmp_path: Path,
) -> None:
    workflow = _write_artifact_upload_workflow(tmp_path, retention_days=1)
    _write_artifact_exceptions(
        tmp_path,
        [
            _valid_artifact_exception(
                action_line=_action_line(workflow, "actions/upload-artifact")
            )
        ],
    )

    violations = check_constraints(tmp_path, _python_profile())

    assert not any(
        violation.category == "GitHub Artifact Storage" for violation in violations
    )


def test_github_artifact_storage_requires_workflow_one_day_retention(
    tmp_path: Path,
) -> None:
    workflow = _write_artifact_upload_workflow(tmp_path, retention_days=2)
    _write_artifact_exceptions(
        tmp_path,
        [
            _valid_artifact_exception(
                action_line=_action_line(workflow, "actions/upload-artifact")
            )
        ],
    )

    violations = check_constraints(tmp_path, _python_profile())

    assert any(
        violation.category == "GitHub Artifact Storage"
        and "retention-days: 1" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_rejects_second_same_surface_without_own_exception(
    tmp_path: Path,
) -> None:
    workflow = _write_artifact_upload_workflow(tmp_path, retention_days=1)
    workflow.write_text(
        workflow.read_text()
        + "\n".join(
            (
                "      - name: Upload another handoff",
                f"        uses: actions/upload-artifact@{_FULL_SHA}",
                "        with:",
                "          name: handoff-two",
                "          path: dist-two",
                "          retention-days: 1",
                "",
            )
        ),
        encoding="utf-8",
    )
    _write_artifact_exceptions(
        tmp_path,
        [
            _valid_artifact_exception(
                action_line=_action_line(workflow, "actions/upload-artifact")
            )
        ],
    )

    violations = check_constraints(tmp_path, _python_profile())

    assert any(
        violation.category == "GitHub Artifact Storage"
        and "without one exact reviewed exception" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_rejects_local_composite_action(tmp_path: Path) -> None:
    action = tmp_path / ".github" / "actions" / "hidden-transfer" / "action.yml"
    action.parent.mkdir(parents=True)
    action.write_text(
        "\n".join(
            (
                "name: hidden transfer",
                "runs:",
                "  using: composite",
                "  steps:",
                "    - name: Upload",
                f"      uses: actions/upload-artifact@{_FULL_SHA}",
                "      with:",
                "        name: handoff",
                "        path: dist",
                "        retention-days: 1",
                "",
            )
        ),
        encoding="utf-8",
    )
    _write_artifact_exceptions(tmp_path, [])

    violations = check_constraints(tmp_path, _python_profile())

    assert any(
        violation.category == "GitHub Artifact Storage"
        and "hides actions/upload-artifact outside a workflow" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_rejects_actions_api_route(tmp_path: Path) -> None:
    workflow = tmp_path / ".github" / "workflows" / "artifact-api.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            (
                "name: API transfer",
                "on: workflow_dispatch",
                "jobs:",
                "  retrieve:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - name: Download through API",
                '        run: gh api "$GITHUB_API_URL/repos/acme/project/actions/runs/1/artifacts"',
                "",
            )
        ),
        encoding="utf-8",
    )
    _write_artifact_exceptions(tmp_path, [])

    violations = check_constraints(tmp_path, _python_profile())

    assert any(
        violation.category == "GitHub Artifact Storage"
        and "uninspectable github-actions-artifact-api" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_rejects_helper_script_route(tmp_path: Path) -> None:
    for relative in (
        ".github/scripts/fetch.sh",
        "ci/fetch.sh",
        "scripts/fetch.sh",
        "tools/fetch.sh",
    ):
        repo = tmp_path / relative.replace("/", "_")
        helper = repo / relative
        helper.parent.mkdir(parents=True)
        helper.write_text("#!/bin/bash\ngh run download 1\n", encoding="utf-8")

        violations = check_constraints(repo, _python_profile())

        assert any(
            violation.category == "GitHub Artifact Storage"
            and f"{relative}:2 hides gh run download outside a workflow"
            in violation.message
            for violation in violations
        ), relative


def test_github_artifact_storage_reports_ineligible_route_reason(
    tmp_path: Path,
) -> None:
    """An ineligible route names its own defect, not a missing exception file."""
    helper = tmp_path / "ci" / "fetch.sh"
    helper.parent.mkdir(parents=True)
    helper.write_text("#!/bin/bash\ngh run download 1\n", encoding="utf-8")

    violations = [
        violation
        for violation in check_constraints(tmp_path, _python_profile())
        if violation.category == "GitHub Artifact Storage"
    ]

    assert violations
    assert not any(
        "github-artifact-exceptions.json" in violation.message
        for violation in violations
    )


def test_github_artifact_storage_ignores_unrelated_actions_paths(
    tmp_path: Path,
) -> None:
    """A local composite action named `artifacts` is not an Actions API route."""
    workflow = tmp_path / ".github" / "workflows" / "local.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            (
                "name: local composite",
                "on: workflow_dispatch",
                "jobs:",
                "  build:",
                "    runs-on: ubuntu-latest",
                "    steps:",
                "      - uses: ./.github/actions/artifacts",
                '      - run: echo "never call the actions/artifacts API"',
                "",
            )
        ),
        encoding="utf-8",
    )

    violations = check_constraints(tmp_path, _python_profile())

    assert not any(
        violation.category == "GitHub Artifact Storage" for violation in violations
    )
