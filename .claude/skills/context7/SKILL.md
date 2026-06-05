---
name: context7
description: "Retrieve library/API documentation from Context7 MCP server. Auto-triggered for doc lookups."
---

# /context7

Library and API documentation lookup via the Context7 MCP server.
Auto-invoke whenever code generation, setup, configuration, or library usage
requires up-to-date documentation.

## Usage

```
/context7 <library> <query>
```

Or use the MCP tools directly in Claude Code:
1. `mcp__plugin_context7_context7__resolve-library-id` — resolve library name to ID
2. `mcp__plugin_context7_context7__query-docs` — fetch documentation

## Behaviour (guaranteed)

1. Resolves the library name to a Context7 library ID.
2. Fetches relevant documentation sections with code examples.
3. Returns formatted content ready to use in code generation.

## Mandatory usage rule

MUST use Context7 (not internal training knowledge) for:
- Python packages: NumPy, Pandas, FastAPI, Django, Flask, pytest, mypy, ruff, etc.
- C++ libraries: Boost, Eigen, OpenCV, CMake patterns
- CUDA Toolkit APIs and programming guides
- Any external library API signature, configuration, or version migration

Do NOT wait for the user to ask — invoke automatically when working with
external libraries.

## Prerequisites: install Context7

**Primary method (plugin-backed MCP):**
```bash
claude plugin install context7@claude-plugins-official
```

**Fallback method (manual MCP server registration):**
```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp \
  --header "CONTEXT7_API_KEY: <your-key>"
```

Verify with:
```bash
claude mcp list
# Expected: plugin:context7:context7: ... ✓ Connected
```

**If Context7 still fails after installation:**
```bash
claude plugin marketplace update claude-plugins-official
claude plugin update context7@claude-plugins-official
npm install -g --prefix "$HOME/.local" @upstash/context7-mcp
```

## Behaviour (best-effort)

- Auto-activation when the user asks about library usage (requires active session).
- Coverage depends on Context7's library database; flag if a library is missing.

## Error handling

If Context7 is unavailable: do NOT silently fall back to training data. Inform
the user that Context7 is unavailable and provide the setup commands above.
