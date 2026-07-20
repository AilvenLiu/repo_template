# Project-profile artefact and host compatibility

The CI/CD workflow owns build and test. Host deployment accepts only its
immutable output and verifies compatibility before changing the live service.
For GitHub Actions build ownership, read `$service-cicd`.

## Pure Python

- Deploy a CI-built wheel, archive, or container with locked dependency and
  Python ABI metadata. Do not run Poetry or pip during production activation.
- If a container copies a virtual environment from a builder stage, builder and
  runtime paths plus interpreter ABI must match.
- Treat migrations as explicit serialized release operations. Record backward
  compatibility before allowing automatic rollback.

## Pure C++ or CUDA

- Deploy a CMake-built archive or immutable container with target OS,
  architecture, compiler/runtime ABI, shared-library, and CUDA compatibility.
- Include executable, libraries, resources, licences, and service metadata in
  one release. Do not compile or resolve CPM dependencies on the host.
- Treat the NVIDIA driver as a host prerequisite. Do not silently bundle or
  replace it. When GPU execution is required, health must eventually cover
  device discovery and a representative kernel; process liveness is inadequate.

## Hybrid Python and C++ or CUDA

- Deploy a CI-built wheel, archive, or container whose native graph was already
  validated directly through CMake and packaged through scikit-build-core.
- Verify Python ABI, native library loading, FFI error propagation, and runtime
  compatibility before activation.
- Record both Python and native/GPU requirements. A passing HTTP endpoint does
  not prove native or FFI health.

## Fleet compatibility

Reject incompatible artefacts before stopping the live release. Record the
chosen digest and compatibility envelope. Use separate artefacts and staged or
canary activation for heterogeneous OS, architecture, ABI, or GPU fleets.
