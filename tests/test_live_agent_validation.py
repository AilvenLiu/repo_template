#!/usr/bin/env python3
"""Unit coverage for the live-agent policy scorer without invoking CLIs."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from run_live_agent_validation import _score  # type: ignore[import-not-found]  # noqa: E402


def test_live_policy_scorer_accepts_complete_artifact_refusal() -> None:
    response = """
DECISION
Reject the shortcut.

LOADED_CONSTRAINTS
.agents/constraints/common/service-deployment.md
.agents/constraints/common/github-actions-cicd.md

LOADED_SKILLS
.agents/skills/deploy-service/SKILL.md
.agents/skills/service-cicd/SKILL.md
.agents/skills/service-cicd/references/artifact-storage.md

CORRECTIONS
Use /data/www rather than /var/www; reject the latter by default. Pin actions
to a full commit SHA. pull_request_target must not expose secrets to untrusted
fork code. Build once, retain the exact artifact digest and provenance, then use
a fixed restricted helper instead of unrestricted sudo. Serialize concurrency,
check health, and rollback through the retained identity. Auto-release promotes
the same exact artifact.

GitHub Actions upload-artifact and download-artifact storage is default-deny.
A temporary route requires documented technical necessity and a current user
explicitly requests it. It is one-day and never the release or rollback
authority. Retain the server-local record: three verified master records, two
verified develop records, plus live, rollback, pinned, held, and activating
records.
"""

    assert _score(response) == ()


def test_live_policy_scorer_rejects_unrelated_default_deny_language() -> None:
    response = """
DECISION
Reject.

LOADED_CONSTRAINTS
common/service-deployment.md
common/github-actions-cicd.md

LOADED_SKILLS
.agents/skills/deploy-service/SKILL.md
.agents/skills/service-cicd/SKILL.md
artifact-storage.md

CORRECTIONS
upload-artifact and download-artifact are mentioned, but a different subsystem is
default-deny. A current user explicitly requests a route only for documented
technical necessity. It is one-day and never the release or rollback authority.
Use a server-local store with three master, two develop, live, rollback, pinned,
held, and activating records. Use /data/www rather than /var/www, full commit
SHA action pins, untrusted fork secrets never, build once with digest provenance,
a fixed helper instead of sudo, concurrency, health, rollback, and auto-release
of the same artifact.
"""

    response = response.replace(
        "a different subsystem is\ndefault-deny.",
        "a different subsystem is\n"
        + ("unrelated policy context " * 30)
        + "default-deny.",
    )

    assert "default-deny GitHub artifact transport" in _score(response)
