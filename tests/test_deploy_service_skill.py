#!/usr/bin/env python3
"""Host-deployment and GitHub Actions CI/CD skill coverage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "create-project" / "scripts"))

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


@pytest.mark.parametrize("project_type", ["python", "cpp", "hybrid"])
@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_generated_project_loads_split_service_skills(
    tmp_path: Path, project_type: str, platform: str
) -> None:
    target = tmp_path / f"{project_type}-{platform}"
    create_project(ROOT, target, project_type)

    result = subprocess.run(
        ["python3", ".agents/scripts/common/verify_skills.py", "--platform", platform],
        cwd=target,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    for skill in ("deploy-service", "service-cicd"):
        assert (target / f".agents/skills/{skill}/SKILL.md").is_file()
        assert (target / f".claude/skills/{skill}/SKILL.md").is_file()
        assert skill in (target / "AGENTS.md").read_text()
        assert skill in (target / "CLAUDE.md").read_text()

    for entrypoint in ("AGENTS.md", "CLAUDE.md"):
        body = (target / entrypoint).read_text()
        assert "common/service-deployment.md" in body
        assert "common/github-actions-cicd.md" in body


def test_host_deployment_skill_owns_host_contract() -> None:
    skill = (ROOT / ".agents/skills/deploy-service/SKILL.md").read_text()
    required = (
        "/data/www/<service>",
        "~/data/www/<service>",
        "local `www/<service>`",
        "`/var/www/<service>` as a compatibility alternative",
        "immutable CI-built artefact",
        "Never run a newly uploaded script as root",
        "activation atomic",
        "rollback",
        "fails closed",
    )
    for phrase in required:
        assert phrase in skill

    references = ROOT / ".agents/skills/deploy-service/references"
    for reference in (
        "host-layout.md",
        "project-profiles.md",
        "static-releases.md",
        "service-releases.md",
        "host-bootstrap.md",
        "validation.md",
    ):
        assert (references / reference).is_file()
    assert not (references / "github-actions.md").exists()


def test_service_cicd_skill_owns_github_actions_contract() -> None:
    skill = (ROOT / ".agents/skills/service-cicd/SKILL.md").read_text()
    required = (
        "GitHub Actions",
        "full commit SHA",
        "Pull-request CI runs without production secrets",
        "built and tested once",
        "Auto-release",
        "serialized per environment",
        "protected workflow",
        "does not rebuild",
    )
    for phrase in required:
        assert phrase in skill

    references = ROOT / ".agents/skills/service-cicd/references"
    for reference in (
        "project-profiles.md",
        "github-actions.md",
        "release-promotion.md",
        "validation.md",
    ):
        assert (references / reference).is_file()


def test_both_service_contracts_are_required_and_always_loaded() -> None:
    capabilities = yaml.safe_load((ROOT / ".agents/capabilities.yml").read_text())
    required = {
        entry["id"]
        for entry in capabilities["common_requirements"]["project_skills"]
        if entry.get("required")
    }
    assert {"deploy-service", "service-cicd"} <= required

    init_source = (ROOT / ".agents/scripts/session_init.py").read_text()
    assert '"common/service-deployment"' in init_source
    assert '"common/github-actions-cicd"' in init_source
    assert (ROOT / ".agents/constraints/common/service-deployment.md").is_file()
    assert (ROOT / ".agents/constraints/common/github-actions-cicd.md").is_file()
