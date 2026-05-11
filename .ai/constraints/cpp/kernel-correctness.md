---
id: cpp/kernel-correctness
status: draft
applies_to:
  - language: cuda
activation_rule: "Activates when .cu or .cuh files are present"
---

# Kernel Correctness Testing Constraint

**Status**: DRAFT - Advisory guidance for AI agents. Not yet validated in production.

This constraint defines testing standards for CUDA kernel implementations, replacing traditional line-coverage metrics with reference-correctness validation, numerical tolerance specifications, performance regression gates, and hardware coverage matrices.

## Reference-Correctness Testing

### Baseline Selection

Every custom CUDA kernel must be validated against a reference implementation:

1. **PyTorch eager mode** - For operations with native PyTorch equivalents
2. **cuBLAS/cuDNN** - For BLAS/DNN operations
3. **CPU reference** - For novel operations without GPU library equivalents
4. **Analytical solution** - For operations with closed-form mathematical expressions

**Pattern**: Test fixture compares kernel output against reference on identical inputs.

```python
import torch
import pytest
from my_kernels import fused_attention  # Custom CUDA kernel

def test_fused_attention_correctness():
    B, H, N, D = 2, 8, 1024, 64
    Q = torch.randn(B, H, N, D, device='cuda', dtype=torch.float16)
    K = torch.randn(B, H, N, D, device='cuda', dtype=torch.float16)
    V = torch.randn(B, H, N, D, device='cuda', dtype=torch.float16)
    
    # Reference: PyTorch eager mode
    ref_output = torch.nn.functional.scaled_dot_product_attention(Q, K, V)
    
    # Custom kernel
    kernel_output = fused_attention(Q, K, V)
    
    # Validate against tolerance band for FP16
    torch.testing.assert_close(
        kernel_output, ref_output,
        rtol=1e-3, atol=1e-3
    )
```

### When Reference is Unavailable

For novel algorithms without established references:

1. **Invariant testing** - Verify mathematical properties (e.g., softmax sums to 1)
2. **Gradient checking** - Compare numerical gradients against autograd
3. **Cross-implementation validation** - Compare against alternative implementations (e.g., Triton vs CUDA)

## Numerical Tolerance Bands

Tolerance thresholds vary by data type due to precision characteristics:

| Data Type | rtol (Relative) | atol (Absolute) | Rationale |
|-----------|-----------------|-----------------|-----------|
| FP32      | 1e-5            | 1e-5            | IEEE 754 single precision: ~7 decimal digits |
| FP16      | 1e-3            | 1e-3            | Half precision: ~3 decimal digits, accumulation error |
| BF16      | 1e-2            | 1e-2            | Brain float: reduced mantissa, larger exponent range |
| FP8 E4M3  | 5e-2            | 5e-2            | 4-bit exponent, 3-bit mantissa: aggressive quantization |
| FP8 E5M2  | 5e-2            | 5e-2            | 5-bit exponent, 2-bit mantissa: wider range, less precision |

**Citations**:
- FP32/FP16 tolerances: PyTorch testing conventions (`torch.testing.assert_close` defaults)
- BF16 tolerance: Empirical observation from transformer training (see "Mixed Precision Training", Micikevicius et al., ICLR 2018)
- FP8 tolerances: NVIDIA H100 Transformer Engine documentation (FP8 formats specification)

### Tolerance Adjustment for Deep Operations

For operations with multiple stages (e.g., fused attention = matmul + softmax + matmul):

- **Multiply tolerance by sqrt(N)** where N is the number of sequential operations
- Example: 3-stage fused kernel with FP16 -> rtol = 1e-3 * sqrt(3) ~= 1.7e-3

### Handling Non-Determinism

CUDA atomics and reduction operations may produce non-deterministic results:

```python
# Use deterministic algorithms when available
torch.use_deterministic_algorithms(True)

# For inherently non-deterministic kernels, test statistical properties
def test_stochastic_rounding():
    x = torch.randn(1000000, device='cuda', dtype=torch.float32)
    y = stochastic_round_to_fp8(x)
    
    # Verify unbiased rounding: mean should be preserved
    assert abs(y.float().mean() - x.mean()) < 1e-4
    
    # Verify variance is within expected range
    expected_variance = x.var() + quantization_noise_variance(fp8_format)
    assert abs(y.float().var() - expected_variance) < 1e-3
```

## Performance Regression Gates

### Baseline Establishment

1. **Initial benchmark** - Run kernel on representative workload, record median latency over 100 iterations (warmup: 10 iterations)
2. **Store baseline** - Commit baseline to `benchmarks/baselines/{kernel_name}_{sm_version}.json`
3. **CI enforcement** - Compare PR benchmarks against baseline

### Regression Thresholds

| Threshold | Action | Rationale |
|-----------|--------|-----------|
| +5% slower | Warning (non-blocking) | Noise tolerance, may be acceptable tradeoff |
| +10% slower | Failure (blocking) | Significant regression, requires justification |
| +20% slower | Hard failure | Unacceptable without explicit override |

**Tool**: Use `pytest-benchmark` with `--benchmark-compare` flag:

