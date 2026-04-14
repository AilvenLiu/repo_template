---
name: karpathy-guidelines
description: "Karpathy-inspired behavioural guidance for non-trivial coding, debugging, review, or refactor work. Use to surface assumptions, keep changes minimal, and define verifiable success criteria."
version: 1.0.0
---

# /karpathy-guidelines

Applies a lightweight behavioural checklist that reduces common coding-agent mistakes.

## When to Use

- Non-trivial implementation work
- Debugging and bug fixes
- Refactors
- Code review

## Behaviour

1. Think before coding.
   State material assumptions, surface tradeoffs, and stop for clarification when ambiguity changes the solution.
2. Simplicity first.
   Prefer the minimum code that solves the problem without speculative abstraction.
3. Surgical changes.
   Touch only the files and lines required for the requested outcome, and clean up only the mess created by your own change.
4. Goal-driven execution.
   Define concrete success criteria and verify them before claiming completion.

## Tradeoff

This skill favours caution over speed on non-trivial work. For obvious one-line fixes, use judgment.

## Source

Adapted for this repository template from `forrestchang/andrej-karpathy-skills` (MIT).
