---
name: context7
description: Look up current official library or framework documentation through Context7. Use when an API, version, option, migration, or behavior may have changed or when implementation depends on precise upstream documentation.
---

# context7 — library documentation lookup via MCP

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

Queries the Context7 MCP server for official library documentation
and API references.

## Usage

```
/context7 <library> <query>
```

(Or invoke the platform's native Context7 MCP tool directly.)

## Behaviour (guaranteed)

1. Resolves library ID via `context7_resolve_library`.
2. Fetches relevant doc sections via `context7_get_docs`.
3. Returns formatted content with code examples.

## Behaviour (best-effort)

- Auto-activation when user asks about library usage (requires CLAUDE.md config).
- Coverage depends on Context7's library database.

## Prerequisites

Context7 MCP server must be configured for the host platform.

**Claude Code, plugin-backed MCP (preferred):**
```bash
claude plugin install context7@claude-plugins-official
```

**Claude Code, manual MCP server registration (fallback):**
```bash
# CONTEXT7_API_KEY must already be exported from an approved secret source.
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: ${CONTEXT7_API_KEY}"
```

The plugin-backed method is preferred and appears in `claude mcp list` as:
`plugin:context7:context7: ... ✓ Connected`

**Codex / Cursor / Cline:** configure the Context7 MCP server in the platform's
own MCP/settings file. The endpoint is `https://mcp.context7.com/mcp`.
