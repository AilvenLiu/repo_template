#!/usr/bin/env python3
"""Instruction-content consistency regression tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".agents" / "scripts" / "common"))

from validate_instruction_content import scan  # type: ignore[import-not-found]  # noqa: E402


def test_repository_instruction_content_is_consistent() -> None:
    assert scan(ROOT) == []


def test_instruction_scan_detects_copyable_policy_breakers(tmp_path: Path) -> None:
    skill = tmp_path / ".agents" / "skills" / "unsafe" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        """# Unsafe examples

```bash
pip install requests
poetry add flask
python -m venv .venv
ssh -o StrictHostKeyChecking=no host
```

```yaml
- uses: actions/checkout@v4
```
"""
    )

    assert {finding.rule for finding in scan(tmp_path)} == {
        "direct-pip-command",
        "direct-poetry-dependency-command",
        "manual-venv-command",
        "disabled-ssh-host-check",
        "mutable-action-ref",
    }
