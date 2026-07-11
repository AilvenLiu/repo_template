# init — session initialization

> Vendor-neutral procedure description. Claude Code dispatches `/init` to this
> body via the stub at `.claude/skills/init/SKILL.md`. Codex / Cursor / Cline
> consult this file directly via the AGENTS.md procedures table.

Detects project type, produces a bounded manifest of applicable constraint
paths, writes `.ai/session_state.json` (and `.claude/session_state.json` for
compatibility), and warns about protected branches and active roadmaps.

## Execution

```bash
# Claude Code
.ai/bin/agent-init --platform claude

# Codex / Cursor / Cline / generic agents
.ai/bin/agent-init --platform codex
```

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type; falls back to heuristic scan.
2. Runs the capability audit defined by `.ai/capabilities.yml`.
3. Prints a deterministic, profile-aware manifest of selected constraints.
   Read the listed files before work to which they apply; this keeps initial
   context bounded and makes the source of each rule inspectable.
4. Creates `.ai/session_state.json` (+ `.claude/session_state.json` mirror) —
   hooks and wrappers use this file to gate mutations.

## Failure mode

If the capability audit fails, the wrapper exits non-zero. The session is
considered blocked for mutating operations until the failure is resolved
and `.ai/bin/agent-init` is re-run.
