# Codex: C++/CUDA Project

## Mandatory Session Initialization

First action every session:

```bash
bin/agent-init --platform codex
```

If initialization or capability audit fails, mutation work is blocked.

## Bundled Behavioural Skill

This template bundles `karpathy-guidelines` in `.codex/skills/karpathy-guidelines/`.

Use it for non-trivial coding, debugging, review, and refactor work. It keeps
the agent focused on explicit assumptions, simple solutions, surgical diffs,
and verifiable success criteria.

## Bundled Codex Skills

Codex-native best-effort skills included in generated C++ repos:
- `build` via `bin/agent-build <setup|compile|test|full|doctor|clean>`
- `navigate` via repo-native `rg`-first exploration

The repository requires British English for user-facing text.

## Required Workflow Commands

- Init: `bin/agent-init --platform codex`
- Build: `bin/agent-build <setup|compile|test|full|doctor|clean>`
- Constraint check: `bin/agent-check-constraints`
- Pre-commit validation: `bin/agent-precommit`
- Dependency add: `bin/agent-dependency add <package> [version]`
- Roadmap workflow: `bin/agent-roadmap <check|create|status|update|handoff|complete|validate>`
- Commit with policy guard: `bin/agent-commit -m "type(scope): description" <file1> [file2 ...]`

## Absolute Prohibitions

- Never commit directly to `master`, `main`, `develop`, `release/*`, `hotfix/*`
- Never install C++ deps through system package managers for project dependencies
- Never ignore CUDA API error handling requirements
- Never include AI attribution in commit messages
- Never bypass failed capability audit

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md`
2. `.ai/constraints/`
3. `AGENTS.md`
4. `CONTRIBUTING.md`
5. System prompts
