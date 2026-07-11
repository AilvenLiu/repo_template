#!/usr/bin/env python3
"""Aggregate compliance report across platforms x project types.

Writes a machine-readable report for each scenario so regressions are
pin-pointable. The suite exercises:

  - skill presence (rate)
  - skill SKILL.md validity (rate)
  - constraint hit rate during /init
  - wrapper presence + executability (rate)
  - roadmap template authority-order coverage (rate)
  - cross-platform skill parity delta

A final summary test fails if any scenario falls below 100% for items the
manifest declares required. Informational rates are still printed to stdout
so the full picture is visible on every run.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "create-project" / "scripts"))
sys.path.insert(0, str(ROOT / ".ai" / "scripts"))

from capability_audit import _entry_enabled_for_repo  # type: ignore[import-not-found]  # noqa: E402
from init import create_project  # type: ignore[import-not-found]  # noqa: E402

PLATFORMS = ("claude", "codex")
PROJECT_TYPES = ("python", "cpp", "hybrid")


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env.setdefault("AGENT_MCP_HEALTH_TIMEOUT_SEC", "1")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)


@dataclass
class Scenario:
    platform: str
    project_type: str
    rates: dict[str, tuple[int, int]] = field(default_factory=dict)
    misses: dict[str, list[str]] = field(default_factory=dict)

    def add(self, name: str, hit: set[str], total: set[str]) -> None:
        self.rates[name] = (len(hit & total), len(total))
        missing = sorted(total - hit)
        if missing:
            self.misses[name] = missing

    def summary(self) -> str:
        lines = [f"[{self.platform}/{self.project_type}]"]
        for name, (hit, total) in self.rates.items():
            pct = (hit / total * 100) if total else 100.0
            status = "OK " if hit == total else "MISS"
            lines.append(f"  {status} {name}: {hit}/{total} ({pct:.0f}%)")
            if name in self.misses:
                lines.append(f"       missing: {self.misses[name]}")
        return "\n".join(lines)


def _manifest() -> dict:
    return yaml.safe_load((ROOT / ".ai" / "capabilities.yml").read_text())


def _expected_skills(manifest: dict, platform: str, project_root: Path) -> set[str]:
    skills: set[str] = set()
    for entry in manifest.get("common_requirements", {}).get("project_skills", []):
        if entry.get("required") and _entry_enabled_for_repo(
            entry, False, project_root
        ):
            skills.add(entry["id"])
    if platform == "codex":
        for entry in (
            manifest.get("platform_requirements", {})
            .get("codex", {})
            .get("codex_skills", [])
        ):
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


def _expected_constraints(project_type: str) -> set[str]:
    common = {
        "common/instruction-hierarchy",
        "common/git-workflow",
        "common/session-discipline",
            "common/closure-discipline",
        "common/karpathy-guidelines",
        "common/mcp-integration",
        "common/ascii-only",
        "common/agentic-team",
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


@pytest.fixture(scope="module")
def compliance(tmp_path_factory) -> list[Scenario]:
    scenarios: list[Scenario] = []
    manifest = _manifest()

    for platform in PLATFORMS:
        for project_type in PROJECT_TYPES:
            tmp = tmp_path_factory.mktemp(f"{platform}_{project_type}")
            target = tmp / "proj"
            create_project(ROOT, target, project_type)
            _run(["git", "checkout", "-b", "feat/report", "-q"], target)

            scenario = Scenario(platform=platform, project_type=project_type)

            # Skill body presence (canonical, vendor-neutral location).
            ai_skills_dir = target / ".ai" / "skills"
            on_disk = {p.name for p in ai_skills_dir.iterdir() if p.is_dir()}
            expected_skills = _expected_skills(manifest, platform, target)
            scenario.add("skills_present", on_disk, expected_skills)

            # Skill SKILL.md validity
            valid_skill_md = {
                p.name
                for p in ai_skills_dir.iterdir()
                if p.is_dir()
                and (p / "SKILL.md").exists()
                and (p / "SKILL.md").read_text().strip()
            }
            scenario.add("skill_md_valid", valid_skill_md, expected_skills)

            # Claude additionally requires a frontmatter stub for each skill.
            if platform == "claude":
                claude_skills_dir = target / ".claude" / "skills"
                claude_stubs = {
                    p.name
                    for p in claude_skills_dir.iterdir()
                    if p.is_dir() and (p / "SKILL.md").exists()
                }
                scenario.add("claude_stubs_present", claude_stubs, expected_skills)

            # Wrappers
            wrappers_expected = _expected_wrappers(manifest, target)
            wrappers_present = {
                p.name
                for p in (target / ".ai" / "bin").iterdir()
                if p.is_file() and os.access(p, os.X_OK) and p.name.startswith("agent-")
            }
            scenario.add("wrappers_executable", wrappers_present, wrappers_expected)

            # Constraint hit rate via /init
            init = _run(["bash", ".ai/bin/agent-init", "--platform", platform], target)
            state_path = target / ".ai" / "session_state.json"
            loaded = set(
                json.loads(state_path.read_text()).get("loaded_constraints", [])
            )
            expected_constraints = _expected_constraints(project_type)
            scenario.add("constraints_loaded", loaded, expected_constraints)

            manifested = {
                key
                for key in expected_constraints
                if f"[READ] .ai/constraints/{key}.md" in init.stdout
            }
            scenario.add("constraint_manifest_printed", manifested, expected_constraints)

            scenarios.append(scenario)

    # Template-level authority-order coverage (shared across scenarios)
    template_dir = ROOT / ".ai" / "scripts" / "roadmap" / "templates"
    tokens = {"INVARIANTS.md", "ROADMAP.md", "roadmap.yml", "sessions", "prompt.md"}
    for target_file in ("prompt.md", "INVARIANTS.md", "ROADMAP.md"):
        body = (template_dir / target_file).read_text()
        hits = {t for t in tokens if t in body}
        for scenario in scenarios:
            scenario.add(f"template_{target_file}_tokens", hits, tokens)

    return scenarios


def test_report_prints_and_every_required_rate_is_100pct(
    compliance: list[Scenario],
) -> None:
    print("\n" + "=" * 70)
    print("DUAL-PLATFORM COMPLIANCE REPORT")
    print("=" * 70)
    for scenario in compliance:
        print(scenario.summary())
    print("=" * 70)

    offenders = []
    for scenario in compliance:
        for name, (hit, total) in scenario.rates.items():
            if total == 0:
                continue
            if hit != total:
                offenders.append(
                    f"{scenario.platform}/{scenario.project_type}:{name} "
                    f"({hit}/{total}); missing={scenario.misses.get(name, [])}"
                )
    assert not offenders, "Compliance gaps detected:\n  - " + "\n  - ".join(offenders)


def test_skill_parity_between_ai_skills_and_claude_stubs() -> None:
    """Every .ai/skills/<name>/ must have a matching .claude/skills/<name>/ stub
    (and vice versa, except for the template-only create-project + the Claude
    'common' utility folder).
    """
    ai_skills = {p.name for p in (ROOT / ".ai" / "skills").iterdir() if p.is_dir()}
    claude_skills = {
        p.name for p in (ROOT / ".claude" / "skills").iterdir() if p.is_dir()
    }

    # Known, documented asymmetries:
    # - 'create-project' is a template-only Claude skill; no .ai/skills body.
    # - 'common' holds shared utility code, not a user-facing skill.
    claude_only_allowed = {"create-project", "common"}
    claude_minus_ai = claude_skills - ai_skills - claude_only_allowed
    ai_minus_claude = ai_skills - claude_skills

    assert not claude_minus_ai, (
        f"Claude skills with no .ai/skills body: {sorted(claude_minus_ai)}"
    )
    assert not ai_minus_claude, (
        f".ai/skills entries with no Claude stub: {sorted(ai_minus_claude)}"
    )
