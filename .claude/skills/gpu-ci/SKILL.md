---
name: gpu-ci
description: "GPU CI patterns for CUDA compilation caching, manylinux wheels, and multi-arch builds. Use when distribution=pypi-wheel or hardware_targets.cuda_arch is non-empty."
version: 1.0.0
---

# /gpu-ci

GPU CI guidance. The canonical, vendor-neutral procedure body lives at
[`.ai/skills/gpu-ci/SKILL.md`](../../../.ai/skills/gpu-ci/SKILL.md).

## Purpose

This skill provides guidance for:
- sccache for CUDA compilation caching
- auditwheel for manylinux wheel validation
- Multi-arch wheel build matrices (cu118, cu121, cu124)
- H100/A100/L40 GPU gating patterns

## Phase 2 Status

This is a guidance-only skill in Phase 2. No executable wrapper (`bin/agent-gpu-ci`)
is provided. The skill documents CI patterns and best practices for GPU-accelerated
projects that distribute Python wheels.

When this slash command is invoked, also read
[`.ai/skills/gpu-ci/SKILL.md`](../../../.ai/skills/gpu-ci/SKILL.md) for the full
guidance.
