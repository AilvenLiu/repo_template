# C++/CUDA Dependency Management

> This document defines mandatory dependency management standards for C++/CUDA
> and hybrid Python/C++/CUDA projects.

## Core Invariant

For pure C++/CUDA and hybrid projects:

```text
CMake owns the native build graph.
CPM owns lightweight C++ dependency acquisition.
scikit-build-core bridges CMake into Python packaging.
Poetry owns Python virtualenv and Python dependencies only.
pip install -e . is not the authoritative C++ build command.
```

C++/CUDA owns core libraries, runtime kernels, native executables, C++ tests,
CUDA tests, benchmarks, compile/link options, third-party C++ dependencies,
ABI-sensitive configuration, install rules, and export targets.

Python owns only thin bindings, wrapper APIs, Python packaging metadata,
Python-side tests, wheel exposure, and developer environment management.

## Required Native Workflow

Agents must make direct CMake builds correct before optimising Python packaging:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build -j
ctest --test-dir build --output-on-failure
```

For hybrid projects, enable the Python binding target during the native build:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo -DPROJECT_ENABLE_PYTHON=ON
cmake --build build -j
ctest --test-dir build --output-on-failure
```

Only after that passes may agents validate Python exposure:

```bash
poetry run pip install -e . --no-build-isolation
poetry run python -c "import PROJECT_NAME; print(PROJECT_NAME)"
poetry run pytest tests/python
```

## CPM First

CPM.cmake is the default mechanism for third-party C++ dependencies that are
part of the native build graph.

Use CPM when the dependency is source-buildable by CMake, exposes modern CMake
targets or can be wrapped cleanly, can be pinned by immutable tag/commit/archive
hash, is not a large binary SDK, does not require complex binary resolution,
and is acceptable to build from source.

Do not use CPM blindly for binary/system dependencies such as CUDA Toolkit,
TensorRT, cuDNN, NCCL, OpenMPI/HPC modules, proprietary SDKs, compiler
toolchains, system drivers, platform runtimes, or large prebuilt inference
engines. Discover those with `find_package`, explicit CMake cache variables,
environment-provided paths, or documented toolchain files.

## Required Layout

Pure C++/CUDA and hybrid projects must include:

```text
cmake/
  CPM.cmake
  Dependencies.cmake
  Options.cmake
  Toolchains/
3rdparty/
  README.md
  .gitkeep
  cpm-cache/
    .gitkeep
```

Hybrid projects additionally keep Python bindings under `bindings/python/` and
thin Python package files under `python/PROJECT_NAME/`.

The project-local CPM source cache is:

```cmake
set(CPM_SOURCE_CACHE
    "${CMAKE_SOURCE_DIR}/3rdparty/cpm-cache"
    CACHE PATH "CPM source cache")
```

`3rdparty/cpm-cache/` should normally be ignored by Git except for `.gitkeep`.
Patches belong under `3rdparty/patches/`; licence notes belong under
`3rdparty/licenses/`.

## Dependency Declarations

All CPM dependencies must be declared in `cmake/Dependencies.cmake` and pinned.
Floating branches such as `main`, `master`, and `develop` are forbidden.

Allowed:

```cmake
GIT_TAG v1.2.3
GIT_TAG 4f3c2a1b9d0e...
URL_HASH SHA256=<hash>
```

Forbidden:

```cmake
GIT_TAG main
GIT_TAG master
GIT_TAG develop
```

Example:

```cmake
set(CPM_SOURCE_CACHE
    "${CMAKE_SOURCE_DIR}/3rdparty/cpm-cache"
    CACHE PATH "CPM source cache")

CPMAddPackage(
  NAME fmt
  GITHUB_REPOSITORY fmtlib/fmt
  GIT_TAG 10.2.1
  OPTIONS
    "FMT_INSTALL ON"
)

CPMAddPackage(
  NAME googletest
  GITHUB_REPOSITORY google/googletest
  GIT_TAG v1.14.0
  OPTIONS
    "INSTALL_GTEST OFF"
)
```

Prefer CMake targets:

```cmake
target_link_libraries(my_target
  PRIVATE
    fmt::fmt
)
```

Do not use raw include directories or raw library paths when an imported or
exported CMake target exists.

## Dependency Addition Metadata

Every dependency addition must record:

- name
- upstream URL
- pinned version, commit, or archive hash
- reason for inclusion
- linked CMake target
- licence note
- whether it is runtime, build-time, test-only, or benchmark-only

For non-trivial dependency changes, add or update an ADR under `.ai/adr/`.

## Exceptions

Git submodules are disallowed by default for C++ dependencies. An exception
requires an ADR and must preserve the exact upstream commit, document local
patches under `3rdparty/patches/`, and explain why CPM is impractical.

Conan, vcpkg, and Bazel are not default dependency managers for this template.
Use them only with an ADR when binary package management, vcpkg toolchain
coverage, or a Bazel-first monorepo build graph is an explicit project decision.

## Enforcement Checklist

- [ ] `cmake/CPM.cmake`, `cmake/Dependencies.cmake`, and `cmake/Options.cmake` exist.
- [ ] `3rdparty/cpm-cache/.gitkeep` exists and generated cache contents are ignored.
- [ ] New C++ dependencies are declared in `cmake/Dependencies.cmake`.
- [ ] Every dependency is pinned by immutable version information.
- [ ] Root `CMakeLists.txt` includes options, CPM, and dependencies before targets.
- [ ] Direct CMake configure, build, and `ctest` pass before Python editable install.
