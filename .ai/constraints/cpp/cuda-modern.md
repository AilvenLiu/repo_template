# Modern CUDA Programming Standards

> **Status**: DRAFT  
> **This constraint is advisory and under validation. It will not fail pre-commit checks.**
>
> This document defines modern CUDA programming standards for high-performance AI infrastructure projects targeting Ampere (SM_80+), Ada Lovelace (SM_89), and Hopper (SM_90+) architectures. These guidelines cover Tensor Cores, asynchronous memory operations, CUTLASS/CuTe abstractions, and mixed-precision computation patterns.

## 1. Tensor Core Programming

### 1.1 WMMA (Warp Matrix Multiply-Accumulate)

**Target Architectures**: Volta (SM_70), Turing (SM_75), Ampere (SM_80, SM_86)

WMMA operates at warp level (32 threads) and supports FP16, BF16, TF32, and INT8 operations.

```cpp
#include <mma.h>
using namespace nvcuda::wmma;

__global__ void wmmaGemm(const half* A, const half* B, float* C, 
                         int M, int N, int K) {
    // Declare fragments (distributed across warp)
    fragment<matrix_a, 16, 16, 16, half, row_major> a_frag;
    fragment<matrix_b, 16, 16, 16, half, col_major> b_frag;
    fragment<accumulator, 16, 16, 16, float> c_frag;
    
    // Initialise accumulator
    fill_fragment(c_frag, 0.0f);
    
    // Load matrix fragments
    load_matrix_sync(a_frag, A + warp_row * 16 * K, K);
    load_matrix_sync(b_frag, B + warp_col * 16, K);
    
    // Perform matrix multiply-accumulate
    mma_sync(c_frag, a_frag, b_frag, c_frag);
    
    // Store result
    store_matrix_sync(C + warp_row * 16 * N + warp_col * 16, c_frag, N, mem_row_major);
}
```

**WMMA Best Practices**:
- Use 16x16x16 tiles for FP16/BF16 (optimal on most architectures)
- Accumulate in FP32 to avoid precision loss
- Ensure proper alignment (16-byte for FP16, 32-byte for optimal performance)
- Check `__CUDA_ARCH__ >= 700` for WMMA availability

### 1.2 WGMMA (Warpgroup Matrix Multiply-Accumulate)

**Target Architecture**: Hopper (SM_90+)

WGMMA operates at warpgroup level (128 threads = 4 warps) with asynchronous execution and native FP8 support.

```cpp
#if __CUDA_ARCH__ >= 900

__global__ void wgmmaGemm(const half* A, const half* B, float* C,
                          int M, int N, int K) {
    // Warpgroup synchronisation fence
    asm volatile("wgmma.fence.sync.aligned;");
    
    // WGMMA instruction (64x128x16 for FP16)
    // Note: Requires PTX inline assembly or CUTLASS abstractions
    uint32_t a_regs[2], b_regs[4], c_regs[4];
    
    asm volatile(
        "wgmma.mma_async.sync.aligned.m64n128k16.f32.f16.f16 "
        "{%0, %1, %2, %3}, {%4, %5}, {%6, %7, %8, %9};"
        : "=r"(c_regs[0]), "=r"(c_regs[1]), "=r"(c_regs[2]), "=r"(c_regs[3])
        : "r"(a_regs[0]), "r"(a_regs[1]), 
          "r"(b_regs[0]), "r"(b_regs[1]), "r"(b_regs[2]), "r"(b_regs[3])
    );
    
    // Commit and wait for completion
    asm volatile("wgmma.commit_group.sync.aligned;");
    asm volatile("wgmma.wait_group.sync.aligned 0;");
}

#endif // __CUDA_ARCH__ >= 900
```

**WGMMA Best Practices**:
- Use CUTLASS 3.x abstractions instead of raw PTX when possible
- Requires warpgroup-level synchronisation (128 threads)
- Provides 2-4x higher throughput than WMMA for large matrices
- Native FP8 support (E4M3 for activations, E5M2 for gradients)

### 1.3 WMMA vs WGMMA Selection

```cpp
#if __CUDA_ARCH__ >= 900
    // Hopper: Use WGMMA for maximum throughput
    #define USE_WGMMA 1
    constexpr int WARP_GROUP_SIZE = 128;
#elif __CUDA_ARCH__ >= 700
    // Volta/Ampere: Use WMMA
    #define USE_WMMA 1
    constexpr int WARP_SIZE = 32;
#else
    #error "Tensor Cores require SM_70 or higher"
#endif
```