```bash
# Establish baseline
pytest tests/benchmarks/test_kernels.py --benchmark-save=baseline

# Compare in CI
pytest tests/benchmarks/test_kernels.py \
    --benchmark-compare=baseline \
    --benchmark-compare-fail=mean:10%
```

### Benchmark Artifact Storage

Store benchmark results as JSON artifacts:

```json
{
  "kernel": "fused_attention",
  "sm_version": "SM_90",
  "shape": {"B": 2, "H": 8, "N": 1024, "D": 64},
  "dtype": "float16",
  "median_us": 123.45,
  "std_us": 2.34,
  "timestamp": "2026-05-11T10:30:00Z",
  "commit": "a1b2c3d4"
}
```

### When to Update Baseline

Update baseline when:
1. **Intentional optimization** - PR explicitly improves performance
2. **Hardware change** - New GPU architecture (e.g., H100 -> H200)
3. **CUDA version upgrade** - Compiler optimizations may change performance

**Process**: Require manual approval + comment explaining why baseline is updated.

## SM Version Coverage Matrix

Test kernels across GPU architectures to catch architecture-specific bugs:

| SM Version | Architecture | Key Features | Test Priority |
|------------|--------------|--------------|---------------|
| SM_80      | A100         | Tensor Cores (3rd gen), FP64 Tensor Cores | High (production workhorse) |
| SM_86      | RTX 3090     | Consumer Ampere, FP32 Tensor Cores | Medium (developer hardware) |
| SM_89      | RTX 4090     | Ada Lovelace, FP8 Tensor Cores | Medium (emerging consumer) |
| SM_90      | H100         | Hopper, FP8 Tensor Cores, TMA, DPX | High (latest datacenter) |
| SM_100     | B100/B200    | Blackwell (future) | Low (forward compatibility) |

### CI Matrix Strategy

**Minimum viable coverage**: SM_80 (A100) + SM_90 (H100)

**Full coverage** (for critical kernels):
```yaml
# .github/workflows/test-kernels.yml
strategy:
  matrix:
    sm_version: [80, 86, 89, 90]
    include:
      - sm_version: 80
        runner: [self-hosted, gpu, a100]
      - sm_version: 86
        runner: [self-hosted, gpu, rtx3090]
      - sm_version: 89
        runner: [self-hosted, gpu, rtx4090]
      - sm_version: 90
        runner: [self-hosted, gpu, h100]
```

### Architecture-Specific Bugs to Watch

1. **Tensor Core alignment** - SM_80+ requires 16-byte alignment for Tensor Core inputs
2. **Shared memory capacity** - SM_80: 164KB, SM_90: 228KB (kernels may OOM on older archs)
3. **Warp size assumptions** - Always 32, but warp scheduling differs across architectures
4. **Atomic performance** - SM_90 has faster global atomics than SM_80

### Conditional Compilation

Use `__CUDA_ARCH__` for architecture-specific code paths:

```cuda
#if __CUDA_ARCH__ >= 900
    // H100-specific: use TMA (Tensor Memory Accelerator)
    tma_load(smem_ptr, gmem_ptr, shape);
#else
    // Fallback: manual async copy
    cp_async(smem_ptr, gmem_ptr, size);
#endif
```

**Test both paths**: Compile with `-gencode arch=compute_80,code=sm_80` and `-gencode arch=compute_90,code=sm_90`.

## Shape-Bucket Coverage

### Motivation

Kernels often have shape-dependent code paths (e.g., different tile sizes for small vs large matrices). Test representative shapes from each bucket.

### Shape Buckets for Attention Kernels

| Bucket | Sequence Length (N) | Batch x Heads (BxH) | Use Case |
|--------|---------------------|---------------------|----------|
| Tiny   | 128-512             | 1-8                 | Inference, short prompts |
| Small  | 512-2048            | 8-32                | Training, standard context |
| Medium | 2048-8192           | 32-128              | Long-context training |
| Large  | 8192-32768          | 128-512             | Extreme long-context |
| Huge   | 32768+              | 512+                | Research, sparse attention |

### Shape Bucket Test Pattern

```python
@pytest.mark.parametrize("shape_bucket", [
    {"B": 1, "H": 8, "N": 256, "D": 64},    # Tiny
    {"B": 2, "H": 16, "N": 1024, "D": 64},  # Small
    {"B": 4, "H": 32, "N": 4096, "D": 128}, # Medium
    {"B": 8, "H": 64, "N": 16384, "D": 128},# Large
])
def test_fused_attention_shapes(shape_bucket):
    Q = torch.randn(shape_bucket["B"], shape_bucket["H"], 
                    shape_bucket["N"], shape_bucket["D"], 
                    device='cuda', dtype=torch.float16)
    # ... test kernel correctness and performance
```

### Edge Cases to Test

1. **Power-of-2 boundaries** - N = 1024, 2048, 4096 (may trigger different tile sizes)
2. **Non-power-of-2** - N = 1000, 3000 (test padding/masking logic)
3. **Odd dimensions** - N = 1023, D = 63 (test alignment handling)
4. **Minimum viable** - N = 1, B = 1 (test degenerate cases)
5. **Maximum supported** - Test at kernel's advertised limit

