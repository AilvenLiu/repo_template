---
name: context7
description: "Retrieve library/API documentation from Context7 MCP server. Auto-triggered for doc lookups."
---

# /context7

Queries the Context7 MCP server for official library documentation
and API references.

## Usage

```
/context7 <library> <query>
```

## Behaviour (guaranteed)

1. Resolves library ID via `context7_resolve_library`.
2. Fetches relevant doc sections via `context7_get_docs`.
3. Returns formatted content with code examples.

## Behaviour (best-effort)

- Auto-activation when user asks about library usage (requires CLAUDE.md config).
- Coverage depends on Context7's library database.

## Prerequisites

Context7 MCP server must be configured:

**Primary method (plugin-backed MCP):**
```bash
claude plugin install context7@claude-plugins-official
```

**Fallback method (manual MCP server registration):**
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
```

The plugin-backed method is preferred and appears in `claude mcp list` as:
`plugin:context7:context7: ... ✓ Connected`
