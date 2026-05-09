---
name: dependency
description: "Add dependencies. Poetry for Python (mandatory), Conan/vcpkg for C++."
---

# /dependency

Add a project dependency. The canonical, vendor-neutral procedure body lives
at [`.ai/skills/dependency/SKILL.md`](../../../.ai/skills/dependency/SKILL.md).

## Execution

```bash
bin/agent-dependency add <package> [version] [--dev]
```

When this slash command is invoked, also read
[`.ai/skills/dependency/SKILL.md`](../../../.ai/skills/dependency/SKILL.md) for
the full behavioural spec (Python vs C++ handling, manifest update rules,
Conan install fallback, etc.).
