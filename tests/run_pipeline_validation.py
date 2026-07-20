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

    clean = run(["bash", ".agents/bin/agent-check-constraints"], project)
    if clean.returncode != 0:
        raise AssertionError(
            f"{scenario.profile}/{scenario.platform} clean gate failed:\n"
            f"{clean.stdout}{clean.stderr}"
        )

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
        Scenario("python", platform, 14, PYTHON_CATEGORIES)
        for platform in ("claude", "codex")
    ]
    scenarios += [
        Scenario("cpp", platform, 14, CPP_CATEGORIES)
        for platform in ("claude", "codex")
    ]
    scenarios += [
        Scenario("hybrid", platform, 22, PYTHON_CATEGORIES | CPP_CATEGORIES)
        for platform in ("claude", "codex")
    ]

    with tempfile.TemporaryDirectory(prefix="repo-template-pipeline-") as tmp:
        base = Path(tmp)
        for scenario in scenarios:
            print(validate_scenario(base, scenario))

    print("Pipeline validation passed: 6/6 platform/profile scenarios.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
