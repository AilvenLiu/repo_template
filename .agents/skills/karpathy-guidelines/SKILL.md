---
name: karpathy-guidelines
description: Apply behavioral guardrails for non-trivial coding, debugging, review, refactoring, or architecture work. Use to keep changes simple, evidence-driven, scoped, explicit about uncertainty, and verified against observable success criteria.
---

# karpathy-guidelines — behavioural guardrails for non-trivial work

> Canonical repository skill. Codex discovers it natively from `.agents/skills/`;
> Claude Code reaches it through the matching `.claude/skills/` delegate.

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
