---
name: gpu-ci
description: Design or review GPU-aware CI for CUDA builds, tests, caches, containers, and Python wheels. Use when hardware targets include CUDA, distribution uses wheels, or CI needs GPU runner gating, multi-architecture coverage, or manylinux validation.
---

# GPU CI

Design the pipeline from the active project profile, then use repository-owned
build and dependency workflows. CI must reinforce the build authority; it must
not create a second build system.

## Load the contract

1. Read `.agents/project.yml`, the session constraint manifest, and the `build`,
   `dependency`, and `service-cicd` skills when release automation is in scope. Read `deploy-service` as well when host activation is in scope.
2. Read the applicable CMake, CUDA, hybrid bridge, dependency, and testing
   constraints before drafting jobs.
3. Classify each job as CPU validation, CUDA compilation, GPU execution,
   wheel repair, or publication. Do not disguise a missing GPU runner by silently
   skipping a required release gate.
4. Record the supported OS, compiler, CUDA toolkit, GPU architecture, Python ABI,
   and wheel-platform matrix. Every axis must map to a supported product target.

## Preserve build ownership

For pure C++/CUDA projects, CMake owns configure, compilation, native tests,
CUDA architectures, dependencies, installation, and export targets. Exercise the
same direct lifecycle as the build skill:

```bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

For hybrid projects, run that direct CMake lifecycle first. Only after it passes,
use scikit-build-core as the packaging bridge and Poetry as the Python environment:

```bash
poetry install
poetry run pip install -e . --no-build-isolation
poetry run pytest tests/python
```

The bridged editable install above is the repository's explicit hybrid exception;
it is not native build authority. Do not use `python -m build`, setuptools native
extensions, direct `pip install`, or host-side compilation as a substitute for the
profile workflow. Add Python build tools through `.agents/bin/agent-dependency`.

## Make the GitHub Actions boundary explicit

- Pin every third-party action to a reviewed full commit SHA and annotate the
  human-readable release tag. A mutable major, version, branch, or floating tag is
  not a security pin.
- Give `GITHUB_TOKEN` the smallest job-level permissions. Pull-request jobs must
  not receive publication, cloud, package-index, or production credentials.
- Separate untrusted validation, trusted build, GPU test, signing/attestation,
  and publication jobs when their permissions differ.
- Protect publication with a GitHub environment, required reviewers where
  appropriate, and environment-scoped concurrency.
- Pin runner images, CUDA containers, compiler toolchains, and Python versions to
  reviewed versions or immutable digests where the platform supports it.
- Upload immutable outputs once. Carry digests and provenance between jobs; do not
  rebuild for publication.

Use this shape, replacing each placeholder with a reviewed current full SHA:

```yaml
permissions:
  contents: read

jobs:
  build:
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@<FULL_40_CHARACTER_COMMIT_SHA> # reviewed release
      - name: Validate native build
        run: .agents/bin/agent-build full
      - uses: actions/upload-artifact@<FULL_40_CHARACTER_COMMIT_SHA> # reviewed release
        with:
          name: wheels-${{ matrix.python }}-${{ matrix.cuda }}
          path: dist/*.whl
          if-no-files-found: error
```

Never copy placeholder SHAs into a real workflow. Resolve them from the official
action repository at implementation time and preserve the tag annotation for
automated update tooling.

## Cache CUDA compilation safely

Configure `sccache` through CMake rather than wrapping the build externally:

```cmake
set(CMAKE_CXX_COMPILER_LAUNCHER sccache)
set(CMAKE_CUDA_COMPILER_LAUNCHER sccache)
```

Cache keys must include at least source revision or dependency-lock digest,
compiler identity, CUDA toolkit version, target architectures, build type, and
ABI-affecting options. Treat remote cache credentials as write-capable secrets;
do not expose them to forked pull requests. A cache miss must affect performance,
not correctness.

## Test the hardware matrix honestly

- Compile every supported CUDA architecture in a controlled build matrix.
- Run CPU-only tests on ordinary runners and device tests only on explicitly
  labelled GPU runners.
- Assert the observed GPU model, compute capability, driver, and toolkit before
  executing hardware-specific tests.
- Mark an unsupported runner as a failed required job, not a successful skip.
  Optional informational coverage may skip only when the job is declared optional.
- Test kernel launch errors, synchronization errors, boundary sizes, odd shapes,
  non-contiguous inputs, dtype/device mismatches, and CPU-reference correctness.
- Preserve GPU diagnostics, test reports, and environment metadata as artefacts on
  failure without leaking credentials.

## Build and validate wheels

For hybrid wheels:

1. Validate direct CMake configure/build/CTest first.
2. Build each declared Python ABI and CUDA variant in a pinned manylinux-compatible
   image through the repository's Poetry/scikit-build-core bridge.
3. Inspect wheel tags and native dependencies before repair.
4. Run `auditwheel show`, then repair with an explicit library policy. Do not apply
   a blanket rule that all CUDA libraries must or must not be bundled; derive the
   policy from licensing, manylinux, driver compatibility, package-index, and
   runtime support contracts.
5. Install the final wheel in a clean test environment and run import, CPU fallback,
   GPU smoke, ABI, and minimal application tests against the repaired artefact.
6. Sign or attest the exact digest that publication consumes.

Never rename a built wheel by string substitution to change its version or ABI
tags. Set versions through packaging metadata before the build and let the backend
produce standards-compliant filenames.

## Adversarial review

Challenge at least these cases before release:

- a fork edits the workflow or cache key while secrets exist
- a cache object was produced by another compiler, CUDA version, or architecture
- the runner label says GPU but the observed model or driver is incompatible
- compilation succeeds although no required kernel executed
- wheel repair bundles a forbidden runtime or drops a required shared library
- publication rebuilds or uploads a different digest than the tested wheel
- two release runs publish the same version or race on an index
- CPU fallback masks an accidentally missing CUDA extension

Report the matrix, build authority, trust boundaries, immutable pins, artefact
digests, hardware evidence, wheel inspection, and every check that could not run.