## 2. TMA (Tensor Memory Accelerator)

**Target Architecture**: Hopper (SM_90+)

TMA is a hardware unit that offloads bulk memory transfers from SM to dedicated hardware, supporting multi-dimensional transfers with automatic swizzling.

```cpp
#include <cuda/barrier>

__global__ void tmaKernel(const float* gmem, float* output, int N) {
    __shared__ float smem[TILE_SIZE];
    __shared__ cuda::barrier<cuda::thread_scope_block> barrier;
    
    if (threadIdx.x == 0) {
        // Initialise barrier for all threads
        init(&barrier, blockDim.x);
        
        // Initiate TMA transfer (thread 0 only)
        cuda::memcpy_async(smem, gmem + blockIdx.x * TILE_SIZE, 
                          TILE_SIZE * sizeof(float), barrier);
    }
    
    // All threads wait for TMA completion
    barrier.arrive_and_wait();
    
    // Process data in shared memory
    int idx = threadIdx.x;
    if (idx < TILE_SIZE) {
        output[blockIdx.x * TILE_SIZE + idx] = smem[idx] * 2.0f;
    }
}
```

**TMA Best Practices**:
- Use for large, regular memory patterns (>1KB transfers)
- Single thread initiates transfer; all threads wait on barrier
- Leverage hardware swizzling for bank conflict avoidance
- Combine with async pipelines for overlapping compute and memory
- Check `__CUDA_ARCH__ >= 900` for TMA availability

## 3. Stream-Ordered Memory Allocation

Stream-ordered allocation eliminates synchronisation overhead of traditional `cudaMalloc`/`cudaFree`.

### 3.1 Basic Stream-Ordered Allocation

```cpp
void streamOrderedAllocation() {
    cudaStream_t stream;
    cudaStreamCreate(&stream);
    
    // Get default memory pool
    cudaMemPool_t mempool;
    int device;
    cudaGetDevice(&device);
    cudaDeviceGetDefaultMemPool(&mempool, device);
    
    // Configure pool to retain memory
    uint64_t threshold = UINT64_MAX;
    cudaMemPoolSetAttribute(mempool, cudaMemPoolAttrReleaseThreshold, &threshold);
    
    // Allocate memory (stream-ordered, no device sync)
    float* d_data;
    cudaMallocAsync(&d_data, size * sizeof(float), stream);
    
    // Use in kernels on same stream
    kernel<<<blocks, threads, 0, stream>>>(d_data, size);
    
    // Free when no longer needed (stream-ordered)
    cudaFreeAsync(d_data, stream);
    
    // Synchronise stream before exit
    cudaStreamSynchronize(stream);
    cudaStreamDestroy(stream);
}
```

### 3.2 Custom Memory Pools

```cpp
void customMemoryPool() {
    int device;
    cudaGetDevice(&device);
    
    // Create custom memory pool
    cudaMemPoolProps poolProps = {};
    poolProps.allocType = cudaMemAllocationTypePinned;
    poolProps.location.type = cudaMemLocationTypeDevice;
    poolProps.location.id = device;
    
    cudaMemPool_t customPool;
    cudaMemPoolCreate(&customPool, &poolProps);
    
    // Allocate from custom pool
    float* d_ptr;
    cudaMallocFromPoolAsync(&d_ptr, size * sizeof(float), customPool, stream);
    
    // Use memory
    kernel<<<blocks, threads, 0, stream>>>(d_ptr, size);
    
    // Free memory
    cudaFreeAsync(d_ptr, stream);
    
    // Trim unused memory from pool
    cudaMemPoolTrimTo(customPool, 0);
    
    // Destroy pool
    cudaMemPoolDestroy(customPool);
}
```

**Stream-Ordered Allocation Benefits**:
- No device synchronisation on alloc/free (10-100x faster)
- Automatic memory reuse within stream
- Better for dynamic workloads
- Reduces allocation latency

**When to Use**:
- Dynamic tensor shapes (variable batch sizes)
- Temporary buffers in multi-kernel pipelines
- Frequent allocation/deallocation patterns

## 4. CUDA Graphs

CUDA Graphs capture kernel launch sequences for replay with minimal CPU overhead.

### 4.1 Stream Capture

