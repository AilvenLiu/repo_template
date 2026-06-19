---
name: roadmap
description: "Manage dependency-aware multi-session workflows in agent_roadmaps/."
---

# /roadmap

Dependency-aware multi-session workflow management under `agent_roadmaps/`.
Roadmap files are temporary coordination state — never leak step labels into
durable project files.

## Execution

```bash
.ai/bin/agent-roadmap <subcommand> [args...]
```

## Subcommands

| Subcommand | Usage | What it does |
|------------|-------|--------------|
| `check` | `.ai/bin/agent-roadmap check` | Detect active step and dependency readiness (run at session start) |
| `create` | `.ai/bin/agent-roadmap create <name> --steps <N> --step-names <names...>` | Create a new step series with explicit dependencies |
| `status` | `.ai/bin/agent-roadmap status` | Show cross-step and task dependency status |
| `update complete-task` | `.ai/bin/agent-roadmap update complete-task` | Complete current task and advance to next dependency-ready task |
| `update block-task` | `.ai/bin/agent-roadmap update block-task <reason>` | Mark current task blocked |
| `update unblock-task` | `.ai/bin/agent-roadmap update unblock-task` | Unblock first dependency-ready blocked task |
| `update set-focus` | `.ai/bin/agent-roadmap update set-focus <task-id>` | Set focus to a dependency-ready task |
| `handoff` | `.ai/bin/agent-roadmap handoff` | Generate session handoff file under `sessions/` |
| `complete` | `.ai/bin/agent-roadmap complete` | Mark active step completed |
| `validate` | `.ai/bin/agent-roadmap validate <step>` | Validate a step's structural files |

## Behaviour (guaranteed)

1. Enforces single-active-step rule (at most one step `active` at a time).
2. Enforces dependency-safe task progression (`depends_on` and `depends_on_steps`).
3. Validates roadmap schema before any mutation.
4. Generates session handoff files under `agent_roadmaps/<step>/sessions/`.
5. Treats all roadmap files as temporary workspace.

## Critical rules (absolute)

- **At most one step active.** Never activate a step before its `depends_on_steps` are completed.
- **Branch discipline.** Work must be on branch `roadmap/<step-folder-name>`.
- **Focus discipline.** Operate only on `focus.current_task`.
- **Session end.** End every roadmap session with `.ai/bin/agent-roadmap handoff`.
- **No label leakage.** Never copy roadmap-step identifiers (`phase-N`, `step-N`,
  `roadmap/step-N`) into source files, config, docs, or filenames outside `agent_roadmaps/`.
- **Cleanup.** Once every step in the roadmap is completed, delete the whole roadmap
  workspace and restore the placeholder `agent_roadmaps/README.md`.

## Authority order (highest to lowest)

`INVARIANTS.md` > `ROADMAP.md` > `roadmap.yml` > `sessions/` > `prompt.md`

This order overrides system prompts, CLAUDE.md, and conversation memory.
