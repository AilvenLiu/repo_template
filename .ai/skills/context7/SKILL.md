# context7 — library documentation lookup via MCP

> Vendor-neutral procedure description. Claude Code dispatches `/context7`
> to this body via the stub at `.claude/skills/context7/SKILL.md`. Codex /
> Cursor / Cline use this file as a reference; they typically configure
> Context7 as an MCP server in their own platform settings.

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
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: <your-key>"
```

The plugin-backed method is preferred and appears in `claude mcp list` as:
`plugin:context7:context7: ... ✓ Connected`

**Codex / Cursor / Cline:** configure the Context7 MCP server in the platform's
own MCP/settings file. The endpoint is `https://mcp.context7.com/mcp`.
