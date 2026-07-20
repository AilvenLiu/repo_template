# Platform Adapter Architecture

The repository keeps one vendor-neutral implementation for every workflow.

## Ownership

- `.agents/skills/<name>/SKILL.md` is the canonical skill body and Codex's
  native repository skill.
- `.agents/constraints/`, `.agents/scripts/`, `.agents/bin/`, and
  `.agents/hooks/` contain canonical policy and deterministic implementation.
- `.claude/skills/<name>/SKILL.md` is a thin Claude Code discovery delegate.
- `.claude/settings.json` and `.claude/hooks/pre_tool_use.sh` register and
  delegate Claude's lifecycle hook.
- `.codex/hooks.json` and `.codex/hooks/pre_tool_use.py` register and adapt
  Codex's lifecycle hook. Codex skills do not live under `.codex/skills/`.

## Adding or updating a skill

1. Create or update `.agents/skills/<name>/SKILL.md`.
2. Keep YAML frontmatter limited to `name` and a trigger-focused
   `description`.
3. Put optional scripts, references, or assets beside the canonical skill.
4. Add a matching thin Claude delegate with the same name and description.
5. Declare the capability in `.agents/capabilities.yml`.
6. Run both platform verifiers and the skill validator.

Do not copy a canonical body into a platform directory. Tests must fail when a
delegate stops pointing at its canonical body or when a Codex skill is placed
under the obsolete `.codex/skills/` path.
