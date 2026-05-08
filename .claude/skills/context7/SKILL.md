---
name: context7
description: "Retrieve library/API documentation from Context7 MCP server. Auto-triggered for doc lookups."
---

# /context7

Library documentation lookup via the Context7 MCP server. The canonical,
vendor-neutral procedure body lives at
[`.ai/skills/context7/SKILL.md`](../../../.ai/skills/context7/SKILL.md).

## Usage

```
/context7 <library> <query>
```

## Prerequisites (Claude Code)

Primary method (plugin-backed MCP):
```bash
claude plugin install context7@claude-plugins-official
```

Fallback method (manual MCP server registration):
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: <your-key>"
```

The plugin-backed method is preferred and appears in `claude mcp list` as:
`plugin:context7:context7: ... ✓ Connected`

When this slash command is invoked, also read
[`.ai/skills/context7/SKILL.md`](../../../.ai/skills/context7/SKILL.md) for
the full behavioural spec, including how non-Claude agents (Codex, Cursor,
Cline) configure Context7 in their own platform settings.
