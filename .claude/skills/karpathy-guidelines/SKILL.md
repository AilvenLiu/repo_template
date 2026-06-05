---
name: karpathy-guidelines
description: "Karpathy-inspired behavioural guidance for non-trivial coding, debugging, review, or refactor work. Use to surface assumptions, keep changes minimal, and define verifiable success criteria."
version: 1.0.0
---

# /karpathy-guidelines

Behavioural checklist for non-trivial coding, debugging, refactoring, and code
review work. The full text is also loaded into every session via
`common/karpathy-guidelines` constraint during `/init`.

## When to apply

- Any implementation work beyond a single obvious line fix
- Debugging sessions
- Refactors that touch more than one file
- Code review

## The four rules

### 1. Think before coding

State material assumptions before writing code. Surface tradeoffs. Stop and ask
when ambiguity changes the solution shape. Prefer a short plan + verification
step over diving straight into implementation.

### 2. Simplicity first

Write the minimum code that fully solves the stated problem.

- Do not add features, configurability, or abstractions not requested.
- Do not build reusable infrastructure for a one-off need.
- Do not add defensive complexity for scenarios that cannot happen.
- Three similar lines > a premature abstraction.

### 3. Surgical changes

Touch only the code needed for the requested outcome.

- Do not refactor adjacent code just because you noticed it.
- Do not rewrite comments, formatting, or APIs unrelated to the task.
- Match local project patterns unless asked to change direction.
- Clean up only unused imports/variables created by your own change.
- Call out unrelated debt separately instead of silently fixing it.

Every changed line must be traceable to the user request or to verification
required by that request.

### 4. Goal-driven execution

Turn vague instructions into concrete success criteria and verify them.

- Prefer reproduction-first debugging: identify a failing check, then make it pass.
- Prefer before-and-after validation for refactors.
- State a short plan for multi-step work with a verification step for each stage.
- Do not claim completion without evidence from tests, builds, linters, or another
  concrete check.

## Tradeoff

This skill favours correctness and caution over raw speed on non-trivial work.
Apply judgment on obvious one-liners — do not over-engineer the process.

## Source

Adapted from `forrestchang/andrej-karpathy-skills` (MIT) for this repository template.
