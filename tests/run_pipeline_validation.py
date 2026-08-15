#!/usr/bin/env python3
"""Standalone dual-platform/profile pipeline validation without pytest."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "skills" / "create-project" / "scripts"))

from init import create_project  # type: ignore[import-not-found]  # noqa: E402


@dataclass(frozen=True)
class Scenario:
    profile: str
    platform: str
    constraint_count: int
    expected_categories: frozenset[str]


PYTHON_CATEGORIES = frozenset(
    {
        "hardcoded-secret",
        "mutable-default",
        "bare-except",
        "eval-exec",
        "pip-install",
        "shell-true-user-input",
    }
)
CPP_CATEGORIES = frozenset(
    {"raw-new", "raw-delete", "c-style-cast", "cuda-error-ignored"}
)


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def seed_python(project: Path) -> None:
    target = project / "src" / "validation_fixture.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        textwrap.dedent(
            """
            API_KEY = "sk-live-ABCDEFGHIJKLMNOP1234567890"

            def parse(values=[]):
                try:
                    return eval(values[0])
                except:
                    return None

            def install():
                import subprocess
                subprocess.run("pip install requests", shell=True)
            """
        ).strip()
        + "\n"
    )


def seed_cpp(project: Path) -> None:
    source = project / "src" / "validation_fixture.cpp"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(
        textwrap.dedent(
            """
            #include <cuda_runtime.h>

            void run() {
                int* value = new int(1);
                int narrowed = (int) 3.14;
                delete value;
                cudaMalloc(nullptr, 1024);
            }
            """
        ).strip()
        + "\n"
    )


_PROBE_SHA = "0123456789abcdef0123456789abcdef01234567"
_PROBE_SOURCE_SHA = "1" * 40
_PROBE_DIGEST = "sha256:" + "2" * 64


def _artifact_probe_workflow(action_ref: str) -> str:
    return textwrap.dedent(
        f"""
        name: temporary artifact-transfer probe
        on: workflow_dispatch
        jobs:
          build:
            runs-on: ubuntu-latest
            steps:
              - uses: actions/upload-artifact@{action_ref}
                with:
                  name: handoff
                  path: dist
                  retention-days: 1
          consume:
            needs: build
            runs-on: ubuntu-latest
            steps:
              - uses: actions/download-artifact@{action_ref}
                with:
                  name: handoff
        """
    ).lstrip()


def _probe_action_line(workflow: Path, surface: str) -> int:
    needle = f"uses: {surface}@"
    for number, line in enumerate(workflow.read_text().splitlines(), start=1):
        if needle in line:
            return number
    raise AssertionError(f"missing {surface} in {workflow}")


def _expect_artifact_block(project: Path, scenario: Scenario, case: str) -> None:
    blocked = run(["bash", ".agents/bin/agent-check-constraints"], project)
    output = blocked.stdout + blocked.stderr
    if blocked.returncode == 0 or "GitHub Artifact Storage" not in output:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: {case} was not blocked:\n{output}"
        )


def validate_github_artifact_guard(project: Path, scenario: Scenario) -> None:
    """Prove default-deny blocking and exact-record acceptance in a real project."""
    workflow = project / ".github" / "workflows" / "artifact-transfer.yml"
    exception_record = project / ".agents" / "github-artifact-exceptions.json"

    # 1. An unapproved route is blocked with no exception record at all.
    workflow.write_text(_artifact_probe_workflow(_PROBE_SHA), encoding="utf-8")
    _expect_artifact_block(project, scenario, "unapproved artifact route")

    upload_line = _probe_action_line(workflow, "actions/upload-artifact")
    download_line = _probe_action_line(workflow, "actions/download-artifact")

    def exception(surface: str, action_line: int) -> dict[str, object]:
        record: dict[str, object] = {
            "workflow": ".github/workflows/artifact-transfer.yml",
            "surface": surface,
            "action_line": action_line,
            "artifact_name": "handoff",
            "technical_necessity": (
                "Synthetic guard probe: local storage and direct transfer unavailable."
            ),
            "user_request": (
                "Synthetic test user explicitly requested this one-day transfer."
            ),
            "request_reference": "Pipeline validation probe: temporary transfer only.",
            "producer": "build",
            "consumer": "consume",
            "environment": "test",
            "contents": "Non-secret digest-bound test archive.",
            "source_sha": _PROBE_SOURCE_SHA,
            "digest": _PROBE_DIGEST,
            "size_limit_bytes": 1048576,
            "retention_days": 1,
            "non_secret": True,
            "release_or_rollback_authority": False,
            "reviewed": True,
        }
        if surface == "actions/download-artifact":
            record["producer_upload_line"] = upload_line
        return record

    exceptions = [
        exception("actions/upload-artifact", upload_line),
        exception("actions/download-artifact", download_line),
    ]

    def write_exceptions(records: list[dict[str, object]]) -> None:
        exception_record.write_text(
            json.dumps({"version": 1, "exceptions": records}, indent=2) + "\n",
            encoding="utf-8",
        )

    # 2. A complete, line-bound, one-day exception pair is accepted.
    write_exceptions(exceptions)
    permitted = run(["bash", ".agents/bin/agent-check-constraints"], project)
    if permitted.returncode != 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: complete one-day exception "
            f"was not accepted:\n{permitted.stdout}{permitted.stderr}"
        )

    # 3. An abbreviated action pin is still blocked even with that record.
    workflow.write_text(_artifact_probe_workflow("0123456789ab"), encoding="utf-8")
    _expect_artifact_block(project, scenario, "abbreviated action pin")

    # 4. A record that no longer binds its action line is blocked.
    workflow.write_text(_artifact_probe_workflow(_PROBE_SHA), encoding="utf-8")
    write_exceptions(
        [
            record | {"action_line": record["action_line"] + 100}  # type: ignore[operator]
            for record in exceptions
        ]
    )
    _expect_artifact_block(project, scenario, "stale action-line binding")

    # Leave the project clean so later gates test only their own seeded state.
    workflow.unlink()
    exception_record.unlink()
    clean = run(["bash", ".agents/bin/agent-check-constraints"], project)
    if clean.returncode != 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: project not clean after the "
            f"artifact guard probe:\n{clean.stdout}{clean.stderr}"
        )


def validate_scenario(base: Path, scenario: Scenario) -> str:
    project = base / f"{scenario.profile}-{scenario.platform}"
    create_project(ROOT, project, scenario.profile)

    branch = run(["git", "switch", "-c", "feat/pipeline-validation"], project)
    if branch.returncode != 0:
        raise AssertionError(branch.stdout + branch.stderr)

    init_result = run(
        ["bash", ".agents/bin/agent-init", "--platform", scenario.platform], project
    )
    if init_result.returncode != 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform} init failed:\n"
            f"{init_result.stdout}{init_result.stderr}"
        )

    state = json.loads((project / ".agents/session_state.json").read_text())
    manifest = state.get("loaded_constraints", [])
    if state.get("platform") != scenario.platform:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: wrong platform in session state"
        )
    if state.get("project_type") != scenario.profile:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: wrong profile in session state"
        )
    required_constraints = {
        "common/service-deployment",
        "common/github-actions-cicd",
    }
    if not required_constraints <= set(manifest):
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: service constraints missing "
            f"from {manifest}"
        )
    if len(manifest) != scenario.constraint_count:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: expected "
            f"{scenario.constraint_count} constraints, got {len(manifest)}"
        )
    if not state.get("capability_audit", {}).get("passed"):
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: audit not passed"
        )

    verify = run(
        [
            "python3",
            ".agents/scripts/common/verify_skills.py",
            "--platform",
            scenario.platform,
        ],
        project,
    )
    if verify.returncode != 0:
        raise AssertionError(verify.stdout + verify.stderr)

    for policy_file in (
        project / ".agents/constraints/common/github-actions-cicd.md",
        project / ".agents/skills/service-cicd/references/artifact-storage.md",
    ):
        body = policy_file.read_text().lower()
        for phrase in (
            "default-deny",
            "actions/upload-artifact",
            "actions/download-artifact",
            "documented technical necessity",
            "current user",
            "one day",
            "release or rollback authority",
        ):
            if phrase not in body:
                raise AssertionError(
                    f"{scenario.profile}/{scenario.platform}: artifact policy "
                    f"missing {phrase!r} in {policy_file.relative_to(project)}"
                )

    for entrypoint in ("AGENTS.md", "CLAUDE.md"):
        body = " ".join((project / entrypoint).read_text().split())
        for phrase in (
            "default-deny",
            "documented technical limitation",
            "current user explicitly",
            "one-day, non-rollback transfer",
            "bounded local store",
        ):
            if phrase not in body:
                raise AssertionError(
                    f"{scenario.profile}/{scenario.platform}: artifact policy "
                    f"missing {phrase!r} in {entrypoint}"
                )
    clean = run(["bash", ".agents/bin/agent-check-constraints"], project)
    if clean.returncode != 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform} clean gate failed:\n"
            f"{clean.stdout}{clean.stderr}"
        )

    validate_github_artifact_guard(project, scenario)

    if scenario.profile in {"python", "hybrid"}:
        seed_python(project)
    if scenario.profile in {"cpp", "hybrid"}:
        seed_cpp(project)

    scan = run(
        [
            "python3",
            ".agents/scripts/forbidden_patterns.py",
            "--project-type",
            "auto",
            "--json",
        ],
        project,
    )
    payload = json.loads(scan.stdout)
    detected = {finding["category"] for finding in payload["findings"]}
    missing = scenario.expected_categories - detected
    if missing:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: missed {sorted(missing)}; "
            f"detected {sorted(detected)}"
        )

    dirty = run(["bash", ".agents/bin/agent-check-constraints"], project)
    if dirty.returncode == 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform}: dirty gate unexpectedly passed"
        )

    return (
        f"{scenario.profile}/{scenario.platform}: init+load+clean+seeded enforcement "
        f"passed ({len(manifest)} constraints, {len(scenario.expected_categories)} "
        "seed categories)"
    )


def main() -> int:
    scenarios = [
        Scenario("python", platform, 15, PYTHON_CATEGORIES)
        for platform in ("claude", "codex")
    ]
    scenarios += [
        Scenario("cpp", platform, 15, CPP_CATEGORIES)
        for platform in ("claude", "codex")
    ]
    scenarios += [
        Scenario("hybrid", platform, 23, PYTHON_CATEGORIES | CPP_CATEGORIES)
        for platform in ("claude", "codex")
    ]

    with tempfile.TemporaryDirectory(prefix="agent-foundry-pipeline-") as tmp:
        base = Path(tmp)
        for scenario in scenarios:
            print(validate_scenario(base, scenario))

    print("Pipeline validation passed: 6/6 platform/profile scenarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
