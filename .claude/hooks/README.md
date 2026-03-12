# Claude Code Hooks

This directory contains PreToolUse hooks that enforce project constraints at the tool-call level.

## Architecture

```
.claude/hooks/
├── pre_tool_use.sh          # Main dispatcher (receives JSON from Claude Code)
├── checks/
│   ├── bash_gate.sh         # Gates on Bash tool calls
│   └── write_gate.sh        # Gates on Write/Edit/MultiEdit tool calls
├── check_poetry_usage.sh    # Legacy: before_bash hook (kept for compatibility)
└── README.md
```

## How Hooks Work

Claude Code calls `pre_tool_use.sh` before executing any `Bash`, `Write`, `Edit`, or `MultiEdit` tool.

The dispatcher receives a JSON payload on stdin:
```json
{"tool_name": "Bash", "tool_input": {"command": "pip install requests"}}
```

- Exit 0 → allow the tool call
- Exit 1 → block the tool call (stderr message shown to agent)

## Gates Implemented

### bash_gate.sh

| Trigger | Action | Reason |
|---------|--------|--------|
| `git commit` on protected branch | BLOCK | Enforces branch policy |
| `git push --force` | BLOCK | Irreversible, requires confirmation |
| `git reset --hard` | BLOCK | Irreversible, requires confirmation |
| `pip install` (not via poetry run) | BLOCK | Enforces Poetry dependency management |
| `python`/`python3` (not via poetry run, not internal scripts) | BLOCK | Enforces Poetry venv isolation |
| `apt install lib*-dev` | BLOCK | Enforces Conan for C++ libraries |
| `brew install <non-toolchain>` | BLOCK | Enforces Conan for C++ libraries |
| `rm -rf src/lib/include/tests/.claude` | BLOCK | Protects source and config |

### write_gate.sh

| Trigger | Action | Reason |
|---------|--------|--------|
| Write to `agent_roadmaps/*/INVARIANTS.md` | BLOCK | Highest-authority document |
| Write to `.git/` | BLOCK | Git internals must not be modified directly |
| Write to `.claude/settings.json` | WARN | Changes affect enforcement itself |

## Design Principles

1. **Block high-risk, deterministic violations** — not aspirational rules
2. **Emit clear, actionable error messages** — tell the agent what to do instead
3. **Avoid false positives** — internal tooling (`.claude/skills/`) is always allowed
4. **Warn rather than block** for ambiguous cases
5. **No infinite loops** — hooks do not call tools that trigger hooks

## Limitations

- Cannot enforce "run /pre-commit before commit" at hook time (no state tracking)
- Cannot enforce "use /dependency skill" for `poetry add` directly (too many false positives)
- Cannot enforce Context7 usage (no deterministic check possible)
- Session handoff creation at end of roadmap sessions is aspirational (not hookable)

These limitations are documented in CLAUDE.md as policy rules.

## Adding New Gates

1. Add logic to `bash_gate.sh` or `write_gate.sh`
2. Follow the pattern: detect → emit clear message → exit 1
3. Add an entry to the gates table in this README
4. Test with: `echo '{"tool_name":"Bash","tool_input":{"command":"<cmd>"}}' | .claude/hooks/pre_tool_use.sh`
