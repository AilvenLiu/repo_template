# Instruction Hierarchy and Platform Compatibility

Repository guidance is mandatory within its proper scope. It is not a
replacement for higher-priority platform safety requirements, developer
instructions, managed organisational policy, tool-enforced permissions,
sandbox restrictions, or user-granted permissions.

If a higher-priority requirement prevents compliance with a repository policy,
the agent MUST follow the higher-priority requirement, avoid silently relaxing
the repository policy, minimise the deviation, and report the conflict before
making an unauthorised or unsafe mutation.

## Repository-Local Precedence

The following order resolves conflicts only among repository-controlled
guidance. It does not rank repository files against platform or tool
requirements.

1. Active phase `INVARIANTS.md`, when a roadmap is active
2. Active phase `roadmap.yml` for current executable state, dependencies, and
   `focus.current_task`
3. Active phase `ROADMAP.md` for approved scope and execution intent
4. Applicable shared and profile-specific `.ai/constraints/` files
5. The relevant platform entrypoint (`AGENTS.md` or `CLAUDE.md`)
6. `CONTRIBUTING.md` and other durable repository documentation
7. Roadmap session handoffs, `prompt.md`, and other temporary notes

Within a phase, session handoffs and `prompt.md` provide context only. They
MUST NOT change invariants, the current `roadmap.yml` state, or durable project
policy. Do not use stale conversational assumptions when they conflict with
the current repository state.

## Applying the Policy

- Do not relax a repository policy because lower-precedence repository prose or
  a stale session record says otherwise.
- Preserve strong requirements such as mandatory validation, dependency
  controls, protected-branch checks, and closure review.
- If repository-controlled sources conflict and the order above does not
  resolve the issue, stop and ask for clarification or an ADR path.
