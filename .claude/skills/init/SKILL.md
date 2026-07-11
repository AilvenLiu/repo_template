---
name: init
description: "Session initialization — run at the start of EVERY session before any other action."
---

# /init

Session initialization. FIRST ACTION every session — skipping is a critical failure.

## Execution

```bash
.ai/bin/agent-init --platform claude
```

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type (Python / C++ / hybrid); falls back to heuristic scan.
2. Runs the capability audit defined by `.ai/capabilities.yml`:
   - checks required project skills under `.claude/skills/` and `.ai/skills/`
   - checks required `.ai/bin/agent-*` wrappers are executable
   - checks Context7 MCP is configured
3. Prints a bounded manifest of selected constraint paths. Read the listed
   files before work to which they apply instead of injecting every body into
   the initial session context.
4. Writes `.ai/session_state.json` and mirrors it to `.claude/session_state.json`.

## Failure modes

| Symptom | Meaning | Resolution |
|---------|---------|------------|
| Capability audit fails | Required plugin/skill/MCP missing | Install missing item, re-run `/init` |
| `[MISS] <key>` in output | Constraint file not found | Restore `.ai/constraints/<key>.md` |
| Session gate blocks Bash/Write | `session_state.json` absent or audit failed | Re-run `/init` |

## Post-init session gate

After a successful `/init`, the pre-tool-use hook allows all operations.
After a **failed** audit, Write/Edit/Bash are blocked until `/init` passes.
Read/Glob/Grep are always permitted for exploration.

## Constraints loaded (always)

- `common/instruction-hierarchy` — scoped repository-local precedence
- `common/git-workflow` — protected branches, commit attribution
- `common/session-discipline` — session lifecycle rules
- `common/closure-discipline` — rigorous review and evidence before closure
- `common/karpathy-guidelines` — behavioural guardrails
- `common/mcp-integration` — Context7 mandatory usage
- `common/ascii-only` — identifier encoding
- `common/agentic-team` — parallel sub-agent policy
- `common/roadmap-awareness` — if an active roadmap is detected

Plus language-specific sets for Python / C++ / hybrid (see `.ai/scripts/session_init.py`
`resolve_constraints()` for the full matrix).
