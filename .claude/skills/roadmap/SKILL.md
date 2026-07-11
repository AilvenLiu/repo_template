---
name: roadmap
description: "Manage dependency-aware multi-session workflows in agent_roadmaps/."
---

# /roadmap

Dependency-aware multi-session workflow management under `agent_roadmaps/`.
Roadmap files are temporary coordination state — never leak phase labels into
durable project files.

## Execution

```bash
.ai/bin/agent-roadmap <subcommand> [args...]
```

## Subcommands

| Subcommand | Usage | What it does |
|------------|-------|--------------|
| `check` | `.ai/bin/agent-roadmap check` | Detect active phase and dependency readiness (run at session start) |
| `create` | `.ai/bin/agent-roadmap create <name> --phases <N> --phase-names <names...>` | Create a new phase series with explicit dependencies |
| `status` | `.ai/bin/agent-roadmap status` | Show cross-phase and task dependency status |
| `update complete-task` | `.ai/bin/agent-roadmap update complete-task` | Complete current task and advance to next dependency-ready task |
| `update block-task` | `.ai/bin/agent-roadmap update block-task <reason>` | Mark current task blocked |
| `update unblock-task` | `.ai/bin/agent-roadmap update unblock-task` | Unblock first dependency-ready blocked task |
| `update set-focus` | `.ai/bin/agent-roadmap update set-focus <task-id>` | Set focus to a dependency-ready task |
| `handoff` | `.ai/bin/agent-roadmap handoff` | Generate session handoff file under `sessions/` |
| `complete` | `.ai/bin/agent-roadmap complete` | Mark active phase completed |
| `validate` | `.ai/bin/agent-roadmap validate <phase>` | Validate a phase's structural files |

## Behaviour (guaranteed)

1. Enforces single-active-phase rule (at most one phase `active` at a time).
2. Enforces dependency-safe task progression (`depends_on` and `depends_on_phases`).
3. Validates roadmap schema before any mutation.
4. Generates session handoff files under `agent_roadmaps/<phase>/sessions/`.
5. Treats all roadmap files as temporary workspace.

## Critical rules

- **At most one phase active.** Never activate a phase before its `depends_on_phases` are completed.
- **Branch discipline.** Work must be on branch `roadmap/<phase-folder-name>`.
- **Focus discipline.** Operate only on `focus.current_task`.
- **Session end.** End every roadmap session with `.ai/bin/agent-roadmap handoff`.
- **No label leakage.** Never copy roadmap-phase identifiers (`phase-N`,
  `roadmap/phase-N`) or legacy step identifiers into source files, config, docs,
  or filenames outside `agent_roadmaps/`.
- **Cleanup.** Once every phase in the roadmap is completed, delete the whole roadmap
  workspace and restore the placeholder `agent_roadmaps/README.md`.

## Repository-Local Precedence

Within the active roadmap workspace, resolve repository-controlled guidance as:

`INVARIANTS.md` > `roadmap.yml` > `ROADMAP.md` > `sessions/` > `prompt.md`

This ordering does not supersede platform or tool requirements. Current
`roadmap.yml` state takes precedence over prose and recorded session context.
