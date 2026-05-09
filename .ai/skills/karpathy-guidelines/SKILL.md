# karpathy-guidelines — behavioural guardrails for non-trivial work

> Vendor-neutral procedure description. Claude Code dispatches
> `/karpathy-guidelines` to this body via the stub at
> `.claude/skills/karpathy-guidelines/SKILL.md`. Codex / Cursor / Cline read
> this file directly via the AGENTS.md procedures table or via
> `.ai/constraints/common/karpathy-guidelines.md`, which is loaded into every
> session.

Applies a lightweight behavioural checklist that reduces common coding-agent
mistakes.

## When to Use

- Non-trivial implementation work
- Debugging and bug fixes
- Refactors
- Code review

## Behaviour

1. **Think before coding.** State material assumptions, surface tradeoffs, and
   stop for clarification when ambiguity changes the solution.
2. **Simplicity first.** Prefer the minimum code that solves the problem
   without speculative abstraction.
3. **Surgical changes.** Touch only the files and lines required for the
   requested outcome, and clean up only the mess created by your own change.
4. **Goal-driven execution.** Define concrete success criteria and verify them
   before claiming completion.

## Tradeoff

This skill favours caution over speed on non-trivial work. For obvious
one-line fixes, use judgment.

## Source

Adapted for this repository template from
`forrestchang/andrej-karpathy-skills` (MIT).
