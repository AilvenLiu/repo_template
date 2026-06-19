# Claude Code Hooks

This directory contains PreToolUse hooks that enforce project constraints at the tool-call level.

## Architecture

```
.claude/hooks/
├── pre_tool_use.sh          # Main dispatcher (receives JSON from Claude Code)
├── checks/
│   ├── bash_gate.sh         # Gates on Bash tool calls
│   └── write_gate.sh        # Gates on Write/Edit/MultiEdit tool calls
├── tests/
│   └── test_security_bypasses.sh   # Regression tests for all security gates
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

### Pre-init Gate (in pre_tool_use.sh)

Before session initialization (`session_state.json` does not exist):

| Trigger | Action | Reason |
|---------|--------|--------|
| Any `Write`/`Edit`/`MultiEdit` tool | BLOCK | No mutations before init |
| Any `Bash` command that is not exactly the init invocation | BLOCK | Fail-closed before init |
| `.ai/bin/agent-init` | ALLOW | Exact init invocation |
| `.ai/bin/agent-init --verbose` | ALLOW | Exact init invocation with verbose |
| `.ai/bin/agent-init --platform claude` | ALLOW | Exact init invocation for Claude |

**Security note**: The allowlist enforces a two-stage check:
1. Reject any command containing shell metacharacters (`; & | < > $ \` \``)
2. Require the remaining command to match exactly one of the approved forms

This prevents prefix-match bypass attacks such as:

```
.ai/bin/agent-init && echo hacked > .claude/session_state.json
```

The above is blocked by stage 1 (detects `&`).

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

`bash_gate.sh` delegates policy decisions to `.ai/scripts/policy_gate.py --op bash`,
so Codex and Claude enforce the same command-level policy.

### write_gate.sh

| Trigger | Action | Reason |
|---------|--------|--------|
| Write to `agent_roadmaps/*/INVARIANTS.md` | BLOCK | Highest-authority document |
| Write to `.git/` | BLOCK | Git internals must not be modified directly |
| Write to `.claude/settings.json` | WARN | Changes affect enforcement itself |

`write_gate.sh` uses `.ai/scripts/policy_gate.py --op mutate` for shared init/audit
gating, then applies write-specific file protections.

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

## Running Tests

The regression test suite covers all security policies, including pre-init bypass attempts:

```bash
bash .claude/hooks/tests/test_security_bypasses.sh
```

This runs 38 tests across 5 policies:
1. Write/Edit/MultiEdit tools blocked before init
2. Only init script allowed via Bash before init
3. All other Bash commands blocked before init
4. Generic shell bypass attempts blocked
5. Init-prefix bypass attempts blocked (the specific vulnerability class)