```cpp
void cudaGraphExample() {
    cudaGraph_t graph;
    cudaGraphExec_t graphExec;
    cudaStream_t stream;
    
    cudaStreamCreate(&stream);
    
    // Begin capture
    cudaStreamBeginCapture(stream, cudaStreamCaptureModeGlobal);
    
    // Launch kernels (captured, not executed)
    kernel1<<<blocks, threads, 0, stream>>>(d_a, d_b, size);
    kernel2<<<blocks, threads, 0, stream>>>(d_b, d_c, size);
    kernel3<<<blocks, threads, 0, stream>>>(d_c, d_d, size);
    
    // End capture
    cudaStreamEndCapture(stream, &graph);
    
    // Instantiate graph
    cudaGraphInstantiate(&graphExec, graph, nullptr, nullptr, 0);
    
    // Replay graph multiple times (low overhead)
    for (int i = 0; i < iterations; ++i) {
        cudaGraphLaunch(graphExec, stream);
    }
    
    cudaStreamSynchronize(stream);
    
    // Cleanup
    cudaGraphExecDestroy(graphExec);
    cudaGraphDestroy(graph);
    cudaStreamDestroy(stream);
}
```

### 4.2 Graph Updates

```cpp
void updateGraphParameters(cudaGraphExec_t graphExec, cudaGraphNode_t node) {
    // Update kernel parameters without recreating graph
    cudaKernelNodeParams newParams;
    newParams.func = (void*)kernel1;
    newParams.gridDim = dim3(new_blocks, 1, 1);
    newParams.blockDim = dim3(threads, 1, 1);
    newParams.sharedMemBytes = 0;
    newParams.kernelParams = new_args;
    
    cudaGraphExecKernelNodeSetParams(graphExec, node, &newParams);
    
    // Launch updated graph
    cudaGraphLaunch(graphExec, stream);
}
```

**CUDA Graph Best Practices**:
- Use for repeated kernel sequences (training loops, inference batches)
- Typical speedup: 1.5-3x for launch-bound workloads
- Update parameters instead of recreating graphs
- Combine with stream-ordered allocation for dynamic memory

**When to Use**:
- Fixed execution patterns
- CPU launch overhead is bottleneck
- Inference pipelines with repeated structure

## 5. CUTLASS and CuTe Idioms

### 5.1 CuTe Core Concepts

CuTe provides compile-time abstractions for tensor operations:
- **Layout**: Describes multi-dimensional data arrangement
- **Tensor**: Combines pointer, layout, and shape
- **MMA Atom**: Hardware instruction abstraction
- **Copy Atom**: Memory transfer abstraction

```cpp
#include <cute/tensor.hpp>
using namespace cute;

__global__ void cuteExample(float* data, int M, int N) {
    // Define layout (row-major)
    auto layout = make_layout(make_shape(Int<64>{}, Int<64>{}),
                             make_stride(Int<64>{}, Int<1>{}));
    
    // Create tensor
    auto tensor = make_tensor(data, layout);
    
    // Partition for thread block
    auto thread_layout = make_layout(make_shape(Int<8>{}, Int<8>{}));
    auto tiled_tensor = local_partition(tensor, thread_layout, threadIdx.x);
    
    // Access elements
    tiled_tensor(0, 0) = 1.0f;
}
```

### 5.2 CUTLASS 3.x GEMM Pattern

```cpp
#include <cutlass/cutlass.h>
#include <cutlass/gemm/collective/collective_builder.hpp>

using namespace cutlass;

// Define GEMM configuration
using CollectiveMainloop = CollectiveBuilder<
    arch::Sm90,                    // Architecture
    OpClassTensorOp,               // Tensor Core operation
    half_t,                        // Element A
    LayoutA,                       // Layout A
    8,                             // Alignment A
    half_t,                        // Element B
    LayoutB,                       // Layout B
    8,                             // Alignment B
    float,                         // Accumulator
    TileShape<_128,_128,_64>,     // Tile shape (M, N, K)
    ClusterShape<_1,_1,_1>,       // Cluster shape
    StageCountAutoCarveout<3>,    // Pipeline stages
    KernelTmaWarpSpecialized      // Kernel schedule (Hopper)
>::CollectiveOp;
```

**CUTLASS/CuTe Best Practices**:
- Use CUTLASS 3.x for Hopper (SM_90+) with TMA support
- Use CUTLASS 2.x for Ampere/Volta compatibility
- Leverage compile-time layout optimisation
- Prefer CuTe abstractions over raw pointer arithmetic
- Use MMA atoms for portable Tensor Core code

## 6. Mixed-Precision Computation

### 6.1 Precision Format Characteristics

