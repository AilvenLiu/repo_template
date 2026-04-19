#!/usr/bin/env python3
"""Real-scenario E2E: build mock realistic projects, seed known violations,
run the agent toolchain, and measure constraint-compliance effectiveness.

Effectiveness is (detected / seeded) per violation category, plus skill
invocation coverage. A final aggregated report is printed and asserted
against the manifest-derived target thresholds.

Each test generates a real project via create-project, lays down realistic
source files (with or without seeded violations), runs the tooling
end-to-end, and inspects exit codes + findings output.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "skills" / "create-project" / "scripts"))
sys.path.insert(0, str(ROOT / ".ai" / "tools"))

from init import create_project  # noqa: E402


def _run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=os.environ.copy())


def _force_audit_pass(project_root: Path) -> None:
    for rel in (".ai/session_state.json", ".claude/session_state.json"):
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


def _bootstrap(tmp_path: Path, project_type: str, platform: str) -> Path:
    target = tmp_path / f"real_{project_type}"
    create_project(ROOT, target, project_type)
    _run(["git", "checkout", "-b", "feat/real-scenario", "-q"], target)
    _run(["bash", "bin/agent-init", "--platform", platform], target)
    _force_audit_pass(target)
    return target


# ---------------------------------------------------------------------------
# Realistic Python project seeding
# ---------------------------------------------------------------------------


def _seed_realistic_python_clean(project: Path) -> None:
    """Drop in a realistic Poetry project skeleton with NO seeded violations."""

    (project / "src" / "service").mkdir(parents=True, exist_ok=True)
    (project / "src" / "service" / "__init__.py").write_text("")
    (project / "src" / "service" / "api.py").write_text(
        textwrap.dedent(
            '''
            """Tiny service facade."""
            from __future__ import annotations

            from typing import Iterable, Optional


            def normalise(values: Optional[Iterable[str]] = None) -> list[str]:
                if values is None:
                    values = []
                return [v.strip().lower() for v in values if v]


            def divide(a: float, b: float) -> float:
                if b == 0:
                    raise ValueError("b must be non-zero")
                return a / b
            '''
        ).strip()
        + "\n"
    )
    (project / "pyproject.toml").write_text(
        textwrap.dedent(
            """
            [tool.poetry]
            name = "service"
            version = "0.1.0"
            description = "example"
            authors = ["Team <team@example.com>"]

            [tool.poetry.dependencies]
            python = "^3.10"

            [build-system]
            requires = ["poetry-core"]
            build-backend = "poetry.core.masonry.api"
            """
        ).strip()
    )
    # Minimal lock file stub so pre-commit's Poetry-managed check succeeds.
    (project / "poetry.lock").write_text("# poetry lock placeholder\n")


def _seed_realistic_python_dirty(project: Path) -> dict[str, int]:
    """Drop the clean skeleton then inject one violation per category.

    Returns a dict of category -> number of seeded occurrences.
    """

    _seed_realistic_python_clean(project)

    dirty = project / "src" / "service" / "legacy.py"
    dirty.write_text(
        textwrap.dedent(
            '''
            """Legacy shim with intentional violations (for tooling tests)."""

            API_KEY = "sk-live-ABCDEFGHIJKLMNOP1234567890"   # hardcoded-secret

            def parse(raw=[]):                                # mutable-default
                try:
                    return int(raw[0])
                except:                                       # bare-except
                    return None


            def run(expr):
                return eval(expr)                             # eval-exec


            def install_deps():
                import subprocess
                subprocess.run("pip install requests", shell=True)   # pip-install + shell-true
            '''
        ).strip()
        + "\n"
    )

    return {
        "hardcoded-secret": 1,
        "mutable-default": 1,
        "bare-except": 1,
        "eval-exec": 1,
        "pip-install": 1,
        "shell-true-user-input": 1,
    }


# ---------------------------------------------------------------------------
# Realistic C++ project seeding
# ---------------------------------------------------------------------------


def _seed_realistic_cpp_clean(project: Path) -> None:
    (project / "src").mkdir(parents=True, exist_ok=True)
    (project / "include").mkdir(parents=True, exist_ok=True)
    (project / "src" / "main.cpp").write_text(
        textwrap.dedent(
            """
            #include <memory>
            #include <string>
            #include <vector>

            namespace service {

            struct Node {
                std::string name;
            };

            std::unique_ptr<Node> make_node(const std::string& name) {
                auto node = std::make_unique<Node>();
                node->name = name;
                return node;
            }

            }  // namespace service
            """
        ).strip()
        + "\n"
    )
    (project / "conanfile.txt").write_text("[requires]\nfmt/10.1.1\n")


def _seed_realistic_cpp_dirty(project: Path) -> dict[str, int]:
    _seed_realistic_cpp_clean(project)

    (project / "src" / "legacy.cpp").write_text(
        textwrap.dedent(
            """
            #include <cstdio>

            struct Node { int value; };

            void run() {
                Node* n = new Node();          // raw-new
                int x = (int) 3.14;            // c-style-cast
                delete n;                       // raw-delete
            }
            """
        ).strip()
        + "\n"
    )
    (project / "src" / "cuda_kernel.cu").write_text(
        textwrap.dedent(
            """
            #include <cuda_runtime.h>

            void launch() {
                cudaMalloc(nullptr, 1024);      // cuda-error-ignored
            }
            """
        ).strip()
        + "\n"
    )

    return {
        "raw-new": 1,
        "c-style-cast": 1,
        "raw-delete": 1,
        "cuda-error-ignored": 1,
    }


# ---------------------------------------------------------------------------
# Effectiveness measurement
# ---------------------------------------------------------------------------


@dataclass
class Effectiveness:
    scenario: str
    seeded: dict[str, int]
    detected: dict[str, int] = field(default_factory=dict)

    @property
    def total_seeded(self) -> int:
        return sum(self.seeded.values())

    @property
    def total_detected(self) -> int:
        return sum(min(self.detected.get(k, 0), self.seeded[k]) for k in self.seeded)

    @property
    def rate(self) -> float:
        return self.total_detected / self.total_seeded if self.total_seeded else 1.0

    def summary(self) -> str:
        lines = [f"[{self.scenario}] seeded={self.total_seeded} detected={self.total_detected} ({self.rate:.0%})"]
        for cat, count in self.seeded.items():
            hit = self.detected.get(cat, 0)
            status = "OK " if hit >= count else "MISS"
            lines.append(f"  {status} {cat}: {hit}/{count}")
        return "\n".join(lines)


def _findings_for(project: Path) -> list[dict]:
    res = _run(
        [
            "bash",
            "bin/agent-check-constraints",
            "--skip-forbidden-scan",  # we'll run forbidden_patterns explicitly w/ --json
        ],
        project,
    )
    assert res.returncode == 0 or "protected" in (res.stdout + res.stderr).lower(), (
        res.stdout + res.stderr
    )
    scan = _run(
        [
            "python3",
            str(project / ".ai" / "tools" / "forbidden_patterns.py"),
            "--project-type",
            "auto",
            "--json",
        ],
        project,
    )
    payload = json.loads(scan.stdout)
    return payload["findings"]


# ---------------------------------------------------------------------------
# Tests: clean projects should produce zero findings
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_clean_python_project_produces_no_findings(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "python", platform)
    _seed_realistic_python_clean(project)
    findings = _findings_for(project)
    assert findings == [], f"False-positive findings on clean project: {findings}"


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_clean_cpp_project_produces_no_findings(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "cpp", platform)
    _seed_realistic_cpp_clean(project)
    findings = _findings_for(project)
    assert findings == [], f"False-positive findings on clean project: {findings}"


# ---------------------------------------------------------------------------
# Tests: seeded violations must be detected (effectiveness >= 100%)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_seeded_python_violations_are_all_detected(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "python", platform)
    seeded = _seed_realistic_python_dirty(project)

    findings = _findings_for(project)
    detected: dict[str, int] = {}
    for f in findings:
        detected[f["category"]] = detected.get(f["category"], 0) + 1

    eff = Effectiveness(f"python/{platform}", seeded, detected)
    print("\n" + eff.summary())
    assert eff.rate >= 1.0, (
        f"Python detection rate {eff.rate:.0%} below 100%:\n{eff.summary()}\n\n"
        f"findings:\n{json.dumps(findings, indent=2)}"
    )


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_seeded_cpp_violations_are_all_detected(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "cpp", platform)
    seeded = _seed_realistic_cpp_dirty(project)

    findings = _findings_for(project)
    detected: dict[str, int] = {}
    for f in findings:
        detected[f["category"]] = detected.get(f["category"], 0) + 1

    eff = Effectiveness(f"cpp/{platform}", seeded, detected)
    print("\n" + eff.summary())
    assert eff.rate >= 1.0, (
        f"C++ detection rate {eff.rate:.0%} below 100%:\n{eff.summary()}\n\n"
        f"findings:\n{json.dumps(findings, indent=2)}"
    )


# ---------------------------------------------------------------------------
# End-to-end through the wrapper (user-facing path)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_check_constraints_wrapper_fails_on_seeded_python_repo(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "python", platform)
    _seed_realistic_python_dirty(project)

    res = _run(["bash", "bin/agent-check-constraints"], project)
    assert res.returncode != 0, (
        "bin/agent-check-constraints should surface seeded violations via forbidden_patterns.\n"
        + res.stdout
    )
    combined = res.stdout + res.stderr
    for cat in ("bare-except", "eval-exec", "hardcoded-secret", "mutable-default", "pip-install"):
        assert cat in combined, f"{cat} not surfaced by wrapper output"


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_check_constraints_wrapper_fails_on_seeded_cpp_repo(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "cpp", platform)
    _seed_realistic_cpp_dirty(project)

    res = _run(["bash", "bin/agent-check-constraints"], project)
    assert res.returncode != 0
    combined = res.stdout + res.stderr
    for cat in ("raw-new", "raw-delete", "c-style-cast", "cuda-error-ignored"):
        assert cat in combined, f"{cat} not surfaced by wrapper output"


# ---------------------------------------------------------------------------
# Suppression pragma works (so tests/fixtures can opt out intentionally)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("platform", ["claude", "codex"])
def test_ai_allow_pragma_suppresses_findings(tmp_path: Path, platform: str) -> None:
    project = _bootstrap(tmp_path, "python", platform)
    _seed_realistic_python_clean(project)

    (project / "src" / "service" / "fixture.py").write_text(
        textwrap.dedent(
            '''
            """Deliberate fixture: exercises error path in tests."""

            def parse(raw):
                try:
                    return int(raw)
                except:  # ai-allow: bare-except
                    return None
            '''
        ).strip()
        + "\n"
    )

    findings = _findings_for(project)
    assert not any(f["category"] == "bare-except" for f in findings), findings


# ---------------------------------------------------------------------------
# Aggregate report across all scenarios (printed + asserted)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def effectiveness_matrix(tmp_path_factory) -> list[Effectiveness]:
    results: list[Effectiveness] = []
    for platform in ("claude", "codex"):
        for project_type, seeder, clean in (
            ("python", _seed_realistic_python_dirty, _seed_realistic_python_clean),
            ("cpp", _seed_realistic_cpp_dirty, _seed_realistic_cpp_clean),
        ):
            tmp = tmp_path_factory.mktemp(f"eff_{platform}_{project_type}")
            target = tmp / "proj"
            create_project(ROOT, target, project_type)
            _run(["git", "checkout", "-b", "feat/eff", "-q"], target)
            _run(["bash", "bin/agent-init", "--platform", platform], target)
            _force_audit_pass(target)
            seeded = seeder(target)
            findings = _findings_for(target)
            detected: dict[str, int] = {}
            for f in findings:
                detected[f["category"]] = detected.get(f["category"], 0) + 1
            results.append(
                Effectiveness(
                    scenario=f"{project_type}/{platform}",
                    seeded=seeded,
                    detected=detected,
                )
            )
    return results


def test_effectiveness_report(effectiveness_matrix: list[Effectiveness]) -> None:
    print("\n" + "=" * 70)
    print("CONSTRAINT-COMPLIANCE EFFECTIVENESS REPORT")
    print("(dirty realistic projects; detection / seeded)")
    print("=" * 70)
    for eff in effectiveness_matrix:
        print(eff.summary())
    print("=" * 70)

    offenders = [eff for eff in effectiveness_matrix if eff.rate < 1.0]
    assert not offenders, "Some scenarios detected < 100% of seeded violations"
