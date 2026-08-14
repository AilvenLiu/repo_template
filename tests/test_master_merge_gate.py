"""Tests for the deterministic master pull-request policy."""

import importlib.util
from pathlib import Path

_SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "master-merge-gate.py"
_SPEC = importlib.util.spec_from_file_location("master_merge_gate", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
master_merge_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(master_merge_gate)

_DEVELOP_SHA = "a" * 40
_HEAD_SHA = "b" * 40


def _violations(
    *,
    head_ref: str = "release/2026.07.22",
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


def _event(*, head_ref: str, body: str | None) -> dict[str, object]:
    return {
        "pull_request": {
            "body": body,
            "base": {
                "ref": "master",
                "repo": {"full_name": "example/project"},
            },
            "head": {
                "ref": head_ref,
                "sha": _HEAD_SHA,
                "repo": {"full_name": "example/project"},
            },
        }
    }


def test_master_accepts_only_declared_same_repository_sources() -> None:
    assert _violations(head_ref="develop")
    assert not _violations(head_ref="release/2026.07.22")
    assert not _violations(head_ref="hotfix/payment-timeout")
    assert _violations(head_ref="feat/direct-to-master")
    assert _violations(head_ref="release/")
    assert _violations(head_ref="hotfix/")
    assert _violations(head_repository="fork/project")


def test_release_projection_allows_only_forbidden_path_deletions() -> None:
    unchanged = ("100644", "blob", "a" * 40)
    source_tree = {
        ".agents/config.yml": ("100644", "blob", "b" * 40),
        "AGENTS.md": ("100644", "blob", "c" * 40),
        "docs/guide.md": ("100644", "blob", "d" * 40),
        "src/product.py": unchanged,
    }

    assert not master_merge_gate.validate_release_projection(
        develop_tree=source_tree,
        release_tree={"src/product.py": unchanged},
    )


def test_release_projection_rejects_every_functional_tree_change() -> None:
    unchanged = ("100644", "blob", "a" * 40)
    source_tree = {
        ".agents/config.yml": ("100644", "blob", "b" * 40),
        "docs/changelog/old.md": ("100644", "blob", "c" * 40),
        "src/product.py": unchanged,
    }

    cases = {
        "addition": {
            "src/new.py": ("100644", "blob", "d" * 40),
            "src/product.py": unchanged,
        },
        "modification": {"src/product.py": ("100644", "blob", "e" * 40)},
        "mode change": {"src/product.py": ("100755", "blob", "a" * 40)},
        "non-policy deletion": {},
    }

    for expected, release_tree in cases.items():
        violations = master_merge_gate.validate_release_projection(
            develop_tree=source_tree,
            release_tree=release_tree,
        )
        assert any(expected in violation for violation in violations), expected


def test_release_event_requires_and_validates_recorded_develop_sha(monkeypatch) -> None:
    unchanged = ("100644", "blob", "c" * 40)
    trees = {
        _DEVELOP_SHA: {
            ".agents/config.yml": ("100644", "blob", "d" * 40),
            "src/product.py": unchanged,
        },
        _HEAD_SHA: {"src/product.py": unchanged},
    }
    comparisons: list[tuple[str, str]] = []

    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_tree",
        lambda repository, sha, token: trees[sha],
    )

    def record_ancestry(
        repository: str, ancestor: str, descendant: str, token: str
    ) -> bool:
        comparisons.append((ancestor, descendant))
        return True

    monkeypatch.setattr(master_merge_gate, "_is_ancestor", record_ancestry)

    missing = master_merge_gate.validate_event(
        _event(head_ref="release/2026.07.22", body=None), "token"
    )
    assert any("Develop-Source-SHA" in violation for violation in missing)

    valid = master_merge_gate.validate_event(
        _event(
            head_ref="release/2026.07.22",
            body=f"Develop-Source-SHA: {_DEVELOP_SHA}",
        ),
        "token",
    )
    assert not valid
    assert comparisons == [(_DEVELOP_SHA, "develop"), (_DEVELOP_SHA, _HEAD_SHA)]


def test_release_event_rejects_unrelated_recorded_source(monkeypatch) -> None:
    monkeypatch.setattr(
        master_merge_gate, "_fetch_tree", lambda repository, sha, token: {}
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_is_ancestor",
        lambda repository, ancestor, descendant, token: False,
    )

    violations = master_merge_gate.validate_event(
        _event(
            head_ref="release/2026.07.22",
            body=f"Develop-Source-SHA: {_DEVELOP_SHA}",
        ),
        "token",
    )

    assert any("not reachable from develop" in violation for violation in violations)
    assert any("does not descend" in violation for violation in violations)


def test_release_source_field_must_be_unique_and_exact() -> None:
    assert (
        master_merge_gate._develop_source_sha(f"Develop-Source-SHA: {_DEVELOP_SHA}")
        == _DEVELOP_SHA
    )
    assert (
        master_merge_gate._develop_source_sha(
            f"Develop-Source-SHA: {_DEVELOP_SHA}\nDevelop-Source-SHA: {_HEAD_SHA}"
        )
        is None
    )
    assert master_merge_gate._develop_source_sha("Develop-Source-SHA: short") is None


def test_hotfix_event_requires_explicit_validation_tradeoff(monkeypatch) -> None:
    monkeypatch.setattr(
        master_merge_gate, "_fetch_tree", lambda repository, sha, token: {}
    )

    missing = master_merge_gate.validate_event(
        _event(head_ref="hotfix/payment-timeout", body=""), "token"
    )
    assert any("Hotfix-Validation-Tradeoff" in violation for violation in missing)

    valid = master_merge_gate.validate_event(
        _event(
            head_ref="hotfix/payment-timeout",
            body="Hotfix-Validation-Tradeoff: agent-precommit absent; ran hosted CI",
        ),
        "token",
    )
    assert not valid


def test_tree_fetch_preserves_blob_and_submodule_identity(monkeypatch) -> None:
    response = {
        "truncated": False,
        "tree": [
            {
                "path": "src",
                "mode": "040000",
                "type": "tree",
                "sha": "1" * 40,
            },
            {
                "path": "src/product.py",
                "mode": "100644",
                "type": "blob",
                "sha": "2" * 40,
            },
            {
                "path": "vendor/library",
                "mode": "160000",
                "type": "commit",
                "sha": "3" * 40,
            },
        ],
    }
    monkeypatch.setattr(
        master_merge_gate, "_request_json", lambda url, token, label: response
    )

    assert master_merge_gate._fetch_tree("example/project", _HEAD_SHA, "token") == {
        "src/product.py": ("100644", "blob", "2" * 40),
        "vendor/library": ("160000", "commit", "3" * 40),
    }


def test_ancestry_requires_zero_behind_commits(monkeypatch) -> None:
    response = {"behind_by": 0}
    monkeypatch.setattr(
        master_merge_gate, "_request_json", lambda url, token, label: response
    )
    assert master_merge_gate._is_ancestor(
        "example/project", _DEVELOP_SHA, _HEAD_SHA, "token"
    )

    response["behind_by"] = 1
    assert not master_merge_gate._is_ancestor(
        "example/project", _DEVELOP_SHA, _HEAD_SHA, "token"
    )


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
    assert "- edited" in workflow
    assert "trusted-policy/.github/scripts/master-merge-gate.py" in workflow
    assert "actions/checkout" not in workflow
