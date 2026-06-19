# bazel -- Bazel build orchestration

> Vendor-neutral procedure description. Claude Code dispatches `/bazel` to this
> body via the stub at `.claude/skills/bazel/SKILL.md`. Codex / Cursor / Cline
> consult this file directly via the AGENTS.md procedures table.

Automates Bazel build workflows for hybrid Python/C++/CUDA projects.

## Execution

```bash
.ai/bin/agent-bazel <build|test|run|clean|query>
```

## Subcommands

- `build` -- build targets with Bazel
- `test` -- run Bazel test suite
- `run` -- execute Bazel targets
- `clean` -- clean Bazel build artefacts
- `query` -- query Bazel build graph

## Behaviour (guaranteed)

1. Detects Bazel workspace via `WORKSPACE` or `MODULE.bazel` file.
2. Reads `.bazelrc` for project-specific build flags.
3. Invokes `bazel build` with appropriate flags for CUDA compilation.
4. Supports `--config` flag for build configurations (e.g., `--config=cuda`).

## Behaviour (best-effort)

- Remote caching and remote execution configuration.
- Bazel query for dependency analysis.
- Integration with CUDA toolkit discovery.
- Cross-compilation for multiple GPU architectures.

## Build Subcommand

The `build` subcommand is fully implemented:

```bash
.ai/bin/agent-bazel build [--config=<config>] [targets...]
```

### Default Behaviour

- Builds all targets if none specified
- Uses `.bazelrc` for default flags
- Respects `CUDA_HOME` and `CUDNN_ROOT` environment variables
- Outputs build logs to stdout

### Configuration Profiles

Common configurations via `--config` flag:

- `--config=cuda` -- CUDA-enabled build with GPU support
- `--config=opt` -- optimized release build
- `--config=dbg` -- debug build with symbols
- `--config=asan` -- AddressSanitizer instrumentation
- `--config=tsan` -- ThreadSanitizer instrumentation

### Examples

```bash
# Build all targets
.ai/bin/agent-bazel build

# Build specific target
.ai/bin/agent-bazel build //src/kernels:flash_attention

# Build with CUDA configuration
.ai/bin/agent-bazel build --config=cuda //src/kernels:all

# Build optimized release
.ai/bin/agent-bazel build --config=opt //...

# Build with multiple configs
.ai/bin/agent-bazel build --config=cuda --config=opt //src:all
```

### CUDA Integration

When building CUDA targets, the wrapper:

1. Checks for `CUDA_HOME` environment variable
2. Validates CUDA Toolkit installation
3. Sets `--action_env=CUDA_HOME` for Bazel
4. Passes `--repo_env=CUDA_HOME` for repository rules
5. Respects `TORCH_CUDA_ARCH_LIST` for GPU architectures

### Error Handling

- Fails fast if `WORKSPACE` or `MODULE.bazel` not found
- Validates Bazel installation before invoking
- Provides actionable error messages for missing dependencies
- Suggests `--config` flags when CUDA targets fail

## Test Subcommand

```bash
.ai/bin/agent-bazel test [--config=<config>] [targets...]
```

Default behaviour: runs `bazel test //...` when no targets are specified.

## Run Subcommand

```bash
.ai/bin/agent-bazel run [--config=<config>] <target> [-- <args>...]
```

Default behaviour: requires an explicit runnable target and forwards all args.

## Clean Subcommand

```bash
.ai/bin/agent-bazel clean [--expunge]
```

Default behaviour: forwards directly to `bazel clean`.

## Query Subcommand

```bash
.ai/bin/agent-bazel query <query-expression>
```

Default behaviour: requires an explicit query expression and forwards it.

## Integration with Constraints

This skill respects the following constraints:

- `.ai/constraints/cpp/cuda-modern.md` -- CUDA compilation flags
- `.ai/constraints/cpp/kernel-correctness.md` -- test target patterns
- `.ai/constraints/hybrid/system-deps.md` -- CUDA Toolkit discovery

## Integration with Other Skills

### With /init

When `/init` detects `WORKSPACE` or `MODULE.bazel`, it loads this skill.

### With /build

The generic `/build` skill delegates to `/bazel` when `build_system=bazel`.

### With /pre-commit

Pre-commit hooks can invoke `.ai/bin/agent-bazel build` for validation.

## Bazel Version Requirements

- Minimum Bazel version: 6.0.0
- Bazel 7.0.0+ improves CUDA support for Bazel-first projects
- Bazelisk can manage per-project Bazel versions

## Common Pitfalls

### CUDA Toolkit Not Found

**Problem**: Bazel cannot find CUDA Toolkit.

**Solution**: Set `CUDA_HOME` environment variable:

```bash
export CUDA_HOME=/usr/local/cuda
.ai/bin/agent-bazel build --config=cuda
```

### Incompatible CUDA Architecture

**Problem**: Compiled kernels don't run on target GPU.

**Solution**: Set `TORCH_CUDA_ARCH_LIST`:

```bash
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
.ai/bin/agent-bazel build --config=cuda
```

### Remote Cache Misconfiguration

**Problem**: Remote cache authentication fails.

**Solution**: Check `.bazelrc` for correct credentials and endpoints.

## References

- Bazel documentation: https://bazel.build/
- Bazel CUDA rules: https://github.com/bazelbuild/rules_cuda
- Bazelisk: https://github.com/bazelbuild/bazelisk
