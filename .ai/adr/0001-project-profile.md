# ADR 0001: Project Profile Composition

**Status**: Proposed  
**Date**: 2026-05-10  
**Authors**: Phase 1 Architecture Team  
**Supersedes**: Binary `project_type` enum

## Context

### The Problem

The current `.ai/project.yml` uses a binary `project_type` field with two values: `python` or `cpp`. This worked for the initial template design where projects were cleanly partitioned into pure-Python or pure-C++/CUDA codebases. However, real AI infrastructure projects do not fit this binary model:

- **Apache TVM** and **MLC-LLM**: Python frontend with C++/CUDA kernels, scikit-build-core build system, nanobind or custom FFI bindings, PyPI distribution, system CUDA libraries
- **FlashInfer** and **xgrammar**: Similar hybrid architecture with different binding strategies
- **CUTLASS-derived projects**: Pure C++/CUDA but may use CMake, Bazel, or custom build systems
- **Google LiteRT-LM**: Hybrid with TensorFlow Lite integration

Adding more `project_type` enum values (e.g., `python_cpp_cuda`, `python_cpp_cuda_tvm`, `python_cpp_cuda_mlc`) explodes combinatorially and couples unrelated concerns (language vs build system vs bindings vs distribution).

### Current Architecture

The binary `project_type` drives three subsystems:

