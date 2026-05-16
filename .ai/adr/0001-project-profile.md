# ADR 0001: Project Profile Composition

**Status**: Active
**Date**: 2026-05-10
**Authors**: Template maintainers

## Summary

The template uses a composable `project_profile` in `.ai/project.yml` so
constraint loading, capability audit, and workflow dispatch can adapt to pure
Python, pure C++/CUDA, and hybrid AI-infrastructure repositories without
copying roadmap history into durable project files.

## Decision

Prefer a profile made from independent axes instead of a single binary project
type flag.

```yaml
project_profile:
  language: [python, cpp]
  build_system: scikit-build-core
  bindings: nanobind
  distribution: pypi-wheel
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
```

## Rationale

- Hybrid repositories need both Python and C++/CUDA constraints at the same time.
- Build-system selection is independent from language selection.
- Capability audit should enable only the skills a generated project actually needs.
- Durable project files must stay free of temporary roadmap-stage identifiers.

## Loader Behaviour

`session_init.py` loads:

1. Always-on common constraints
2. Language constraints for every language listed in `project_profile.language`
3. Hybrid constraints when both Python and C++ are present
4. File-triggered constraints based on the files being edited

## Compatibility

Legacy `project_type: python` and `project_type: cpp` values continue to map to
equivalent profile shapes so existing projects still load the same constraint
sets.

## Examples

### Pure Python

```yaml
project_profile:
  language: [python]
  build_system: poetry
```

### Pure C++/CUDA

```yaml
project_profile:
  language: [cpp]
  build_system: cmake
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
```

### Hybrid AI Infra

```yaml
project_profile:
  language: [python, cpp]
  build_system: scikit-build-core
  bindings: nanobind
  distribution: pypi-wheel
  hardware_targets: [cuda, cpu]
  external_dependencies: system_cuda
```

## Consequences

- Generated Python, C++/CUDA, and hybrid projects share one loader model.
- Claude Code and Codex consume the same project profile and constraint graph.
- Temporary roadmap workflow may be used during implementation, but roadmap
  state must remain confined to `agent_roadmaps/` and be deleted when fully
  complete.
