# Karpathy-Inspired Execution Guidelines

> Adapted for Agent Foundry from `forrestchang/andrej-karpathy-skills` (MIT).
> These guidelines apply to all non-trivial coding, debugging, review, and refactor work.

## Overview

Use this constraint to reduce common agent failure modes:
- silent assumptions
- unnecessary complexity
- broad, unrelated edits
- weak or unverifiable completion criteria

For trivial, low-risk changes, use judgment and keep momentum.

## 1. Think Before Coding

Do not silently choose an interpretation when the request is ambiguous.

- State important assumptions explicitly before committing to an implementation
- Surface non-obvious tradeoffs rather than hiding them
- Ask when a missing detail could materially change the design or risk profile
- Push back gently when a simpler approach would better fit the request

## 2. Simplicity First

Prefer the smallest change that completely solves the problem.

- Do not add features, configurability, or abstractions that were not requested
- Do not build reusable infrastructure for one-off needs
- Do not add defensive complexity for scenarios that cannot realistically happen
- If the same outcome can be achieved with much less code, simplify

## 3. Surgical Changes

Touch only the code needed for the requested outcome.

- Do not refactor adjacent code just because you noticed it
- Do not rewrite comments, formatting, or APIs unrelated to the task
- Match local project patterns unless the user asked for a change in direction
- Clean up only the unused imports, variables, or helpers created by your own change
- If you notice unrelated debt, call it out separately instead of deleting it

Every changed line should be traceable to the user request or to verification required by that request.

## 4. Goal-Driven Execution

Turn vague instructions into concrete success criteria and verify them.

- Prefer reproduction-first debugging: create or identify a failing test/check, then make it pass
- Prefer before-and-after validation for refactors
- State a short plan for multi-step work with a verification step for each stage
- Do not claim completion without evidence from tests, builds, linters, or another concrete check

Strong success criteria help the agent work autonomously. Weak criteria invite drift.
