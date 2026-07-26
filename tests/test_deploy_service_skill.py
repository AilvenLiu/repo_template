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

    assert (
        target / ".agents/skills/service-cicd/references/self-hosted-runners.md"
    ).is_file()

    for entrypoint in ("AGENTS.md", "CLAUDE.md"):
        body = (target / entrypoint).read_text()
        assert "common/service-deployment.md" in body
        assert "common/github-actions-cicd.md" in body
        assert "automatic deployment" in body
        assert "automatic release run only after `master` is updated" in body
        assert "canonical root beneath `/data/`, `~/data/`" in body
        assert "never uses `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`" in body


def test_host_deployment_skill_owns_host_contract() -> None:
    skill = (ROOT / ".agents/skills/deploy-service/SKILL.md").read_text()
    required = (
        "/data/www/<service>",
        "~/data/www/<service>",
        "dedicated data volume",
        "reject `/var/`",
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
        "self-hosted-runners.md",
        "release-promotion.md",
        "validation.md",
    ):
        assert (references / reference).is_file()


def test_self_hosted_ci_and_ssh_deploy_have_separate_contracts() -> None:
    runner_reference = (
        ROOT / ".agents/skills/service-cicd/references/self-hosted-runners.md"
    ).read_text()
    required = (
        "Pattern A: CI compute",
        "Pattern B: deployment",
        "different operating-system principals",
        "no interactive login and no sudo",
        "SHA-256",
        "Restart=on-failure",
        "OOMScoreAdjust",
        "~/.local/bin",
        "active job worker",
        "per-run swapfile",
        "toolchain",
    )
    for phrase in required:
        assert phrase in runner_reference

    cicd_constraint = (
        ROOT / ".agents/constraints/common/github-actions-cicd.md"
    ).read_text()
    deployment_constraint = (
        ROOT / ".agents/constraints/common/service-deployment.md"
    ).read_text()
    assert "Pattern A" in cicd_constraint
    assert "Pattern B" in cicd_constraint
    assert "MUST NOT overlap" in cicd_constraint
    assert "self-hosted ci compute is not a deployment identity" in (
        deployment_constraint.lower()
    )


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


def test_default_automatic_promotion_is_master_only() -> None:
    cicd_constraint = (
        ROOT / ".agents/constraints/common/github-actions-cicd.md"
    ).read_text()
    assert "only after an update to `master`" in cicd_constraint
    assert "exact `github.sha`" in cicd_constraint
    assert "has no default" in cicd_constraint
    assert "authority to publish a version" in cicd_constraint

    deployment_constraint = (
        ROOT / ".agents/constraints/common/service-deployment.md"
    ).read_text()
    assert "authorised only by an update to `master`" in deployment_constraint
    assert "exact updated" in deployment_constraint
    assert "`master` SHA" in deployment_constraint
    assert "Do not use `/var/`, `/srv/`, `/opt/`, `/usr/`, `/usr/local/`" in (
        deployment_constraint
    )

    deploy_skill = (ROOT / ".agents/skills/deploy-service/SKILL.md").read_text()
    cicd_skill = (ROOT / ".agents/skills/service-cicd/SKILL.md").read_text()
    governance_skill = (ROOT / ".agents/skills/branch-governance/SKILL.md").read_text()
    for body in (deploy_skill, cicd_skill, governance_skill):
        assert "project-specific" in body
        assert "policy" in body
        assert "`master`" in body
        assert "release" in body

    github_reference = (
        ROOT / ".agents/skills/service-cicd/references/github-actions.md"
    ).read_text()
    promotion_reference = (
        ROOT / ".agents/skills/service-cicd/references/release-promotion.md"
    ).read_text()
    host_reference = (
        ROOT / ".agents/skills/deploy-service/references/service-releases.md"
    ).read_text()
    assert "github.ref == 'refs/heads/master'" in github_reference
    assert "exact updated `master` SHA" in promotion_reference
    assert "exact SHA produced by" in host_reference
    assert "`master` update" in host_reference

    for profile in ("python", "cpp", "hybrid"):
        for entrypoint in ("AGENTS.md", "CLAUDE.md"):
            body = (ROOT / "templates" / profile / entrypoint).read_text()
            assert "automatic deployment" in body
            assert "automatic release run only after `master` is updated" in body