## Integration with CI/CD

### Pre-Merge Requirements

All PRs touching `.cu` or `.cuh` files must pass:

1. **Correctness tests** - All reference-correctness tests pass on SM_80 and SM_90
2. **Performance gates** - No regressions >10% on baseline benchmarks
3. **Shape coverage** - At least 3 shape buckets tested (tiny, small, medium)

### Nightly Extended Tests

Run full coverage nightly:

1. **All SM versions** - SM_80, SM_86, SM_89, SM_90
2. **All shape buckets** - Including large and huge
3. **All dtypes** - FP32, FP16, BF16, FP8 (if supported)
4. **Stress tests** - 1000+ iterations to catch rare race conditions

### Benchmark Tracking

Store benchmark history in time-series database (e.g., InfluxDB) for trend analysis:

```python
# Post-benchmark hook
def store_benchmark_result(result):
    influxdb_client.write_point(
        measurement="kernel_latency",
        tags={"kernel": result.name, "sm": result.sm_version},
        fields={"median_us": result.median, "p99_us": result.p99},
        timestamp=datetime.utcnow()
    )
```

Visualize trends in Grafana to detect gradual performance degradation.

## Debugging Failed Correctness Tests

### Step 1: Isolate the Failure

```python
# Add detailed logging
def test_kernel_debug():
    output = my_kernel(input)
    reference = reference_impl(input)
    
    diff = (output - reference).abs()
    max_diff = diff.max().item()
    mean_diff = diff.mean().item()
    
    print(f"Max absolute difference: {max_diff}")
    print(f"Mean absolute difference: {mean_diff}")
    print(f"Locations of max diff: {torch.where(diff == max_diff)}")
    
    # Save tensors for inspection
    torch.save({"output": output, "reference": reference, "input": input}, 
               "debug_tensors.pt")
```

### Step 2: Check for Common Issues

1. **Uninitialized memory** - Run with `cuda-memcheck`
2. **Race conditions** - Run with `cuda-gdb` and `--device-debug`
3. **Numerical instability** - Check for NaN/Inf with `torch.isnan(output).any()`
4. **Incorrect indexing** - Print intermediate values from kernel

### Step 3: Reduce to Minimal Reproducer

Binary search over input dimensions to find smallest failing case:

```python
# Start with failing shape (B=8, N=1024)
# Try (B=4, N=1024) -> passes
# Try (B=6, N=1024) -> fails
# Try (B=5, N=1024) -> passes
# Conclusion: Bug triggers at B=6+
```

## Exceptions and Overrides

### When to Skip Reference Testing

1. **No reference exists** - Novel algorithm, use invariant testing instead
2. **Reference is too slow** - For large shapes, test subset of outputs
3. **Non-deterministic by design** - Stochastic rounding, dropout

Document exceptions in test docstring:

```python
def test_novel_kernel():
    """
    Tests novel_kernel using invariant testing (no reference available).
    
    Validates:
    - Output sum equals input sum (conservation property)
    - Output is non-negative (ReLU-like activation)
    """
```

### When to Relax Performance Gates

Acceptable reasons to exceed +10% threshold:

1. **Correctness fix** - Bug fix that trades performance for correctness
2. **Numerical stability** - More stable algorithm with slight slowdown
3. **Generalization** - Support for new dtypes/shapes with minor overhead

**Process**: Add `# performance-regression-override: <reason>` comment in PR description.

## Summary Checklist

For every CUDA kernel implementation, ensure:

- [ ] Reference-correctness test exists (PyTorch eager, cuBLAS, or CPU reference)
- [ ] Tolerance bands are appropriate for dtype (FP32: 1e-5, FP16: 1e-3, BF16: 1e-2, FP8: 5e-2)
- [ ] Performance baseline is established and tracked
- [ ] Regression gates are configured (+5% warning, +10% failure)
- [ ] Tested on at least SM_80 (A100) and SM_90 (H100)
- [ ] At least 3 shape buckets are covered (tiny, small, medium)
- [ ] Edge cases are tested (power-of-2, non-power-of-2, odd dimensions)
- [ ] Benchmark artifacts are stored for historical tracking
- [ ] CI pipeline enforces correctness and performance gates

---

**Activation**: This constraint activates when `.cu` or `.cuh` files are present in the project.

**Rationale**: Traditional code coverage metrics (line coverage, branch coverage) are insufficient for CUDA kernels because they don't validate numerical correctness or performance. This constraint establishes a testing standard that catches both correctness bugs (wrong results) and performance regressions (slower than baseline), while ensuring coverage across GPU architectures and input shapes.

**Related Constraints**:
- `cpp/cuda-modern.md` - Modern CUDA API patterns (Cooperative Groups, async copy)
- `hybrid/ffi-boundary.md` - Python/C++ boundary testing (if kernel is exposed via bindings)
- `hybrid/system-deps.md` - CUDA Toolkit version requirements for testing infrastructure
