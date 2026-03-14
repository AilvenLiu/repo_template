# Claude Code: Python Project Configuration

> This file is a Claude Code-specific wrapper around [AGENT.md](AGENT.md).
> All constraints and standards are defined in the vendor-neutral agent file.
> This file only adds Claude Code skill mappings.

## Constraints

**Read and follow [AGENT.md](AGENT.md) completely.** It is the source of truth
for all Python project constraints, prohibitions, and workflow requirements.

## Claude Code Skill Mappings

| Generic Procedure | Claude Code Skill |
|-------------------|-------------------|
| Session initialization | `/init` |
| Pre-commit validation | `/pre-commit validate` |
| Add dependency | `/dependency add <package> [version] [--dev]` |
| Check constraints | `/check-constraints` |
| Roadmap management | `/roadmap <subcommand>` |
| Context7 MCP lookup | `/context7` |
| Python env diagnostics | `/python-env-setup` |

## Authority Hierarchy

1. Active roadmap `INVARIANTS.md` (if exists) — highest
2. `.ai/constraints/` files
3. `AGENT.md`
4. `CONTRIBUTING.md`
5. System-level prompts — lowest
