# Hybrid Python/C++/CUDA Build and Packaging

> CMake owns the native build graph. scikit-build-core bridges that graph into
> Python packaging. Poetry owns the Python environment and Python dependencies.
> This ownership order is mandatory.

## Ownership boundary

CMake owns:

- C++ and CUDA libraries, executables, kernels, tests, and benchmarks
- compiler and linker options, CUDA architectures, ABI flags, and feature probes
- native dependencies, generated native sources, install rules, and exports

Python packaging owns only:

- binding exposure and thin Python wrappers
- package metadata and wheel layout
- Python-side dependencies and tests
- invoking the already-correct CMake graph through scikit-build-core

`setup.py`, setuptools extension definitions, ad hoc compiler subprocesses, and
Python-authored native dependency discovery are forbidden. They create a second
native build graph.

## Required direct-native gate

Before any editable install or wheel build, validate CMake directly:

```bash
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DPROJECT_ENABLE_PYTHON=ON
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

The binding target must link to the same native library targets used by native
tests. Do not compile duplicate source lists specifically for Python.

Only after the direct gate passes may the repository validate Python exposure:

```bash
poetry install
poetry run pip install -e . --no-build-isolation
poetry run pytest tests/python
```

The editable-install command is the one explicit bridge exception. It is not a
general dependency-installation mechanism and never replaces direct CMake
validation.

## Canonical pyproject bridge

Use scikit-build-core as the build backend and keep native configuration small:

```toml
[build-system]
requires = ["scikit-build-core"]
build-backend = "scikit_build_core.build"

[tool.scikit-build]
cmake.build-type = "Release"
wheel.packages = ["python/project_name"]
```

Declare Python dependencies through Poetry and change them only with
`.agents/bin/agent-dependency`. Do not encode compiler flags, dependency fetching,
CUDA architecture policy, native test topology, or install/export semantics in
`pyproject.toml`.

## Binding boundary

- Put bindings under `bindings/python/` and thin package code under
  `python/project_name/`.
- Translate native errors at the boundary without discarding type or context.
- State ownership and lifetime for every borrowed buffer, view, capsule, pointer,
  and callback.
- Release the GIL only when native code cannot call Python and all accessed state
  is safe without it. Reacquire it before any Python API call.
- Validate dtype, rank, shape, stride, alignment, device, stream, and mutability
  before passing array or tensor memory into native code.
- Avoid Python-controlled loops over native operations; expose a batched C++ API.

## ABI and CUDA compatibility

Treat these as explicit inputs to the release matrix:

- operating system and manylinux baseline
- CPU architecture
- compiler family and runtime ABI
- Python version and ABI tag
- C++ standard-library ABI when an upstream framework imposes one
- CUDA toolkit, driver floor, GPU architectures, and optional runtime libraries

Derive ABI definitions in CMake from authoritative discovered targets or
documented probes. Never mirror ABI logic in a legacy packaging script. Reject an
incompatible host before replacing a live service or publishing a wheel.

For CUDA, set `CMAKE_CUDA_ARCHITECTURES` explicitly and test every supported
architecture. Do not use `native` for release artefacts or assume the build
runner's GPU represents the supported fleet.

## Wheel construction

1. Run the direct-native gate.
2. Build in a pinned, manylinux-compatible environment for each declared matrix
   entry through Poetry and scikit-build-core.
3. Inspect the produced filename tags and native dependencies.
4. Apply an explicit auditwheel repair/exclusion policy based on licensing,
   runtime compatibility, and support commitments.
5. Install the final wheel into a clean Poetry-managed validation project and run
   import, CPU fallback, ABI, and GPU smoke tests against that exact wheel.
6. Publish, sign, or attest the tested digest without rebuilding it.

Do not rename wheel files to manufacture version, CUDA, Python, ABI, or platform
tags. Configure version metadata before building and let the backend generate a
standards-compliant filename.

## GitHub Actions requirements

- Pin all third-party actions to reviewed full commit SHAs, with a tag comment for
  update tools. Do not use mutable `@vN`, branch, or floating tags.
- Separate pull-request validation from credentialed build and publication jobs.
- Give each job minimum `GITHUB_TOKEN` permissions.
- Protect publication with an environment and environment-scoped concurrency.
- Commit the tested wheel once to the server-local artefact store and propagate
  its record id, digest, and provenance to publication.
- GitHub Actions artefact storage is default-deny; use it only when the local
  store and fixed transfer cannot work and the current user explicitly requests
  the one-day, non-rollback exception in `artifact-storage.md`.
- Preserve CMake, CTest, wheel-inspection, and GPU diagnostics in ordinary
  workflow logs, job summaries, or a bounded local diagnostic store on failure.

Illustrative shape only; resolve placeholders from official action repositories:

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@<FULL_40_CHARACTER_COMMIT_SHA> # reviewed release
  - name: Validate direct native graph
    run: .agents/bin/agent-build full
  - name: Commit tested wheel to the server-local artefact store
    run: >-
      ./ci/commit-artifact --path dist --source-sha "${GITHUB_SHA}"
      --workflow-run-id "${GITHUB_RUN_ID}" --source-ref "${GITHUB_REF}"
```

The `ci/commit-artifact` path is illustrative: each project must provide its
reviewed fixed host helper. It must validate the immutable event identity,
write a digest-bearing manifest, derive the release id, and apply the rolling
policy. It must not use the supplied ref to select or escape the trusted store.
Read `.agents/skills/service-cicd/references/artifact-storage.md` for its
required path, identity, and retention contract.

## Test topology

Native tests own core behavior, error paths, resource lifetime, concurrency, and
CUDA kernel correctness. Python tests own binding conversion, exception mapping,
packaging/import behavior, and thin user-facing wrappers. Cross-boundary tests
must cover:

- invalid dtype, shape, stride, device, and lifetime
- native exception translation and message context
- reference ownership and garbage collection
- concurrent calls and GIL behavior
- wheel import without a source tree present
- CPU-only behavior when CUDA is optional
- required-GPU failure when CUDA support is promised

## Forbidden shortcuts

- making editable installation the authoritative native build
- defining native sources or compiler flags in Python packaging code
- direct dependency installation outside the guarded workflow
- committing generated binaries, build trees, or an uncontrolled CPM cache
- downloading compilers, CUDA, or binary SDKs through CPM
- silently skipping required native, ABI, wheel, or GPU tests
- publishing a rebuild rather than the artefact that passed validation
- copying mutable action tags into CI examples

Run `.agents/bin/agent-build full`, `.agents/bin/agent-precommit`, and
`.agents/bin/agent-check-constraints` before handoff, or state precisely why a gate
could not run.
