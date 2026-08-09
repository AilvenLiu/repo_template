"""Tests for the deterministic master pull-request policy."""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "master-merge-gate.py"
_SPEC = importlib.util.spec_from_file_location("master_merge_gate", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
master_merge_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(master_merge_gate)


def _violations(
    *,
    head_ref: str = "develop",
    head_repository: str = "example/project",
    changed_paths: list[str] | None = None,
) -> list[str]:
    return master_merge_gate.validate_master_pull_request(
        base_ref="master",
        head_ref=head_ref,
        base_repository="example/project",
        head_repository=head_repository,
        source_tree_paths=changed_paths or [],
    )


def test_master_accepts_only_declared_same_repository_sources() -> None:
    assert not _violations(head_ref="develop")
    assert not _violations(head_ref="release/2026.07.22")
    assert not _violations(head_ref="hotfix/payment-timeout")
    assert _violations(head_ref="feat/direct-to-master")
    assert _violations(head_ref="release/")
    assert _violations(head_ref="hotfix/")
    assert _violations(head_repository="fork/project")


def test_master_rejects_all_development_only_paths() -> None:
    forbidden_paths = [
        ".ai",
        ".ai/settings.yml",
        ".agents",
        ".agents/scripts/policy_gate.py",
        ".claude",
        ".claude/settings.json",
        ".codex",
        ".codex/hooks.json",
        "agent_roadmaps",
        "agent_roadmaps/phase-1/ROADMAP.md",
        "AGENTS.md",
        "CLAUDE.md",
        "CODEX.md",
        "docs",
        "docs/architecture.md",
        "docs/guide/index.md",
    ]

    for path in forbidden_paths:
        violations = _violations(changed_paths=[path])
        assert any(path in violation for violation in violations), path


def test_master_allows_changelog_and_product_paths() -> None:
    assert not _violations(
        changed_paths=[
            "src/product.py",
            "docs/changelog",
            "docs/changelog/2026-07-22.md",
            "docs/changelog/README.md",
            ".github/workflows/product-validation.yml",
        ]
    )


def test_master_rejects_renamed_development_paths() -> None:
    violations = _violations(
        changed_paths=["src/policy.py", ".agents/scripts/policy.py"]
    )
    assert any(".agents/scripts/policy.py" in violation for violation in violations)


def test_non_master_target_is_outside_the_gate_scope() -> None:
    assert not master_merge_gate.validate_master_pull_request(
        base_ref="develop",
        head_ref="feat/example",
        base_repository="example/project",
        head_repository="fork/project",
        source_tree_paths=[".agents/scripts/policy_gate.py"],
    )


def test_workflow_uses_trusted_policy_and_read_only_permissions() -> None:
    workflow = (
        Path(__file__).parent.parent / ".github" / "workflows" / "master-merge-gate.yml"
    ).read_text(encoding="utf-8")

    assert "pull_request_target:" in workflow
    assert "- master" in workflow
    assert "contents: read" in workflow
    assert "pull-requests: read" in workflow
    assert "trusted-policy/.github/scripts/master-merge-gate.py" in workflow
    assert "actions/checkout" not in workflow
