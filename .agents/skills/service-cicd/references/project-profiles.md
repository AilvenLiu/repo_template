# CI build ownership by project profile

Read `.agents/project.yml` and the repository's build skill before designing the
matrix. GitHub Actions invokes the authoritative graph; it does not redefine it.

## Pure Python

- Use Poetry to create the environment, synchronize locked dependencies, and
  run format, lint, type, test, and package commands.
- Build wheels or source distributions in CI and test the built artefact in a
  clean job before publication or deployment.
- Do not install application dependencies with ad hoc system `pip` commands.

## Pure C++ or CUDA

- Configure, build, install/package, and test through CMake with Ninja. CPM
  remains the default lightweight dependency mechanism.
- Matrix entries declare OS, architecture, compiler, build type, and CUDA
  compatibility where applicable. Cache acceleration must not become the only
  source of a dependency or overwrite release identity.
- CPU-native configure/build/ctest remains required even when CUDA execution is
  unavailable. Put real GPU tests on labelled compatible runners and state any
  approved omission explicitly.

## Hybrid Python and C++ or CUDA

- Run direct CMake configure, native build, and CTest first.
- Use scikit-build-core only to bridge that CMake-owned graph into Python
  packaging. Poetry owns the Python environment and Python dependencies.
- Test wheel installation/import, native symbol loading, representative FFI
  calls and errors, and ABI/platform compatibility before promotion.

## Release matrix

Prefer one immutable artefact per target platform or ABI. A manifest must map
each target to its digest and compatibility envelope. Do not label one runner's
success as validation for a different architecture, ABI, or GPU generation.
