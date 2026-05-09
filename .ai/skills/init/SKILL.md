# init — session initialization

> Vendor-neutral procedure description. Claude Code dispatches `/init` to this
> body via the stub at `.claude/skills/init/SKILL.md`. Codex / Cursor / Cline
> consult this file directly via the AGENTS.md procedures table.

Detects project type, loads constraint bodies into the conversation,
writes `.ai/session_state.json` (and `.claude/session_state.json` for
compatibility), and warns about protected branches and active roadmaps.

## Execution

```bash
# Claude Code
bin/agent-init --platform claude

# Codex / Cursor / Cline / generic agents
bin/agent-init --platform codex
```

## Behaviour (guaranteed)

1. Reads `.ai/project.yml` for project type; falls back to heuristic scan.
2. Runs the capability audit defined by `.ai/capabilities.yml`.
3. Prints the full text of every selected constraint so the agent ingests it.
4. Creates `.ai/session_state.json` (+ `.claude/session_state.json` mirror) —
   hooks and wrappers use this file to gate mutations.

## Failure mode

If the capability audit fails, the wrapper exits non-zero. The session is
considered blocked for mutating operations until the failure is resolved
and `bin/agent-init` is re-run.