| Format | Bits | Range | Precision | Primary Use Case |
|--------|------|-------|-----------|------------------|
| FP32 | 32 | +/-3.4e38 | 7 digits | Master weights, reductions |
| FP16 | 16 | +/-65504 | 3 digits | Compute (Volta+), activations |
| BF16 | 16 | +/-3.4e38 | 2 digits | Training (Ampere+), gradients |
| TF32 | 19 | +/-3.4e38 | 3 digits | Tensor Core compute (Ampere+) |
| FP8 E4M3 | 8 | +/-448 | ~2 digits | Forward pass (Hopper) |
| FP8 E5M2 | 8 | +/-57344 | ~1 digit | Gradients (Hopper) |

### 6.2 Mixed-Precision Training Pattern

```cpp
__global__ void mixedPrecisionTraining(
    const half* activations,      // FP16 activations
    const half* weights_fp16,     // FP16 weight copy
    float* weights_fp32,          // FP32 master weights
    float* gradients,             // FP32 gradient accumulation
    float loss_scale,
    float learning_rate,
    int size) {
    
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= size) return;
    
    // Forward: FP16 compute
    half output = __hmul(activations[idx], weights_fp16[idx]);
    
    // Backward: accumulate in FP32
    float grad = __half2float(output) * loss_scale;
    atomicAdd(&gradients[idx], grad);
    
    // Update: FP32 master weights
    weights_fp32[idx] -= learning_rate * (gradients[idx] / loss_scale);
    
    // Copy back to FP16 for next iteration
    weights_fp16[idx] = __float2half(weights_fp32[idx]);
}
```

### 6.3 FP8 Computation (Hopper)

```cpp
#if __CUDA_ARCH__ >= 900

__global__ void fp8Gemm(
    const __nv_fp8_e4m3* A,      // FP8 input (E4M3 for activations)
    const __nv_fp8_e4m3* B,      // FP8 weights
    half* C,                      // FP16 output
    float scale_a,                // Input scale factor
    float scale_b,                // Weight scale factor
    int M, int N, int K) {
    
    // Hardware handles scaling during WGMMA
    // Output automatically scaled to FP16
    // Use CUTLASS for production FP8 GEMM
}

#endif // __CUDA_ARCH__ >= 900
```

### 6.4 Precision Selection Guidelines

**Training**:
- **Master weights**: Always FP32
- **Activations**: BF16 (Ampere+) or FP16 (Volta)
- **Gradients**: BF16 with loss scaling
- **Accumulation**: FP32

**Inference**:
- **Weights**: FP16 (Ampere) or FP8 (Hopper)
- **Activations**: FP16 or FP8
- **Compute**: TF32 (automatic on Ampere+)

**Why BF16 over FP16 for Training**:
- Wider dynamic range (same as FP32)
- Fewer overflow/underflow issues
- No loss scaling required (but recommended)
- Native Tensor Core support on Ampere+

## 7. Modern SM Dispatch Patterns

### 7.1 Compute Capability Mapping

| Architecture | SM Version | Key Features |
|--------------|------------|--------------|
| Volta | SM_70 | First Tensor Cores (WMMA) |
| Turing | SM_75 | INT8 Tensor Cores |
| Ampere | SM_80 | TF32, BF16, FP64 Tensor Cores |
| Ampere | SM_86 | Consumer Ampere (RTX 30xx) |
| Ada Lovelace | SM_89 | FP8 support, improved Tensor Cores |
| Hopper | SM_90 | WGMMA, TMA, FP8 Tensor Cores |
| Blackwell | SM_100 | Next generation (future) |

### 7.2 Multi-Architecture Compilation

```cmake
# CMakeLists.txt
set(CMAKE_CUDA_ARCHITECTURES 80 86 89 90)

# Or specify explicitly
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_80,code=sm_80")
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_86,code=sm_86")
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_89,code=sm_89")
set(CMAKE_CUDA_FLAGS "${CMAKE_CUDA_FLAGS} -gencode arch=compute_90,code=sm_90")
```

### 7.3 Runtime Architecture Detection

```cpp
int getComputeCapability() {
    int device;
    cudaGetDevice(&device);
    
    cudaDeviceProp prop;
    cudaGetDeviceProperties(&prop, device);
    
    return prop.major * 10 + prop.minor;
}

void dispatchKernel(float* data, int size) {
    int sm_version = getComputeCapability();
    
    if (sm_version >= 90) {
        // Hopper: Use WGMMA, TMA, FP8
        hopperKernel<<<blocks, threads>>>(data, size);
    } else if (sm_version >= 80) {
        // Ampere: Use TF32, BF16, async copy
        ampereKernel<<<blocks, threads>>>(data, size);
    } else if (sm_version >= 70) {
        // Volta: Use WMMA, FP16
        voltaKernel<<<blocks, threads>>>(data, size);
    } else {
        throw std::runtime_error("Minimum SM_70 required");
    }
}
```

