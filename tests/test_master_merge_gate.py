"""Tests for the deterministic master pull-request policy."""

import base64
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).parent.parent / ".github" / "scripts" / "master-merge-gate.py"
_SPEC = importlib.util.spec_from_file_location("master_merge_gate", _SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
master_merge_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(master_merge_gate)

_DEVELOP_SHA = "a" * 40
_HEAD_SHA = "b" * 40
_SOURCE_SHA = "c" * 40
_MASTER_SHA = "d" * 40


def _violations(
    *,
    head_ref: str = "release/v1.2.3",
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
                "sha": _MASTER_SHA,
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
    assert not _violations(head_ref="release/v1.2.3")
    assert not _violations(head_ref="hotfix/v1.2.4")
    assert not _violations(head_ref="release/v0.1.0")
    assert not _violations(head_ref="release/v10.20.30")
    assert _violations(head_ref="feat/direct-to-master")
    assert _violations(head_ref="release/")
    assert _violations(head_ref="hotfix/")
    assert _violations(head_repository="fork/project")


def test_master_source_branch_requires_exact_semantic_version_name() -> None:
    """Only release/v<x.y.z> and hotfix/v<x.y.z> may reach master."""
    for rejected in (
        "release/2026.07.22",
        "release/1.2.3",
        "release/v1.2",
        "release/v1.2.3.4",
        "release/v1.2.3-rc1",
        "release/v1.2.3+build7",
        "release/v01.2.3",
        "release/vnext",
        "release/v1.2.3/extra",
        "chore/release-v1.2.3",
        "hotfix/payment-timeout",
    ):
        assert _violations(head_ref=rejected), rejected


def test_branch_and_tag_version_parsers_agree_on_canonical_names() -> None:
    assert master_merge_gate.branch_version("release/v1.2.3") == (1, 2, 3)
    assert master_merge_gate.branch_version("hotfix/v0.0.1") == (0, 0, 1)
    assert master_merge_gate.branch_version("release/v1.2.3-rc1") is None
    assert master_merge_gate.tag_version("release-v2.0.1") == (2, 0, 1)
    assert master_merge_gate.tag_version("v2.0.1") is None
    assert master_merge_gate.tag_version("release/v2.0.1") is None
    assert master_merge_gate.format_version((1, 2, 3)) == "1.2.3"


_PYPROJECT = '[project]\nname = "demo"\nversion = "{version}"\n'
_POETRY = '[tool.poetry]\nname = "demo"\nversion = "{version}"\n'
_CMAKE = "cmake_minimum_required(VERSION 3.24)\nproject(demo VERSION {version} LANGUAGES CXX)\n"


def _version_violations(
    *,
    head_ref: str = "release/v1.2.3",
    source: dict[str, str] | None = None,
    master: dict[str, str] | None = None,
) -> list[str]:
    return master_merge_gate.validate_release_version(
        head_ref=head_ref,
        source_manifests=source if source is not None else {},
        master_manifests=master if master is not None else {},
    )


def test_version_manifest_is_parsed_for_every_project_profile() -> None:
    """Python reads pyproject, cpp and hybrid read CMake as the authority."""
    assert (
        master_merge_gate.parse_pyproject_version(_PYPROJECT.format(version="1.2.3"))
        == "1.2.3"
    )
    assert (
        master_merge_gate.parse_pyproject_version(_POETRY.format(version="4.5.6"))
        == "4.5.6"
    )
    assert (
        master_merge_gate.parse_cmake_version(_CMAKE.format(version="1.2.3")) == "1.2.3"
    )
    assert (
        master_merge_gate.parse_cmake_version(
            "# project(ignored VERSION 9.9.9)\nproject(demo VERSION 1.0.0)\n"
        )
        == "1.0.0"
    )


def test_malformed_pyproject_does_not_fall_back_on_modern_python() -> None:
    malformed = '[project]\nversion = "1.2.3"\nbroken = [\n'
    assert master_merge_gate.parse_pyproject_version(malformed) is None


def test_branch_version_must_match_the_source_manifest() -> None:
    assert not _version_violations(
        source={"pyproject.toml": _PYPROJECT.format(version="1.2.3")}
    )
    assert not _version_violations(
        source={"CMakeLists.txt": _CMAKE.format(version="1.2.3")}
    )
    assert _version_violations(
        source={"pyproject.toml": _PYPROJECT.format(version="1.2.4")}
    )
    assert _version_violations(source={})


def test_hybrid_manifests_must_declare_the_same_version() -> None:
    """CMake is authoritative; a disagreeing pyproject is a hard failure."""
    assert not _version_violations(
        source={
            "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
            "pyproject.toml": _PYPROJECT.format(version="1.2.3"),
        }
    )
    assert _version_violations(
        source={
            "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
            "pyproject.toml": _PYPROJECT.format(version="1.2.4"),
        }
    )


def test_promoted_version_rejects_prerelease_and_build_suffixes() -> None:
    for rejected in ("1.2.3-dev", "1.2.3-rc1", "1.2.3+build7", "1.2", "01.2.3"):
        assert _version_violations(
            head_ref="release/v1.2.3",
            source={"pyproject.toml": _PYPROJECT.format(version=rejected)},
        ), rejected


def test_candidate_version_must_exceed_the_version_on_master() -> None:
    source = {"pyproject.toml": _PYPROJECT.format(version="1.2.3")}
    assert not _version_violations(
        source=source, master={"pyproject.toml": _PYPROJECT.format(version="1.2.2")}
    )
    assert not _version_violations(
        source=source, master={"pyproject.toml": _PYPROJECT.format(version="0.9.9")}
    )
    assert _version_violations(
        source=source, master={"pyproject.toml": _PYPROJECT.format(version="1.2.3")}
    )
    assert _version_violations(
        source=source, master={"pyproject.toml": _PYPROJECT.format(version="1.3.0")}
    )
    assert _version_violations(
        source=source, master={"pyproject.toml": _PYPROJECT.format(version="2.0.0")}
    )


def test_invalid_master_version_fails_closed() -> None:
    violations = _version_violations(
        source={"pyproject.toml": _PYPROJECT.format(version="1.2.3")},
        master={"pyproject.toml": _PYPROJECT.format(version="1.2.2-rc1")},
    )
    assert any("master pyproject.toml" in violation for violation in violations)


def test_first_release_is_allowed_when_master_declares_no_version() -> None:
    assert not _version_violations(
        head_ref="release/v0.1.0",
        source={"pyproject.toml": _PYPROJECT.format(version="0.1.0")},
        master={},
    )


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


def _metadata_case(
    *,
    parent_manifests: dict[str, str],
    source_manifests: dict[str, str],
    source_parents: list[str] | None = None,
    extra_source_tree: dict[str, tuple[str, str, str]] | None = None,
    source_modes: dict[str, str] | None = None,
) -> list[str]:
    unchanged = ("100644", "blob", "f" * 40)
    parent_tree = {"src/product.py": unchanged}
    source_tree = {"src/product.py": unchanged}
    for index, path in enumerate(parent_manifests):
        parent_tree[path] = ("100644", "blob", str(index + 1) * 40)
    for index, path in enumerate(source_manifests):
        mode = (source_modes or {}).get(path, "100644")
        source_tree[path] = (mode, "blob", str(index + 5) * 40)
    source_tree.update(extra_source_tree or {})
    return master_merge_gate.validate_release_metadata_only(
        parent_sha=_SOURCE_SHA,
        source_parent_shas=(
            [_SOURCE_SHA] if source_parents is None else source_parents
        ),
        parent_tree=parent_tree,
        source_tree=source_tree,
        parent_manifests=parent_manifests,
        source_manifests=source_manifests,
    )


def test_metadata_only_proof_accepts_python_and_hybrid_version_fields() -> None:
    parent_python = '[project]\nname = "demo"\nversion = "1.2.2"  # release\n'
    source_python = '[project]\nname = "demo"\nversion = "1.2.3"  # release\n'
    assert not _metadata_case(
        parent_manifests={"pyproject.toml": parent_python},
        source_manifests={"pyproject.toml": source_python},
    )

    parent_cmake = (
        "project(\n  # VERSION 9.9.9 is documentation\n"
        "  demo VERSION 1.2.2 LANGUAGES CXX)\n"
    )
    source_cmake = parent_cmake.replace("1.2.2", "1.2.3")
    assert not _metadata_case(
        parent_manifests={
            "CMakeLists.txt": parent_cmake,
            "pyproject.toml": _PYPROJECT.format(version="1.2.2"),
        },
        source_manifests={
            "CMakeLists.txt": source_cmake,
            "pyproject.toml": _PYPROJECT.format(version="1.2.3"),
        },
    )


@pytest.mark.parametrize(
    ("case", "kwargs", "expected"),
    [
        (
            "wrong parent",
            {"source_parents": ["d" * 40]},
            "exactly the recorded parent",
        ),
        (
            "merge commit",
            {"source_parents": [_SOURCE_SHA, "d" * 40]},
            "exactly the recorded parent",
        ),
        (
            "non-version path",
            {"extra_source_tree": {"src/sneaky.py": ("100644", "blob", "e" * 40)}},
            "non-version path",
        ),
        (
            "manifest mode",
            {"source_modes": {"pyproject.toml": "100755"}},
            "mode or type",
        ),
    ],
)
def test_metadata_only_proof_rejects_structural_bypasses(
    case: str, kwargs: dict[str, object], expected: str
) -> None:
    violations = _metadata_case(
        parent_manifests={"pyproject.toml": _PYPROJECT.format(version="1.2.2")},
        source_manifests={"pyproject.toml": _PYPROJECT.format(version="1.2.3")},
        **kwargs,  # type: ignore[arg-type]
    )
    assert any(expected in violation for violation in violations), case


def test_metadata_only_proof_rejects_manifest_content_and_version_bypasses() -> None:
    parent = _PYPROJECT.format(version="1.2.2")
    cases = {
        "dependency": parent.replace(
            'name = "demo"', 'name = "demo"\ndependencies = ["unsafe"]'
        ).replace("1.2.2", "1.2.3"),
        "comment": parent.replace('version = "1.2.2"', 'version = "1.2.3"  # changed'),
        "unchanged": parent,
        "decreased": parent.replace("1.2.2", "1.2.1"),
        "invalid": parent.replace("1.2.2", "1.2.3-rc1"),
    }
    for case, source in cases.items():
        violations = _metadata_case(
            parent_manifests={"pyproject.toml": parent},
            source_manifests={"pyproject.toml": source},
        )
        assert violations, case


def test_metadata_only_proof_rejects_added_or_disagreeing_hybrid_manifest() -> None:
    parent = {"CMakeLists.txt": _CMAKE.format(version="1.2.2")}
    source = {
        "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
        "pyproject.toml": _PYPROJECT.format(version="1.2.4"),
    }
    violations = _metadata_case(
        parent_manifests=parent,
        source_manifests=source,
    )
    assert any("adds or removes" in violation for violation in violations)
    assert any("do not agree" in violation for violation in violations)


def test_metadata_only_proof_rejects_disagreeing_parent_hybrid_versions() -> None:
    parent = {
        "CMakeLists.txt": _CMAKE.format(version="1.2.2"),
        "pyproject.toml": _PYPROJECT.format(version="1.2.1"),
    }
    source = {
        "CMakeLists.txt": _CMAKE.format(version="1.2.3"),
        "pyproject.toml": _PYPROJECT.format(version="1.2.3"),
    }
    violations = _metadata_case(
        parent_manifests=parent,
        source_manifests=source,
    )
    assert any("parent versions do not agree" in violation for violation in violations)


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
    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_manifest_texts",
        lambda repository, tree, token: {
            "pyproject.toml": _PYPROJECT.format(version="1.2.3")
        },
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_commit_parent_shas",
        lambda repository, sha, token: [_DEVELOP_SHA],
    )
    monkeypatch.setattr(master_merge_gate, "_master_manifests", lambda *args: {})

    missing = master_merge_gate.validate_event(
        _event(head_ref="release/v1.2.3", body=None), "token"
    )
    assert any("Develop-Source-SHA" in violation for violation in missing)

    valid = master_merge_gate.validate_event(
        _event(
            head_ref="release/v1.2.3",
            body=f"Develop-Source-SHA: {_DEVELOP_SHA}",
        ),
        "token",
    )
    assert not valid
    assert comparisons == [(_DEVELOP_SHA, "develop"), (_DEVELOP_SHA, _HEAD_SHA)]

    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_commit_parent_shas",
        lambda repository, sha, token: [_DEVELOP_SHA, _SOURCE_SHA],
    )
    invalid_shape = master_merge_gate.validate_event(
        _event(
            head_ref="release/v1.2.3",
            body=f"Develop-Source-SHA: {_DEVELOP_SHA}",
        ),
        "token",
    )
    assert any("only parent" in violation for violation in invalid_shape)


