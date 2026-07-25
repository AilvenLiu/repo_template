#!/usr/bin/env python3
"""Comprehensive parity + compliance sweep across both platforms.

For each (platform, project_type) combination this suite exercises:
  - skill-presence parity vs the canonical capability manifest
  - .agents/bin/agent-* wrapper presence + executability
  - constraint hit rate during /init (bounded-manifest coverage)
  - full roadmap lifecycle (create -> set-focus -> complete-task -> handoff -> complete)
  - structural validator (positive + negative cases)
  - protected-branch detection by .agents/bin/agent-check-constraints

Hit-rate thresholds (computed against the manifest, not hardcoded counts) are
asserted so future drift between manifest and template is caught immediately.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "create-project" / "scripts"))
sys.path.insert(0, str(ROOT / ".agents" / "scripts"))

from capability_audit import _entry_enabled_for_repo  # type: ignore[import-not-found]  # noqa: E402
from init import create_project  # type: ignore[import-not-found]  # noqa: E402

PLATFORMS = ("claude", "codex")
PROJECT_TYPES = ("python", "cpp", "hybrid")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("AGENT_MCP_HEALTH_TIMEOUT_SEC", "1")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


def _force_audit_pass(project_root: Path) -> None:
    for rel in (".agents/session_state.json", ".claude/session_state.json"):
        path = project_root / rel
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        audit = data.get("capability_audit")
        if isinstance(audit, dict):
            audit["passed"] = True
            for entry in audit.get("entries", []):
                if entry.get("required"):
                    entry["available"] = True
        data["capability_audit"] = audit
        path.write_text(json.dumps(data, indent=2))


def _seed_initialized_state(
    project_root: Path, platform: str, project_type: str
) -> None:
    state = {
        "initialized": True,
        "timestamp": datetime.now().isoformat(),
        "platform": platform,
        "project_type": project_type,
        "loaded_constraints": ["common/agentic-team"],
        "active_roadmap": None,
        "capability_audit": {"passed": True, "entries": []},
    }
    for rel in (".agents/session_state.json", ".claude/session_state.json"):
        path = project_root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, indent=2))


def _make_project(tmp_path: Path, project_type: str) -> Path:
    target = tmp_path / f"mock_{project_type}"
    create_project(ROOT, target, project_type)
    _run(["git", "checkout", "-b", "feat/sweep", "-q"], target)
    return target


def _init(project_root: Path, platform: str) -> subprocess.CompletedProcess:
    return _run(
        ["bash", ".agents/bin/agent-init", "--platform", platform], project_root
    )


def _manifest() -> dict:
    return yaml.safe_load((ROOT / ".agents" / "capabilities.yml").read_text())


def _expected_skills(manifest: dict, platform: str, project_root: Path) -> set[str]:
    """Skills that must exist on disk for a generated project of this type.

    The platform argument is informational because both platforms consume the same
    canonical skill in common_requirements.project_skills is expected on both
    platforms (under .agents/skills/<id>/SKILL.md).
    """
    del platform  # parity is now uniform across platforms

    skills: set[str] = set()
    for entry in manifest.get("common_requirements", {}).get("project_skills", []):
        if entry.get("required") and _entry_enabled_for_repo(
            entry, False, project_root
        ):
            skills.add(entry["id"])
    return skills


def _expected_wrappers(manifest: dict, project_root: Path) -> set[str]:
    wrappers: set[str] = set()
    for entry in manifest.get("common_requirements", {}).get("repo_commands", []):
        if entry.get("required") and _entry_enabled_for_repo(
            entry, False, project_root
        ):
            wrappers.add(entry["path"].rsplit("/", 1)[-1])
    return wrappers


# ---------------------------------------------------------------------------
# Skill parity
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
@pytest.mark.parametrize("platform", PLATFORMS)
def test_all_required_skills_present_on_disk(
    tmp_path: Path, platform: str, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    manifest = _manifest()
    expected = _expected_skills(manifest, platform, project)

    # Every required skill must have its canonical body under .agents/skills/.
    agents_skills_dir = project / ".agents" / "skills"
    found_agents = {p.name for p in agents_skills_dir.iterdir() if p.is_dir()}
    missing_ai = expected - found_agents
    assert not missing_ai, (
        f"[{project_type}] Required skill bodies missing under .agents/skills/: "
        f"{sorted(missing_ai)}\n  Found: {sorted(found_agents)}"
    )

    if platform == "claude":
        # Claude additionally requires the slash-command stub for discovery.
        claude_skills_dir = project / ".claude" / "skills"
        found_claude = {p.name for p in claude_skills_dir.iterdir() if p.is_dir()}
        missing_claude = expected - found_claude
        assert not missing_claude, (
            f"[claude/{project_type}] Required Claude stubs missing under "
            f".claude/skills/: {sorted(missing_claude)}"
        )


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_every_agents_skill_has_skill_md_body(
    tmp_path: Path, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    skills_dir = project / ".agents" / "skills"
    assert skills_dir.is_dir(), ".agents/skills/ must exist in generated projects"
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists(), (
            f"[{project_type}] .agents/skills/{skill_dir.name}/SKILL.md missing"
        )
        body = skill_md.read_text()
        assert body.strip(), (
            f"[{project_type}] .agents/skills/{skill_dir.name}/SKILL.md is empty"
        )


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_every_claude_skill_has_frontmatter(tmp_path: Path, project_type: str) -> None:
    project = _make_project(tmp_path, project_type)
    skills_dir = project / ".claude" / "skills"
    for skill_dir in skills_dir.iterdir():
        if not skill_dir.is_dir() or skill_dir.name == "common":
            continue
        skill_md = skill_dir / "SKILL.md"
        assert skill_md.exists(), (
            f"[claude/{project_type}] {skill_dir.name}/SKILL.md missing"
        )
        body = skill_md.read_text()
        assert body.strip(), (
            f"[claude/{project_type}] {skill_dir.name}/SKILL.md is empty"
        )
        # Claude requires frontmatter for slash-command dispatch.
        assert re.search(r"name:\s*\S+", body), (
            f"{skill_dir}/SKILL.md missing frontmatter name"
        )


# ---------------------------------------------------------------------------
# Wrapper presence + executability
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_all_required_wrappers_present_and_executable(
    tmp_path: Path, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    manifest = _manifest()
    expected = _expected_wrappers(manifest, project)

    bin_dir = project / ".agents" / "bin"
    found = {
        p.name for p in bin_dir.iterdir() if p.is_file() and p.name.startswith("agent-")
    }

    missing = expected - found
    assert not missing, f"[{project_type}] Required wrappers missing: {sorted(missing)}"

    for name in expected:
        path = bin_dir / name
        assert os.access(path, os.X_OK), f"[{project_type}] {name} is not executable"


# ---------------------------------------------------------------------------
# Constraint hit rate during /init
# ---------------------------------------------------------------------------


def _expected_constraints(project_type: str) -> set[str]:
    """Constraints that resolve_constraints() should always pick at session start."""

    common = {
        "common/instruction-hierarchy",
        "common/git-workflow",
        "common/session-discipline",
        "common/closure-discipline",
        "common/karpathy-guidelines",
        "common/mcp-integration",
        "common/ascii-only",
        "common/agentic-team",
        "common/service-deployment",
        "common/master-merge-policy",
        "common/github-actions-cicd",
    }
    if project_type == "python":
        common |= {
            "python/dependencies",
            "python/forbidden-practices",
            "python/security",
            "python/error-handling",
        }
    elif project_type == "cpp":
        common |= {
            "cpp/dependencies",
            "cpp/forbidden-practices",
            "cpp/error-handling",
            "cpp/static-analysis",
        }
    else:
        common |= {
            "python/dependencies",
            "python/forbidden-practices",
            "python/security",
            "python/error-handling",
            "cpp/dependencies",
            "cpp/forbidden-practices",
            "cpp/error-handling",
            "cpp/static-analysis",
            "hybrid/ffi-boundary",
            "hybrid/python-cpp-build",
            "hybrid/system-deps",
        }
    return common


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
@pytest.mark.parametrize("platform", PLATFORMS)
def test_constraint_hit_rate_meets_100pct(
    tmp_path: Path, platform: str, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    init = _init(project, platform)
    expected = _expected_constraints(project_type)

    state_path = project / ".agents" / "session_state.json"
    assert state_path.exists(), (
        f"[{platform}/{project_type}] session_state.json missing"
    )
    state = json.loads(state_path.read_text())
    loaded = set(state.get("loaded_constraints", []))

    missing = expected - loaded
    extra = loaded - expected
    hit_rate = len(loaded & expected) / len(expected) if expected else 0.0

    assert not missing, (
        f"[{platform}/{project_type}] hit_rate={hit_rate:.0%} missing={sorted(missing)} "
        f"extra={sorted(extra)}\nstdout-tail:\n" + init.stdout[-1500:]
    )

    for key in expected:
        assert f"[READ] .agents/constraints/{key}.md" in init.stdout, (
            f"[{platform}/{project_type}] constraint {key} missing from /init manifest"
        )
    assert "[CONSTRAINT]" not in init.stdout


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_generated_entrypoints_expose_phase_and_closure_discipline(
    tmp_path: Path, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)

    agents = (project / "AGENTS.md").read_text()
    claude = (project / "CLAUDE.md").read_text()

    for name, text in {"AGENTS.md": agents, "CLAUDE.md": claude}.items():
        assert "closure-discipline.md" in text, f"{name} missing closure discipline"
        assert "roadmap phase" in text.lower(), f"{name} missing roadmap phase wording"
        assert "agent_roadmaps/<phase>" in text, f"{name} uses stale roadmap path token"

    roadmap_skill = (
        project / ".agents" / "skills" / "roadmap" / "SKILL.md"
    ).read_text()
    roadmap_stub = (project / ".claude" / "skills" / "roadmap" / "SKILL.md").read_text()
    roadmap_guide = (
        project
        / ".agents"
        / "skills"
        / "roadmap"
        / "references"
        / "template-compliance.md"
    ).read_text()
    init_skill = (project / ".agents" / "skills" / "init" / "SKILL.md").read_text()
    init_runtime = (project / ".agents" / "scripts" / "session_init.py").read_text()
    init_stub = (project / ".claude" / "skills" / "init" / "SKILL.md").read_text()

    for name, text in {
        ".agents/skills/roadmap/SKILL.md": roadmap_skill,
        ".agents/skills/roadmap/references/template-compliance.md": roadmap_guide,
    }.items():
        assert "--phases" in text, f"{name} missing phase create flag"
        assert "depends_on_phases" in text, f"{name} missing phase dependencies"
        assert "depends_on_steps" not in text, f"{name} still references step schema"
        assert "--steps" not in text, f"{name} still documents legacy create flag"

    assert "common/closure-discipline" in init_runtime
    assert ".agents/bin/agent-init" in init_skill
    assert ".agents/skills/roadmap/SKILL.md" in roadmap_stub
    assert ".agents/skills/init/SKILL.md" in init_stub


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
@pytest.mark.parametrize("platform", PLATFORMS)
def test_session_state_records_platform_and_project_type(
    tmp_path: Path, platform: str, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    _init(project, platform)
    state = json.loads((project / ".agents" / "session_state.json").read_text())
    assert state["platform"] == platform
    assert state["project_type"] == project_type
    assert state["project_profile"]
    assert state["initialized"] is True


# ---------------------------------------------------------------------------
# Roadmap full lifecycle
# ---------------------------------------------------------------------------


def _bootstrap_for_roadmap(tmp_path: Path, project_type: str, platform: str) -> Path:
    project = _make_project(tmp_path, project_type)
    _seed_initialized_state(project, platform, project_type)
    _force_audit_pass(project)
    return project


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
@pytest.mark.parametrize("platform", PLATFORMS)
def test_full_roadmap_lifecycle(
    tmp_path: Path, platform: str, project_type: str
) -> None:
    project = _bootstrap_for_roadmap(tmp_path, project_type, platform)

    create = _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "lifecycle",
            "--phases",
            "1",
            "--phase-names",
            "core",
        ],
        project,
    )
    assert create.returncode == 0, create.stdout + create.stderr

    phase = "phase-0-core"
    phase_dir = project / "agent_roadmaps" / phase
    for name in ("INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"):
        assert (phase_dir / name).exists()

    data = yaml.safe_load((phase_dir / "roadmap.yml").read_text())
    assert data["phase"] == 0
    assert "step" not in data
    assert data["depends_on_phases"] == []

    _run(["git", "checkout", "-b", f"roadmap/{phase}", "-q"], project)

    validate = _run(["bash", ".agents/bin/agent-roadmap", "validate", phase], project)
    assert validate.returncode == 0, validate.stdout + validate.stderr

    check = _run(["bash", ".agents/bin/agent-roadmap", "check"], project)
    assert check.returncode == 0, check.stdout + check.stderr

    status = _run(["bash", ".agents/bin/agent-roadmap", "status"], project)
    assert status.returncode == 0, status.stdout + status.stderr
    assert phase in status.stdout

    # Complete the first two tasks; phase remains active.
    for _ in range(2):
        comp = _run(
            ["bash", ".agents/bin/agent-roadmap", "update", "complete-task"], project
        )
        assert comp.returncode == 0, comp.stdout + comp.stderr

    handoff = _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "handoff",
            "--non-interactive",
            "--work",
            "finished 2 tasks",
            "--next-steps",
            "close out final task",
        ],
        project,
    )
    assert handoff.returncode == 0, handoff.stdout + handoff.stderr
    sessions = list((phase_dir / "sessions").glob("session-*.md"))
    assert sessions, "handoff did not produce a session file"

    # Complete the last task — this auto-marks the phase completed.
    final = _run(
        ["bash", ".agents/bin/agent-roadmap", "update", "complete-task"], project
    )
    assert final.returncode == 0, final.stdout + final.stderr

    assert not phase_dir.exists(), (
        "Final roadmap phase should be deleted after full roadmap completion"
    )
    readme = (project / "agent_roadmaps" / "README.md").read_text()
    assert "No roadmap is active" in readme


# ---------------------------------------------------------------------------
# Roadmap negative cases (structural validator)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "missing_file", ["INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "prompt.md"]
)
def test_validator_flags_each_missing_required_file(
    tmp_path: Path, missing_file: str
) -> None:
    project = _bootstrap_for_roadmap(tmp_path, "python", "claude")
    _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "neg",
            "--phases",
            "1",
            "--phase-names",
            "core",
        ],
        project,
    )
    target = project / "agent_roadmaps" / "phase-0-core" / missing_file
    target.unlink()

    res = _run(
        ["bash", ".agents/bin/agent-roadmap", "validate", "phase-0-core"], project
    )
    assert res.returncode != 0
    assert missing_file in res.stdout
    assert (
        "Missing required phase file" in res.stdout or "Phase Structure" in res.stdout
    )


@pytest.mark.parametrize("victim", ["prompt.md", "INVARIANTS.md"])
def test_validator_flags_authority_order_strip(tmp_path: Path, victim: str) -> None:
    project = _bootstrap_for_roadmap(tmp_path, "python", "claude")
    _run(
        [
            "bash",
            ".agents/bin/agent-roadmap",
            "create",
            "neg",
            "--phases",
            "1",
            "--phase-names",
            "core",
        ],
        project,
    )
    target = project / "agent_roadmaps" / "phase-0-core" / victim
    target.write_text("Just plain prose with no authority order anywhere.\n")
    res = _run(
        ["bash", ".agents/bin/agent-roadmap", "validate", "phase-0-core"], project
    )
    assert res.returncode != 0
    assert "Authority Order" in res.stdout


# ---------------------------------------------------------------------------
# Constraint check (protected branch detection)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_check_constraints_flags_protected_branch(
    tmp_path: Path, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    # The fixture left us on feat/sweep -- switch back to the default protected branch.
    # Modern git defaults to 'main'; fall back to 'master' for older configs.
    r = _run(["git", "checkout", "main", "-q"], project)
    if r.returncode != 0:
        _run(["git", "checkout", "master", "-q"], project)
    res = _run(["bash", ".agents/bin/agent-check-constraints"], project)
    assert res.returncode != 0
    assert "protected branch" in (res.stdout + res.stderr).lower()


@pytest.mark.parametrize("project_type", PROJECT_TYPES)
def test_check_constraints_passes_on_feature_branch(
    tmp_path: Path, project_type: str
) -> None:
    project = _make_project(tmp_path, project_type)
    res = _run(["bash", ".agents/bin/agent-check-constraints"], project)
    assert res.returncode == 0, res.stdout + res.stderr


# ---------------------------------------------------------------------------
# Manifest <-> filesystem cross-check (template, not generated project)
# ---------------------------------------------------------------------------


def test_every_manifest_skill_has_implementation_in_template() -> None:
    """Every manifest skill must have a body under .agents/skills/ (vendor-neutral),
    plus a Claude stub under .claude/skills/ for slash-command dispatch.
    """
    manifest = _manifest()
    skill_ids: set[str] = {
        entry["id"]
        for entry in manifest.get("common_requirements", {}).get("project_skills", [])
    }

    agents_skills = {
        p.name for p in (ROOT / ".agents" / "skills").iterdir() if p.is_dir()
    }
    claude_skills = {
        p.name for p in (ROOT / ".claude" / "skills").iterdir() if p.is_dir()
    }

    for skill_id in skill_ids:
        assert skill_id in agents_skills, (
            f"Manifest declares skill '{skill_id}' but no .agents/skills/{skill_id}/ "
            "directory exists"
        )
        assert skill_id in claude_skills, (
            f"Manifest declares skill '{skill_id}' but no .claude/skills/{skill_id}/ "
            "directory exists"
        )


def test_every_constraint_file_resolves_via_loader() -> None:
    """Every .agents/constraints/**/*.md should be loadable by session_init.load_constraint."""

    sys.path.insert(0, str(ROOT / ".agents" / "scripts"))
    from session_init import load_constraint  # type: ignore[import-not-found]  # noqa: E402

    for md in (ROOT / ".agents" / "constraints").rglob("*.md"):
        if md.name == "README.md":
            continue
        rel = md.relative_to(ROOT / ".agents" / "constraints").with_suffix("")
        body = load_constraint(ROOT, str(rel).replace(os.sep, "/"))
        assert body is not None and body.strip(), f"Constraint {rel} did not load"
