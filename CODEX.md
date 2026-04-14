# Codex Instructions for This Repository

This is the **template repository**.

Language-specific Codex entrypoints live in:
- `CODEX_PYTHON.md`
- `CODEX_CPP.md`

When generating a real project, the selected variant is copied to `CODEX.md`.

The vendor-neutral constraints live in `AGENTS.md` and `.ai/constraints/`.

## Bundled Behavioural Skill

This template now vendors `karpathy-guidelines` locally for Codex.

Use it for non-trivial coding, debugging, review, and refactor work to keep
changes minimal, surface assumptions early, and drive work with verifiable
success criteria.

Codex also ships local best-effort skills for:
- `build`
- `navigate`
- `python-env-setup` on Python projects

The repository requires British English for user-facing text.
