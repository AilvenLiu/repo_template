# roadmap — dependency-aware multi-session workflows

> Vendor-neutral procedure description. Claude Code dispatches `/roadmap`
> to this body via the stub at `.claude/skills/roadmap/SKILL.md`. Codex /
> Cursor / Cline read this file directly via the AGENTS.md procedures table.

Structured commands for dependency-aware step workflows under
`agent_roadmaps/`.
These files are temporary coordination state and must not leak into durable
project artefacts.

## Execution

```bash
bin/agent-roadmap <subcommand> [args...]
```

## Subcommands

- `check` — detect active step and dependency readiness (run at session start)
- `create <name> --steps <N> --step-names <names...>` — create step series
  with explicit dependencies
- `status` — show cross-step and task dependency status
- `update complete-task` — complete current task and advance to next dependency-ready task
- `update block-task <reason>` — mark current task blocked
- `update unblock-task` — unblock first dependency-ready blocked task
- `update set-focus <task-id>` — set focus to a dependency-ready task
- `handoff` — generate session handoff file
- `complete` — mark active step completed
- `validate <step>` — validate a step's structural files

## Behaviour (guaranteed)

1. Enforces single-active-step rule.
2. Enforces dependency-safe task progression (`depends_on`).
3. Validates dependency-aware roadmap schema.
4. Generates session handoff files under `sessions/`.
5. Treats roadmap files as temporary workspace that must be removed after full completion.

## Critical rules

- At most one step may be active.
- Work must be on branch `roadmap/<step-folder-name>`.
- Do not start a step before `depends_on_steps` are completed.
- Operate only on `focus.current_task`.
- End each roadmap session with roadmap state + handoff update.
- Do not copy roadmap-stage labels into durable files outside `agent_roadmaps/`.
- Once every step in the roadmap is completed, delete the roadmap workspace and restore the placeholder `agent_roadmaps/README.md`.
- Authority order:
  `INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`.