1. **Constraint loading** ([session_init.py:185-224](../../.ai/scripts/session_init.py#L185-L224)): Loads constraint files from `.ai/constraints/common/`, `.ai/constraints/python/`, or `.ai/constraints/cpp/` based on the project type
2. **Capability audit** ([capabilities.yml:12-91](../../.ai/capabilities.yml#L12-L91)): Declares required skills per `project_types: [python]` or `project_types: [cpp]`
3. **Build and dependency dispatch** ([bin/agent-build](../../bin/agent-build), [bin/agent-dependency](../../bin/agent-dependency)): Routes to Poetry (Python) or CMake+Conan (C++)

This architecture cannot express:
- A project with **both** Python and C++ source requiring **both** constraint sets
- A Python project using **scikit-build-core** instead of Poetry
- A C++ project using **Bazel** instead of CMake
- A project with **nanobind** bindings requiring binding-specific constraints

### Why This Matters Now

Phase 2 of the AI Infra Optimisation roadmap adds:
- Hybrid Python+C++/CUDA constraint overlay
- scikit-build-core build system support
- Binding-specific constraints (nanobind, pybind11, TVM FFI)
- Distribution-specific constraints (PyPI wheel, conda, system package)

Without a composable profile schema, Phase 2 would require either:
1. Adding 20+ new `project_type` enum values (unmaintainable)
2. Overloading the binary `project_type` with side-channel configuration (fragile)
3. Rewriting the entire constraint system (out of scope)

## Decision

We replace the binary `project_type` with a **composable `project_profile`** that captures multiple independent axes:

```yaml
project_profile:
  language: [python, cpp]           # Can be multiple
  build_system: cmake                # Primary build orchestrator
  bindings: nanobind                 # FFI/binding layer (optional)
  distribution: pypi-wheel           # Distribution target (optional)
  hardware_targets: [cuda, cpu]      # Hardware backends (optional)
  external_dependencies: system_cuda # Dependency strategy (optional)
```

### Schema Design

Each axis is independent and loads its own constraint subset additively:

| Axis | Values | Constraint Path | Loaded When |
|------|--------|----------------|-------------|
| `language` | `python`, `cpp` | `.ai/constraints/{language}/` | Always (at least one required) |
| `build_system` | `poetry`, `cmake`, `scikit-build`, `scikit-build-core`, `bazel`, `mixed` | Dispatch in `bin/agent-build` | Always (exactly one required) |
| `bindings` | `none`, `nanobind`, `pybind11`, `tvm-ffi`, `ctypes` | `.ai/constraints/bindings/{value}/` | Optional (Phase 2) |
| `distribution` | `none`, `pypi`, `pypi-wheel`, `conda`, `system`, `header-only` | `.ai/constraints/distribution/{value}/` | Optional (Phase 2) |
| `hardware_targets` | `cpu`, `cuda`, `rocm`, `metal`, `vulkan` | `.ai/constraints/hardware/{value}/` | Optional (Phase 2) |
| `external_dependencies` | `none`, `system_cuda`, `system_nvidia`, `vendored` | Guidance in dependency wrapper | Optional (Phase 2) |

### Constraint Loading Algorithm

The new loader in [session_init.py](../../.ai/scripts/session_init.py) works as follows:

1. Load all `.ai/constraints/common/` constraints (unchanged)
2. For each value in `language`, load `.ai/constraints/{language}/` constraints
3. If `bindings` is set and not `none`, load `.ai/constraints/bindings/{bindings}/`
4. If `distribution` is set and not `none`, load `.ai/constraints/distribution/{distribution}/`
5. For each value in `hardware_targets`, load `.ai/constraints/hardware/{hardware}/`
6. Apply file-extension triggers (`.py` -> `python/formatting`, `.cu` -> `cpp/cuda`) as before

This is **additive composition**: a hybrid project gets both Python and C++ constraints, plus binding-specific constraints, plus distribution-specific constraints.

### Build System Dispatch

The `build_system` axis drives `bin/agent-build` dispatch:

```bash
case "$build_system" in
  poetry)
    # Existing Poetry path (setup -> poetry install, test -> poetry run pytest)
    ;;
  cmake)
    # Existing CMake+Conan path (setup -> conan install, compile -> cmake --build)
    ;;
  scikit-build)
    # Phase 2: pip install -e ., pytest, wheel build
    echo "scikit-build not yet implemented in this phase" >&2
    exit 1
    ;;
  bazel)
    # Phase 2: bazel build, bazel test
    echo "bazel not yet implemented in this phase" >&2
    exit 1
    ;;
  mixed)
    # Phase 2: orchestrate multiple build systems (e.g., CMake for C++, Poetry for Python wrapper)
    echo "mixed not yet implemented in this phase" >&2
    exit 1
    ;;
esac
```

Phase 1 keeps `poetry` and `cmake` paths exactly as-is. New build systems are stubs that exit non-zero with a clear message.

### Capability Audit Selectors

The new [capabilities.yml](../../.ai/capabilities.yml) schema uses `when:` selectors:

```yaml
common_requirements:
  project_skills:
    - id: python-env-setup
      required: true
      when: language=python

    - id: bazel
      required: true
      when: build_system=bazel
```

The capability audit evaluates selectors against the active profile. Legacy `project_types: [python]` is rewritten as `when: language=python` during Phase 1 migration.

## Worked Examples

### Example 1: Pure Python Project (Legacy Compatible)

**Legacy `.ai/project.yml`:**
```yaml
project_type: python
```

**New `.ai/project.yml`:**
```yaml
project_profile:
  language: [python]
  build_system: poetry
```

**Backward-compat shim:** The legacy `project_type: python` is automatically mapped to the new profile above. No file change required.

**Loaded constraints:**
- `.ai/constraints/common/*`
- `.ai/constraints/python/*`
- File-extension triggers (`.py` -> `python/formatting`, `python/type-checking`)

**Build dispatch:** `bin/agent-build` routes to Poetry (`poetry install`, `poetry run pytest`)

### Example 2: Pure C++/CUDA Project (Legacy Compatible)

**Legacy `.ai/project.yml`:**
```yaml
project_type: cpp
```

**New `.ai/project.yml`:**
```yaml
project_profile:
  language: [cpp]
  build_system: cmake
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
```

**Backward-compat shim:** The legacy `project_type: cpp` is automatically mapped to the new profile above.

**Loaded constraints:**
- `.ai/constraints/common/*`
- `.ai/constraints/cpp/*`
- File-extension triggers (`.cu` -> `cpp/cuda`, `.cpp` -> `cpp/formatting`)

**Build dispatch:** `bin/agent-build` routes to CMake+Conan (`conan install`, `cmake --build`)

### Example 3: Hybrid TVM-Shaped Project (Phase 2)

**New `.ai/project.yml`:**
```yaml
project_profile:
  language: [python, cpp]
  build_system: scikit-build-core
  bindings: tvm-ffi
  distribution: pypi-wheel
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
```

**Loaded constraints (Phase 2):**
- `.ai/constraints/common/*`
- `.ai/constraints/python/*`
- `.ai/constraints/cpp/*`
- `.ai/constraints/bindings/tvm-ffi/*` (Phase 2)
- `.ai/constraints/distribution/pypi/*` (Phase 2)
- `.ai/constraints/hardware/cuda/*` (Phase 2, if split from `cpp/cuda.md`)
- File-extension triggers for both `.py` and `.cu`

**Build dispatch (Phase 2):** `bin/agent-build` routes to scikit-build-core (`pip install -e .`, `pytest`, `python -m build`)

**Capability audit (Phase 2):** Requires both `python-env-setup` (when `language=python`) and `bazel` is NOT required (when `build_system=scikit-build`)

## Backward Compatibility

This is the **hard invariant** of Phase 1. Every existing project must continue to work without any change.

### Legacy Mapping Table

| Legacy `project_type` | Equivalent `project_profile` |
|-----------------------|------------------------------|
| `python` | `language: [python]`, `build_system: poetry` |
| `cpp` | `language: [cpp]`, `build_system: cmake`, `hardware_targets: [cuda, cpu]`, `external_dependencies: system_cuda` |

### Shim Implementation

The file [.ai/scripts/project_type.py](../../.ai/scripts/project_type.py) is renamed to [.ai/scripts/project_profile.py](../../.ai/scripts/project_profile.py). The old path is retained as a thin import shim:

```python
# .ai/scripts/project_type.py (shim)
from .project_profile import ProjectProfile, detect, legacy_project_type_to_profile

# Re-export legacy API
ProjectType = ProjectProfile  # Alias for backward compat
```

The new `legacy_project_type_to_profile()` function maps legacy values:

```python
def legacy_project_type_to_profile(project_type: str) -> dict:
    if project_type == "python":
        return {
            "language": ["python"],
            "build_system": "poetry",
        }
    elif project_type == "cpp":
        return {
            "language": ["cpp"],
            "build_system": "cmake",
            "hardware_targets": ["cuda", "cpu"],
            "external_dependencies": "system_cuda",
        }
    else:
        raise ValueError(f"Unknown legacy project_type: {project_type}")
```

### Verification Strategy

Phase 1 task-1-8 requires running a real Python project (consuming this template) through the post-Phase-1 template and verifying:

1. `bin/agent-init` produces identical loaded constraint sets (round-trip test)
2. `bin/agent-build full` completes successfully
3. `bin/agent-dependency add <package>` works identically
4. `bin/agent-precommit` passes
5. Capability audit passes with identical required skills

If any drift is detected, it is a Phase 1 blocker and must be fixed before the PR is opened.

## Consequences

### Positive

1. **Unlocks Phase 2**: Hybrid Python+C++/CUDA projects can now be expressed without combinatorial enum explosion
2. **Composable**: New axes (bindings, distribution, hardware) can be added without touching the loader logic
3. **Backward compatible**: Existing projects continue to work with zero changes
4. **Explicit**: The profile makes all project dimensions visible in one place
5. **Testable**: Round-trip tests prove equivalence between legacy and new schemas

### Negative

1. **Migration complexity**: The shim adds a translation layer that must be maintained until all projects migrate
2. **Schema validation**: The new profile schema is more complex and requires validation (Phase 1 task-1-2)
3. **Documentation burden**: Both legacy and new schemas must be documented until legacy is deprecated
4. **Capability audit complexity**: The `when:` selector evaluation adds logic to the audit script

### Neutral

1. **No constraint content changes**: Phase 1 only refactors loaders; constraint bodies under `.ai/constraints/` are unchanged
2. **No new skills**: Phase 1 does not add new skills; it only refactors how existing skills are selected
3. **No new build systems**: Phase 1 stubs out new build systems; Phase 2 implements them

### Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Shim silently changes loaded constraints | Round-trip tests in task-1-8 (mandatory) |
| Schema design flaw surfaces in Phase 2 | User-gate after task-1-1 (this ADR) for review |
| Real project breaks on post-Phase-1 template | Exit criteria require real-world verification |
| Capability audit drops a required skill | Fixture tests in task-1-4 assert audit equality |

### Migration Path

**Phase 1 (this phase):**
- Legacy `project_type` continues to work via shim
- New `project_profile` is optional
- Both schemas coexist

**Phase 2:**
- New constraint content (bindings, distribution, hardware) requires `project_profile`
- Legacy `project_type` still works for pure Python/C++ projects
- Hybrid projects must use `project_profile`

**Phase 3 (future):**
- Deprecation warning added for legacy `project_type`
- Migration guide published
- Legacy shim remains for backward compatibility

**No forced migration**: Projects can stay on legacy `project_type` indefinitely if they do not need hybrid features.

## Alternatives Considered

### Alternative 1: Extend the Binary Enum

Add more `project_type` values: `python_cpp_cuda`, `python_cpp_cuda_tvm`, `python_cpp_cuda_mlc`, etc.

**Rejected because:**
- Combinatorial explosion: 2 languages x 5 build systems x 4 bindings x 3 distributions = 120 enum values
- Couples unrelated concerns (language + build system + bindings)
- Does not scale to future axes (hardware backends, distribution targets)

### Alternative 2: Side-Channel Configuration

Keep `project_type: python` but add separate fields: `build_system: scikit-build`, `bindings: nanobind`, etc.

**Rejected because:**
- Ambiguous semantics: Does `project_type: python` with `bindings: nanobind` load C++ constraints?
- Backward compatibility unclear: What if a legacy project has no `build_system` field?
- Constraint loader logic becomes a maze of conditionals

### Alternative 3: Rewrite Constraint System

Replace the file-based constraint system with a database or DSL.

**Rejected because:**
- Out of scope for Phase 1 (and Phase 2)
- High risk: would break all existing projects
- No clear benefit over composition-based loading

### Alternative 4: Multiple `project_type` Values

Allow `project_type: [python, cpp]` as a list.

**Rejected because:**
- Does not solve the build system problem (Poetry vs scikit-build for Python)
- Does not solve the bindings problem (nanobind vs pybind11)
- Still couples language to other concerns

## Implementation Plan

Phase 1 tasks (see [roadmap.yml](../agent_roadmaps/phase-1-profile-architecture/roadmap.yml)):

1. **task-1-1**: Write this ADR (current task) -> **USER GATE: explicit approval required**
2. **task-1-2**: Rename `project_type.py` to `project_profile.py`, implement schema reader, add shim
3. **task-1-3**: Refactor `session_init.py` to load constraints by profile axes
4. **task-1-4**: Refactor `capabilities.yml` to use `when:` selectors
5. **task-1-5**: Refactor `bin/agent-build` to dispatch by `build_system`
6. **task-1-6**: Refactor `bin/agent-dependency` to dispatch by profile
7. **task-1-7**: Add migration note to `templates/python/CLAUDE.md` and `templates/cpp/CLAUDE.md`
8. **task-1-8**: Verify backward compatibility on a real Python project

## References

- [Phase 1 ROADMAP.md](../agent_roadmaps/phase-1-profile-architecture/ROADMAP.md)
- [Phase 1 INVARIANTS.md](../agent_roadmaps/phase-1-profile-architecture/INVARIANTS.md)
- [Current session_init.py](../../.ai/scripts/session_init.py)
- [Current project_type.py](../../.ai/scripts/project_type.py)
- [Current capabilities.yml](../../.ai/capabilities.yml)
- Apache TVM: https://github.com/apache/tvm
- MLC-LLM: https://github.com/mlc-ai/mlc-llm
- FlashInfer: https://github.com/flashinfer-ai/flashinfer
