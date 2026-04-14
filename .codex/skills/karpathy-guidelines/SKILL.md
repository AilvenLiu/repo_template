---
name: karpathy-guidelines
description: Apply Karpathy-inspired behavioural guidance during non-trivial coding, debugging, review, or refactor tasks. Use it to surface assumptions, keep changes minimal, and define verifiable success criteria.
---

# Codex Karpathy Guidelines

Use this skill for non-trivial implementation, debugging, review, or refactor work.

## Principles

1. Think before coding.
   Make important assumptions explicit, surface tradeoffs, and ask when ambiguity materially changes the solution.
2. Simplicity first.
   Prefer the smallest complete fix. Do not add speculative features, abstractions, or configuration.
3. Surgical changes.
   Touch only the code needed for the request. Do not refactor or clean unrelated areas.
4. Goal-driven execution.
   Turn the task into verifiable success criteria and do not stop until the checks pass or a real blocker is identified.

## Tradeoff

These guidelines optimise for fewer costly mistakes, not maximum speed on trivial edits.

## Source

Adapted for this repository template from `forrestchang/andrej-karpathy-skills` (MIT).
