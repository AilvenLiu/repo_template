---
name: bazel
description: "Bazel build orchestration for hybrid Python/C++/CUDA projects. Use when build_system=bazel."
version: 1.0.0
---

# /bazel

Bazel build orchestration for hybrid Python/C++/CUDA projects.
Use this skill when `.ai/project.yml` declares `build_system: bazel`.

## Execution

```bash
bin/agent-bazel <build|test|run|clean|query>
```

## Subcommands

| Subcommand | Usage | What it does |
|------------|-------|--------------|
| `build` | `bin/agent-bazel build [--config=<cfg>] [targets...]` | Build targets |
| `test` | `bin/agent-bazel test [--config=<cfg>] [targets...]` | Run test suite |
| `run` | `bin/agent-bazel run [--config=<cfg>] <target> [-- <args>]` | Execute a runnable target |
| `clean` | `bin/agent-bazel clean [--expunge]` | Remove build artefacts |
| `query` | `bin/agent-bazel query <expr>` | Query the build graph |

## Behaviour (guaranteed)

1. Verifies `WORKSPACE` or `MODULE.bazel` exists; fails fast otherwise.
2. Reads `.bazelrc` for project-specific flags.
3. For CUDA targets: checks `CUDA_HOME`, sets `--action_env=CUDA_HOME` and
   `--repo_env=CUDA_HOME`, respects `TORCH_CUDA_ARCH_LIST`.
4. Validates Bazel ≥ 6.0.0 is installed before invoking.

## Common `--config` profiles

| Config | Purpose |
|--------|---------|
| `--config=cuda` | CUDA-enabled build with GPU support |
| `--config=opt` | Optimised release build |
| `--config=dbg` | Debug build with symbols |
| `--config=asan` | AddressSanitizer instrumentation |
| `--config=tsan` | ThreadSanitizer instrumentation |

## Example commands

```bash
# Build all targets
bin/agent-bazel build

# Build a specific CUDA kernel with optimisation
bin/agent-bazel build --config=cuda --config=opt //src/kernels:flash_attention

# Run all tests
bin/agent-bazel test //...

# Query reverse dependencies
bin/agent-bazel query "rdeps(//..., //src/kernels:attention)"
```

## Environment variables required for CUDA

```bash
export CUDA_HOME=/usr/local/cuda
export TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9;9.0"
```

## Behaviour (best-effort)

- Remote caching and remote execution configuration.
- Cross-compilation for multiple GPU architectures.
- Integration with CUDA toolkit discovery beyond `CUDA_HOME`.

## Common pitfalls

| Problem | Solution |
|---------|---------|
| CUDA Toolkit not found | Set `CUDA_HOME` env var |
| Compiled kernels wrong arch | Set `TORCH_CUDA_ARCH_LIST` |
| Remote cache auth fails | Check `.bazelrc` credentials |
