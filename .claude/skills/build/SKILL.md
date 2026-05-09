---
name: build
description: "Orchestrate build workflows. Environment setup, compilation, and testing."
---

# /build

Build orchestration. The canonical, vendor-neutral procedure body lives at
[`.ai/skills/build/SKILL.md`](../../../.ai/skills/build/SKILL.md).

## Execution

```bash
bin/agent-build <setup|compile|test|full|doctor|clean>
```

## Subcommands

- `setup` — create venv / install deps / configure toolchain
- `compile` — compile C++ (no-op for Python)
- `test` — run test suite
- `full` — setup + compile + test
- `clean` — remove build artefacts
- `doctor` — diagnose build environment issues

When this slash command is invoked, also read
[`.ai/skills/build/SKILL.md`](../../../.ai/skills/build/SKILL.md) for the full
behavioural spec.
