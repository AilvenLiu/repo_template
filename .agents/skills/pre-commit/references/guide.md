# Pre-Commit Skill

This repository-local Claude skill delegates to the canonical procedure at
`.agents/skills/pre-commit/SKILL.md`. Do not copy it into a global skill directory;
the generated project carries the matching constraints and wrappers with it.

Run the profile-aware gate from the repository root:

```bash
.agents/bin/agent-precommit
```

Use `.agents/bin/agent-dependency` for Python tool dependencies and the documented
system/toolchain setup for C++/CUDA tools. Do not install project tooling directly
with pip or create an unmanaged virtual environment.

The gate selects the applicable formatter, linter, type checker, build, tests,
and forbidden-pattern checks from `.agents/project.yml` and the initialized
constraint manifest. Its exit status is authoritative for commit readiness;
missing required tools are failures to provision, not permission to skip checks.
