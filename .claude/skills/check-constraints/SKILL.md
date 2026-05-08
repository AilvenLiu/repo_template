---
name: check-constraints
description: "Validate constraint compliance at any time during development."
---

# /check-constraints

Lightweight constraint compliance check. The canonical, vendor-neutral
procedure body lives at
[`.ai/skills/check-constraints/SKILL.md`](../../../.ai/skills/check-constraints/SKILL.md).

## Execution

```bash
bin/agent-check-constraints
```

Exit `0` = no critical violations, exit `1` = violations found.

When this slash command is invoked, also read
[`.ai/skills/check-constraints/SKILL.md`](../../../.ai/skills/check-constraints/SKILL.md)
for the full behavioural spec.
