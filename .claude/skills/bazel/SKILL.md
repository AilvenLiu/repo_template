---
name: bazel
description: "Bazel build orchestration for hybrid Python/C++/CUDA projects. Use when build_system=bazel."
version: 1.0.0
---

# /bazel

Bazel build orchestration. The canonical, vendor-neutral procedure body lives at
[`.ai/skills/bazel/SKILL.md`](../../../.ai/skills/bazel/SKILL.md).

## Execution

```bash
bin/agent-bazel <build|test|run|clean|query>
```

## Subcommands

- `build` -- build targets with Bazel
- `test` -- run Bazel test suite
- `run` -- execute Bazel targets
- `clean` -- clean Bazel build artefacts
- `query` -- query Bazel build graph

## Status

The wrapper now supports the common Bazel workflow surface directly. See the
vendor-neutral skill body for command semantics and examples.

When this slash command is invoked, also read
[`.ai/skills/bazel/SKILL.md`](../../../.ai/skills/bazel/SKILL.md) for the full
behavioural spec.
