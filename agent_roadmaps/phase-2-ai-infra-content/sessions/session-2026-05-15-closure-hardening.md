# Session Handoff: 2026-05-15 - Closure Hardening and Revalidation

## Summary

This session addressed the remaining static-review blockers that prevented an
honest "Phase 2 is functionally complete" assessment.

## Template-Side Fixes Landed

1. **Hybrid profile/schema alignment**
   - Added `Distribution.PYPI_WHEEL` support.
   - Corrected selector/documentation mismatches around `pypi-wheel` and
     `external_dependencies=system_cuda`.
   - Extended capability-selector parsing to support `OR` / `AND`.

2. **Hybrid constraint loading**
   - `/init` now loads:
     - `hybrid/ffi-boundary`
     - `hybrid/python-cpp-build`
     - `hybrid/system-deps`
   - `gpu-ci` is now required for `distribution=pypi-wheel OR hardware_targets=cuda`.

3. **Bazel/build wrapper hardening**
   - `bin/agent-bazel` now supports `build`, `test`, `run`, `clean`, and `query`.
   - `bin/agent-build` now dispatches Bazel projects through real Bazel flows
     instead of a Phase-2-era stub.
   - Build/bazel skill docs were updated to match the code.

4. **Hybrid pre-commit support**
   - Pre-commit now detects hybrid projects explicitly.
   - Python environment/manifest checks accept scikit-build-core projects.
   - Hybrid pre-commit runs both Python and C++ validation paths.
   - Shared runtime constraint validation no longer incorrectly requires Poetry
     for scikit-build-core projects.

5. **Regression coverage expanded**
   - Added / updated tests so hybrid generation and hybrid `/init` are covered.
   - Updated stale tests that still expected old stubs or pre-Phase-2 loader behaviour.

## Local Test Evidence

Targeted repository tests passed after the fixes:

- `pytest -q tests/test_precommit_utils.py .ai/scripts/tests/test_project_profile.py .ai/scripts/tests/test_session_init.py .ai/scripts/tests/test_capability_audit.py .ai/scripts/tests/test_agent_build.py tests/test_e2e_project_generation.py`
- Result: **71 passed**

## Real Consuming Project Revalidation

Revalidated against the existing local TVM sandbox at:

- `/private/tmp/tvm-phase2-validation/tvm`

### Results

1. `bin/agent-init --platform codex`
   - **PASS**
   - `gpu-ci` is now required and present.
   - Hybrid constraints now load correctly:
     - `hybrid/ffi-boundary`
     - `hybrid/python-cpp-build`
     - `hybrid/system-deps`

2. `bin/agent-build doctor`
   - **PASS**
   - Confirms scikit-build-core path is selected.

3. `bin/agent-dependency add requests`
   - **PASS**
   - Confirms scikit-build-core dependency workflow is active.

4. `bin/agent-precommit`
   - **TEMPLATE-SIDE BUG FIX VERIFIED**
   - Previously failed immediately because hybrid/scikit-build-core projects were
     misclassified as Poetry-only Python projects.
   - After the fixes, that misclassification is gone.
   - Remaining failures are now consuming-project/toolchain issues:
     - missing `tvm` import for pytest plugin setup
     - missing `clang-format`, `clang-tidy`, `cppcheck`
     - no configured package-manager file for the local sandbox copy
     - no configured build directory

5. `bin/agent-build full`
   - **FAILS DUE TO LOCAL ENVIRONMENT**
   - Current machine / sandbox is missing `scikit_build_core.build`, so editable
     install cannot proceed.
   - This is now an environment provisioning problem, not the original template
     dispatch problem.

## Assessment

The remaining blockers identified in the static review are resolved in the
template codebase itself.

The consuming-project failures that remain in the local TVM sandbox are now
external to the template logic: missing Python build backend installation,
missing C++ toolchain utilities, and missing project-specific runtime/build
provisioning.

## Recommendation

From a **template/codebase** perspective, Phase 2 now appears functionally
complete and Phase 3 remains optional.

If the user wants a **strict roadmap-paperwork closure**, the last remaining
work is to repeat `task-2-10` in a fully provisioned consuming-project
environment and then update `roadmap.yml` / PR state accordingly.
