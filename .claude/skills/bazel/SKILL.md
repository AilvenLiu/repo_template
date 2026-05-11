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

- `build` -- build targets with Bazel (fully implemented in Phase 2)
- `test` -- run Bazel test suite (Phase 3 stub)
- `run` -- execute Bazel targets (Phase 3 stub)
- `clean` -- clean Bazel build artefacts (Phase 3 stub)
- `query` -- query Bazel build graph (Phase 3 stub)

## Phase 2 Status

The `build` subcommand is fully implemented. Other subcommands are stubs that
print "not yet implemented; see Phase 3" and exit non-zero.

When this slash command is invoked, also read
[`.ai/skills/bazel/SKILL.md`](../../../.ai/skills/bazel/SKILL.md) for the full
behavioural spec.