### 7.4 Compile-Time Feature Detection

```cpp
template<int SM_VERSION>
__global__ void featureSpecificKernel(float* data, int size) {
#if __CUDA_ARCH__ >= 900
    // Hopper-specific code
    __nv_fp8_e4m3 fp8_data;
    // Use WGMMA, TMA
#elif __CUDA_ARCH__ >= 800
    // Ampere-specific code
    __nv_bfloat16 bf16_data;
    // Use async copy, TF32
#elif __CUDA_ARCH__ >= 700
    // Volta-specific code
    half fp16_data;
    // Use WMMA
#else
    #error "Minimum SM_70 required for Tensor Cores"
#endif
}
```

## 8. Performance Optimisation Guidelines

### 8.1 Tensor Core Utilisation

- **Tile sizes**: Use multiples of Tensor Core instruction shapes (16x16x16 for WMMA, 64x128x16 for WGMMA)
- **Alignment**: Ensure 16-byte alignment for FP16, 32-byte for optimal performance
- **Occupancy**: Balance shared memory usage with occupancy (use `--ptxas-options=-v`)
- **Pipeline depth**: Use 3-5 stages for Ampere, 5-7 for Hopper

### 8.2 Memory Bandwidth Optimisation

- **Coalescing**: Ensure contiguous memory access patterns
- **TMA**: Use for large transfers on Hopper (>1KB)
- **Async copy**: Use `cp.async` for Ampere, TMA for Hopper
- **Shared memory**: Leverage hardware swizzling to avoid bank conflicts

### 8.3 Launch Overhead Reduction

- **CUDA Graphs**: Use for repeated kernel sequences (1.5-3x speedup)
- **Stream-ordered allocation**: Eliminate synchronisation overhead
- **Persistent kernels**: Consider for very small kernels with high launch frequency

## 9. Testing and Validation

### 9.1 Architecture-Specific Testing

```cpp
TEST(ModernCUDA, TensorCoreCorrectness) {
    int sm_version = getComputeCapability();
    
    if (sm_version >= 90) {
        // Test Hopper features
        testWGMMA();
        testTMA();
        testFP8();
    } else if (sm_version >= 80) {
        // Test Ampere features
        testWMMA_BF16();
        testTF32();
        testAsyncCopy();
    } else if (sm_version >= 70) {
        // Test Volta features
        testWMMA_FP16();
    } else {
        GTEST_SKIP() << "Tensor Cores not available";
    }
}
```

### 9.2 Numerical Validation

- **Reference implementation**: Compare against PyTorch eager or cuBLAS
- **Tolerance bands**: Use dtype-specific tolerances (see kernel-correctness.md)
- **Shape coverage**: Test multiple tile sizes and edge cases
- **SM coverage**: Test on SM_80, SM_86, SM_89, SM_90 if available

## 10. Enforcement

**Status**: DRAFT (Advisory Only)

This constraint is under validation and will not fail pre-commit checks. Adoption is recommended for new CUDA kernel development targeting modern architectures (Ampere, Ada Lovelace, Hopper).

### 10.1 Recommended Adoption Path

1. **Phase 1**: Use for new kernel development
2. **Phase 2**: Refactor performance-critical kernels
3. **Phase 3**: Promote to required after validation on real projects

### 10.2 Validation Criteria

Before promotion to required status:
- Validated on at least one real AI infrastructure project (TVM, FlashInfer, MLC-LLM, xgrammar)
- Demonstrated performance improvements over legacy patterns
- No regressions in numerical correctness
- Community feedback incorporated

## 11. References

- NVIDIA CUDA Programming Guide: https://docs.nvidia.com/cuda/cuda-c-programming-guide/
- CUTLASS Documentation: https://github.com/NVIDIA/cutlass
- CuTe Tutorial: https://github.com/NVIDIA/cutlass/blob/main/media/docs/cute/00_quickstart.md
- Hopper Architecture Whitepaper: https://resources.nvidia.com/en-us-tensor-core
- Mixed Precision Training: https://docs.nvidia.com/deeplearning/performance/mixed-precision-training/