def test_release_event_rejects_unrelated_recorded_source(monkeypatch) -> None:
    monkeypatch.setattr(
        master_merge_gate, "_fetch_tree", lambda repository, sha, token: {}
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_is_ancestor",
        lambda repository, ancestor, descendant, token: False,
    )

    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_commit_parent_shas",
        lambda repository, sha, token: [_DEVELOP_SHA],
    )
    monkeypatch.setattr(master_merge_gate, "_master_manifests", lambda *args: {})
    violations = master_merge_gate.validate_event(
        _event(
            head_ref="release/v1.2.3",
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


def test_metadata_parent_field_is_optional_but_never_ambiguous() -> None:
    label = "Release-Metadata-Parent-SHA"
    assert master_merge_gate._release_metadata_parent_sha("") is None
    assert (
        master_merge_gate._release_metadata_parent_sha(f"{label}: {_SOURCE_SHA}")
        == _SOURCE_SHA
    )
    assert master_merge_gate._release_metadata_parent_sha(f"{label}: short") == ""
    assert (
        master_merge_gate._release_metadata_parent_sha(
            f"{label}: {_SOURCE_SHA}\n{label}: {_DEVELOP_SHA}"
        )
        == ""
    )


def test_metadata_parent_binds_validation_provenance_to_proved_parent(
    monkeypatch,
) -> None:
    parent_tree = {
        ".agents/config.yml": ("100644", "blob", "d" * 40),
        "pyproject.toml": ("100644", "blob", "1" * 40),
    }
    develop_tree = {
        ".agents/config.yml": ("100644", "blob", "d" * 40),
        "pyproject.toml": ("100644", "blob", "2" * 40),
    }
    release_tree = {"pyproject.toml": ("100644", "blob", "2" * 40)}
    trees = {
        _SOURCE_SHA: parent_tree,
        _DEVELOP_SHA: develop_tree,
        _HEAD_SHA: release_tree,
    }
    manifests = {
        id(parent_tree): {"pyproject.toml": _PYPROJECT.format(version="1.2.2")},
        id(develop_tree): {"pyproject.toml": _PYPROJECT.format(version="1.2.3")},
        id(release_tree): {"pyproject.toml": _PYPROJECT.format(version="1.2.3")},
    }
    provenance_shas: list[str] = []

    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_tree",
        lambda repository, sha, token: trees[sha],
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_manifest_texts",
        lambda repository, tree, token: manifests[id(tree)],
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_commit_parent_shas",
        lambda repository, sha, token: (
            [_DEVELOP_SHA] if sha == _HEAD_SHA else [_SOURCE_SHA]
        ),
    )
    monkeypatch.setattr(
        master_merge_gate,
        "_is_ancestor",
        lambda repository, ancestor, descendant, token: True,
    )
    monkeypatch.setattr(
        master_merge_gate, "_required_source_checks", lambda: ["validation"]
    )
    monkeypatch.setattr(master_merge_gate, "_master_manifests", lambda *args: {})

    def workflow_runs(repository: str, sha: str, token: str) -> dict[str, object]:
        provenance_shas.append(sha)
        return {
            "total_count": 1,
            "workflow_runs": [
                {
                    "name": "validation",
                    "status": "completed",
                    "conclusion": "success",
                    "event": "push",
                    "head_branch": "develop",
                    "head_sha": sha,
                }
            ],
        }

    monkeypatch.setattr(master_merge_gate, "_fetch_workflow_runs", workflow_runs)
    body = (
        f"Develop-Source-SHA: {_DEVELOP_SHA}\n"
        f"Release-Metadata-Parent-SHA: {_SOURCE_SHA}"
    )
    assert not master_merge_gate.validate_event(
        _event(head_ref="release/v1.2.3", body=body),
        "token",
    )
    assert provenance_shas == [_SOURCE_SHA]


def test_hotfix_event_requires_explicit_validation_tradeoff(monkeypatch) -> None:
    monkeypatch.setattr(
        master_merge_gate, "_fetch_tree", lambda repository, sha, token: {}
    )

    monkeypatch.setattr(
        master_merge_gate,
        "_fetch_manifest_texts",
        lambda repository, tree, token: {
            "pyproject.toml": _PYPROJECT.format(version="1.2.4")
        },
    )

    monkeypatch.setattr(master_merge_gate, "_master_manifests", lambda *args: {})

    missing = master_merge_gate.validate_event(
        _event(head_ref="hotfix/v1.2.4", body=""), "token"
    )
    assert any("Hotfix-Validation-Tradeoff" in violation for violation in missing)

    valid = master_merge_gate.validate_event(
        _event(
            head_ref="hotfix/v1.2.4",
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


def test_manifest_fetch_accepts_wrapped_base64_and_rejects_malformed_data(
    monkeypatch,
) -> None:
    text = _PYPROJECT.format(version="1.2.3")
    encoded = base64.b64encode(text.encode()).decode()
    wrapped = "\n".join(
        encoded[index : index + 12] for index in range(0, len(encoded), 12)
    )
    payload = {"encoding": "base64", "content": wrapped}
    monkeypatch.setattr(
        master_merge_gate,
        "_request_json",
        lambda url, token, label: payload,
    )
    tree = {"pyproject.toml": ("100644", "blob", "1" * 40)}
    assert master_merge_gate._fetch_manifest_texts(
        "example/project", tree, "token"
    ) == {"pyproject.toml": text}

    payload["content"] = "not!base64"
    with pytest.raises(RuntimeError, match="valid UTF-8 base64"):
        master_merge_gate._fetch_manifest_texts("example/project", tree, "token")


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
    assert "'release/**'" not in workflow
    assert "trusted-policy/.github/scripts/master-merge-gate.py" in workflow
    assert "actions/checkout" not in workflow


def _workflow_run(name: str = "validation", **overrides: object) -> dict[str, object]:
    run: dict[str, object] = {
        "name": name,
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "head_branch": "develop",
        "head_sha": _SOURCE_SHA,
    }
    run.update(overrides)
    return run


def _workflow_runs_payload(*runs: dict[str, object]) -> dict[str, object]:
    return {"total_count": len(runs), "workflow_runs": list(runs)}


def _provenance(payload: object, required: list[str]) -> list[str]:
    return master_merge_gate.validate_source_validation_provenance(
        workflow_runs_payload=payload,
        required_workflows=required,
        expected_head_sha=_SOURCE_SHA,
    )


def test_provenance_passes_when_every_required_workflow_succeeded() -> None:
    payload = _workflow_runs_payload(
        _workflow_run("validation"), _workflow_run("gpu-validation")
    )
    assert not _provenance(payload, ["validation"])
    assert not _provenance(payload, ["validation", "gpu-validation"])


def test_provenance_is_inert_without_required_workflows() -> None:
    assert not _provenance(None, [])
    assert not _provenance({"workflow_runs": "broken"}, [])


def test_provenance_rejects_missing_failed_or_running_workflows() -> None:
    assert _provenance(_workflow_runs_payload(), ["validation"])
    assert _provenance(
        _workflow_runs_payload(_workflow_run(conclusion="failure")), ["validation"]
    )
    assert _provenance(
        _workflow_runs_payload(_workflow_run(status="in_progress", conclusion=None)),
        ["validation"],
    )
    assert _provenance(
        _workflow_runs_payload(_workflow_run("other-workflow")), ["validation"]
    )


def test_provenance_rejects_neutral_skipped_and_incomplete_conclusions() -> None:
    """Neutral and skipped are the classic fail-open conclusions; pin them."""
    for conclusion in ("neutral", "skipped", "cancelled", "timed_out"):
        assert _provenance(
            _workflow_runs_payload(_workflow_run(conclusion=conclusion)),
            ["validation"],
        ), conclusion
    # A successful conclusion on a run that is not completed must not count.
    assert _provenance(
        _workflow_runs_payload(_workflow_run(status="queued")), ["validation"]
    )


def test_provenance_binds_evidence_to_push_runs_of_develop_at_the_sha() -> None:
    """A same-named run from another event, branch, or SHA is not evidence."""
    assert _provenance(
        _workflow_runs_payload(_workflow_run(event="pull_request")), ["validation"]
    )
    assert _provenance(
        _workflow_runs_payload(_workflow_run(event="workflow_dispatch")),
        ["validation"],
    )
    assert _provenance(
        _workflow_runs_payload(_workflow_run(head_branch="feat/anything")),
        ["validation"],
    )
    assert _provenance(
        _workflow_runs_payload(_workflow_run(head_sha="d" * 40)), ["validation"]
    )


def test_provenance_fails_closed_on_malformed_or_partial_listings() -> None:
    assert _provenance(None, ["validation"])
    assert _provenance([], ["validation"])
    assert _provenance({}, ["validation"])
    assert _provenance({"workflow_runs": "broken"}, ["validation"])
    partial = _workflow_runs_payload(_workflow_run())
    partial["total_count"] = 2
    violations = _provenance(partial, ["validation"])
    assert violations and "incomplete" in violations[0]


def test_non_master_event_is_ignored_without_fetching_pr_content(monkeypatch) -> None:
    event = _event(head_ref="feat/anything", body=None)
    event["pull_request"]["base"]["ref"] = "release/v1.2.3"  # type: ignore[index]

    def unexpected_fetch(*args: object) -> object:
        raise AssertionError("non-master events must be out of scope")

    monkeypatch.setattr(master_merge_gate, "_fetch_tree", unexpected_fetch)
    assert not master_merge_gate.validate_event(event, "token")


def test_required_source_checks_parses_the_environment_list(monkeypatch) -> None:
    monkeypatch.delenv("REQUIRED_SOURCE_CHECKS", raising=False)
    assert master_merge_gate._required_source_checks() == []
    monkeypatch.setenv("REQUIRED_SOURCE_CHECKS", " validation , gate ,,")
    assert master_merge_gate._required_source_checks() == ["validation", "gate"]


def _run_git(repo, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def _rehearsal_repo(tmp_path, develop_version: str, master_version: str | None):
    """Build a local python-profile repo with sanitised master and full develop."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _run_git(repo, "init", "-b", "master")
    _run_git(repo, "config", "user.email", "test@example.invalid")
    _run_git(repo, "config", "user.name", "Test")
    if master_version is not None:
        (repo / "pyproject.toml").write_text(
            f'[project]\nname = "demo"\nversion = "{master_version}"\n'
        )
        _run_git(repo, "add", "-A")
        _run_git(repo, "commit", "-m", "chore: initial master")
        _run_git(repo, "checkout", "-b", "develop")
    else:
        _run_git(repo, "checkout", "-b", "develop")
    (repo / "pyproject.toml").write_text(
        f'[project]\nname = "demo"\nversion = "{develop_version}"\n'
    )
    (repo / ".agents").mkdir(exist_ok=True)
    (repo / ".agents" / "project.yml").write_text("project_type: python\n")
    (repo / "CLAUDE.md").write_text("# dev\n")
    (repo / "docs" / "changelog").mkdir(parents=True, exist_ok=True)
    (repo / "docs" / "guide.md").write_text("# guide\n")
    (repo / "docs" / "changelog" / "notes.md").write_text("# notes\n")
    (repo / "src").mkdir(exist_ok=True)
    (repo / "src" / "demo.py").write_text("VALUE = 1\n")
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-m", "feat: develop content")
    return repo


def _rehearse(
    repo, master_ref: str = "master", *extra: str
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(_SCRIPT),
            "--rehearse",
            "--repo",
            str(repo),
            "--source-ref",
            "develop",
            "--master-ref",
            master_ref,
            *extra,
        ],
        capture_output=True,
        text=True,
    )


def test_rehearsal_passes_and_derives_names_for_a_promotable_develop(tmp_path) -> None:
    repo = _rehearsal_repo(tmp_path, develop_version="0.2.0", master_version="0.1.0")
    result = _rehearse(repo)
    assert result.returncode == 0, result.stderr
    assert "release/v0.2.0" in result.stdout
    assert "chore/release-v0.2.0" not in result.stdout
    assert "release-v0.2.0" in result.stdout
    assert "Develop-Source-SHA: " in result.stdout


def test_rehearsal_rejects_a_version_that_is_not_strictly_greater(tmp_path) -> None:
    repo = _rehearsal_repo(tmp_path, develop_version="0.1.0", master_version="0.1.0")
    result = _rehearse(repo)
    assert result.returncode == 1
    assert "strictly greater" in result.stderr


def test_rehearsal_rejects_a_pre_release_suffix(tmp_path) -> None:
    repo = _rehearsal_repo(
        tmp_path, develop_version="0.2.0-rc1", master_version="0.1.0"
    )
    result = _rehearse(repo)
    assert result.returncode == 1
    assert "pre-release" in result.stderr


def test_rehearsal_fails_closed_on_an_unresolvable_master_ref(tmp_path) -> None:
    """An unverified monotonicity comparison must never look like a pass."""
    repo = _rehearsal_repo(tmp_path, develop_version="0.2.0", master_version="0.1.0")
    result = _rehearse(repo, master_ref="no-such-ref")
    assert result.returncode == 1
    assert "monotonicity" in result.stderr
    assert "--allow-missing-master-ref" in result.stderr


def test_rehearsal_bootstrap_requires_the_explicit_flag(tmp_path) -> None:
    repo = _rehearsal_repo(tmp_path, develop_version="0.1.0", master_version=None)
    blocked = _rehearse(repo, "no-such-ref")
    assert blocked.returncode == 1
    allowed = _rehearse(repo, "no-such-ref", "--allow-missing-master-ref")
    assert allowed.returncode == 0, allowed.stderr
    assert "release/v0.1.0" in allowed.stdout
    assert "NOT verified" in allowed.stderr


def test_rehearsal_falls_back_to_the_origin_master_ref(tmp_path) -> None:
    """A develop-only clone must still verify monotonicity via origin/master."""
    repo = _rehearsal_repo(tmp_path, develop_version="0.1.0", master_version="0.1.0")
    master_sha = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "master"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    _run_git(repo, "update-ref", "refs/remotes/origin/master", master_sha)
    _run_git(repo, "branch", "-D", "master")
    result = _rehearse(repo)
    assert result.returncode == 1
    assert "strictly greater" in result.stderr


def test_pyproject_normalisation_has_a_python_310_fallback(monkeypatch) -> None:
    parent = '[project]\nname = "demo"\nversion = "1.2.2"  # release\n'
    source = parent.replace("1.2.2", "1.2.3")
    monkeypatch.setitem(sys.modules, "tomllib", None)

    assert master_merge_gate.parse_pyproject_version(source) == "1.2.3"
    assert master_merge_gate._normalise_pyproject_release_version(
        parent
    ) == master_merge_gate._normalise_pyproject_release_version(source)


def test_master_manifest_lookup_requires_a_full_base_sha() -> None:
    with pytest.raises(RuntimeError, match="full master SHA"):
        master_merge_gate._master_manifests(
            {},
            "example/project",
            "release/v1.2.3",
            "token",
        )


def test_rehearsal_fails_cleanly_on_a_missing_source_ref(tmp_path) -> None:
    repo = tmp_path / "empty"
    repo.mkdir()
    _run_git(repo, "init", "-b", "master")
    result = _rehearse(repo)
    assert result.returncode == 1
    assert "REHEARSAL FAILED" in result.stderr


def test_rehearsal_reports_cleanly_on_undecodable_manifest_bytes(tmp_path) -> None:
    """Non-UTF-8 manifest bytes must yield a policy message, not a traceback."""
    repo = _rehearsal_repo(tmp_path, develop_version="0.2.0", master_version="0.1.0")
    (repo / "pyproject.toml").write_bytes(
        b'\xff\xfe[project]\nname = "demo"\nversion = "0.2.0"\n'
    )
    _run_git(repo, "add", "-A")
    _run_git(repo, "commit", "-m", "chore: corrupt manifest")
    result = _rehearse(repo)
    assert result.returncode == 1
    assert "Traceback" not in result.stderr
    assert "REHEARSAL FAILED" in result.stderr
