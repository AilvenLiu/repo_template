# C++ First Policy

> **This document defines the C++ First design principle for C++/CUDA and Hybrid projects.**
> It is a mandatory, non-negotiable architectural constraint.
> Violations are considered critical design failures.

## Overview

For all C++/CUDA and Hybrid (Python + C++/CUDA) projects, **C++ is the primary and
default implementation language**. Python exists only to expose C++ functionality
externally — as a binding layer, a thin wrapper, or a wheel delivery mechanism.

This policy prevents the common anti-pattern of implementing core logic in Python and
calling C++ only for performance-critical hot paths. The rule is simpler and more
absolute: core logic goes in C++ first, always.

## 1. The Rule

### 1.1 C++ Owns the Core

**MANDATORY**: All of the following MUST be implemented in C++:

- Core algorithms and data structures
- Computational kernels (CUDA or CPU-bound)
- State management and business logic
- I/O abstractions and protocol handling
- Error types and error propagation logic
- Configuration validation and parsing (beyond trivial)
- Mathematical operations and numerical routines
- Memory management and resource lifecycle

### 1.2 Python is Permitted Only For

Python code in a Hybrid project is permitted **only** for these purposes:

| Permitted | Examples |
|-----------|---------|
| Binding layer | pybind11 / nanobind `NB_MODULE` / `PYBIND11_MODULE` definitions |
| Python-facing type stubs | `.pyi` stub files |
| CLI entry points | `argparse` / `click` thin dispatch — must delegate to C++ |
| Build configuration | `pyproject.toml`, `CMakeLists.txt` integration via scikit-build-core |
| Test orchestration | `pytest` wrappers that call C++ extension functions |
| Package metadata | `__init__.py` re-exports, `__version__`, `__all__` |
| Configuration loading | Parsing YAML/JSON/TOML to pass into C++ structs (thin) |

**Every item above must be thin.** If a Python file grows beyond wiring/dispatch,
that growth is a signal the logic should be in C++.

### 1.3 Prohibited Python Usage

**FORBIDDEN** in Hybrid and C++/CUDA projects:

- Implementing algorithms in Python that could be in C++
- Holding application state in Python objects instead of C++ structs
- Writing Python classes that duplicate C++ class functionality
- Using NumPy / PyTorch / JAX for core computation when a C++ kernel is possible
- Calling C++ functions from Python in a loop that Python controls (loop should be C++)
- Implementing retry logic, error recovery, or fallback policies in Python
- Growing Python utility modules that are not bindings

### 1.4 Design Order

When designing a new feature:

1. **Design the C++ interface first** — types, functions, error codes
2. **Implement in C++** — unit-tested with Google Test / Catch2
3. **Expose via nanobind / pybind11** — minimal binding code only
4. **Write Python tests** — thin pytest wrappers calling the C++ extension
5. **Never start from the Python side** and work downward into C++

## 2. Rationale

### 2.1 Performance and Determinism

C++ code:
- Has predictable performance (no GC pauses, no interpreter overhead)
- Can be compiled with `-O3`, PGO, LTO
- Has full SIMD / intrinsic access
- Interoperates directly with CUDA without marshalling overhead

Python reimplementations of the same logic will always be slower and less
predictable, even with NumPy vectorisation.

### 2.2 Portability

A C++ core can be:
- Wrapped for Python (pybind11 / nanobind)
- Called from Rust, Go, or Swift via FFI
- Compiled to WASM
- Deployed on embedded systems without a Python runtime

A Python core cannot be ported to any of these targets without a rewrite.

### 2.3 Ecosystem Interoperability

Python wheels with C++ extensions can be distributed via PyPI and installed with
`pip install` — the Python binding is the distribution mechanism, not the
implementation language.

## 3. Code Review Checklist

When reviewing Hybrid project code, check:

- [ ] Is new logic in C++ or Python? If Python: is it binding/wiring only?
- [ ] Does the C++ function have unit tests (Google Test / Catch2)?
- [ ] Is the Python binding thin (< ~30 lines per exposed function/class)?
- [ ] Are Python `pytest` files calling C++ extension functions, not reimplementing logic?
- [ ] Are there any Python utility modules that should be C++ headers?
- [ ] Is any application state held in Python dicts/lists instead of C++ structs?

## 4. Migration Guidance

When you encounter Python logic that violates this policy:

1. **Identify the C++ equivalent** — what struct/function would this be?
2. **Write the C++ implementation** with unit tests
3. **Write a nanobind binding** for the new C++ code
4. **Replace the Python implementation** with a call through the binding
5. **Delete the Python implementation** — do not leave it as a fallback

Do not leave Python implementations in place "for compatibility" or "as a fallback".
The C++ implementation is the only implementation.

## 5. Allowed Exceptions

The only exceptions to C++ First are:

| Exception | Condition |
|-----------|-----------|
| External Python-only library | The library has no C++ equivalent and a C++ port is not feasible (e.g., a specific HTTP framework used only in tests) |
| Prototyping step | Code is explicitly labelled as a prototype (`# PROTOTYPE: move to C++ before merge`) and removed before the PR merges |

Neither exception permits Python in production paths. Both require explicit user approval.

## 6. Enforcement

This constraint is enforced through:

1. **Agent behaviour**: When asked to implement a feature, the agent proposes a C++
   implementation first. If the user asks for a Python implementation of core logic,
   the agent MUST flag the violation and ask for confirmation before proceeding.

2. **Code review**: Reviewers check that Python files are binding/wiring only.

3. **Architecture decisions**: Any decision to put significant logic in Python MUST be
   documented in an ADR with explicit justification and user approval.

**When asked to add Python code that violates this policy, the agent MUST**:
1. State clearly that the requested Python code violates the C++ First constraint
2. Propose the C++ implementation instead
3. Ask whether the user wants to proceed with C++ or has a documented exception
4. NOT silently implement the Python version

## 7. Relationship to FFI Boundary Constraint

The `hybrid/ffi-boundary` constraint defines *how* to cross the Python/C++ boundary
correctly (GIL management, DLPack, error propagation). This constraint defines *what*
lives on each side of that boundary.

Both constraints apply simultaneously. C++ First determines where logic lives;
FFI Boundary determines how the binding is written.
