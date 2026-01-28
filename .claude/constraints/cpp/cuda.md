# CUDA-Specific Development Guidelines

> **This document defines mandatory CUDA development standards for C++/CUDA projects.**
> All CUDA code must follow these requirements for correctness, safety, and performance.

## 1. CUDA Toolkit Requirements

### 1.1 Version Requirements
- **Minimum CUDA Toolkit**: 11.0
- **Preferred CUDA Toolkit**: 12.0 or later
- **Compute Capability**: Document minimum required (e.g., sm_70 for Volta+)
- **CUDA Standard**: Match or be compatible with C++ standard used

### 1.2 Compiler Compatibility
- **nvcc**: CUDA compiler with host compiler compatibility
- **Host Compiler**: Must be compatible with CUDA toolkit version
  - GCC 9.0+ for CUDA 11.0
  - GCC 10.0+ for CUDA 11.5+
  - Clang 10.0+ for CUDA 11.0

## 2. CUDA Memory Management

### 2.1 Device Memory Allocation
- **Device Memory**: Always pair `cudaMalloc` with `cudaFree`
- **RAII Wrappers**: Create or use RAII wrappers for CUDA resources
- **Unified Memory**: Document when using `cudaMallocManaged` and prefetch strategies
- **Memory Pools**: Consider using memory pools for frequent allocations

### 2.2 RAII Wrapper Example
```cpp
template<typename T>
class CudaDeviceMemory {
    T* ptr_ = nullptr;
    size_t size_ = 0;
public:
    explicit CudaDeviceMemory(size_t count) : size_(count) {
        cudaError_t err = cudaMalloc(&ptr_, count * sizeof(T));
        if (err != cudaSuccess) {
            throw std::runtime_error(cudaGetErrorString(err));
        }
    }
    ~CudaDeviceMemory() { if (ptr_) cudaFree(ptr_); }

    // Delete copy, implement move
    CudaDeviceMemory(const CudaDeviceMemory&) = delete;
    CudaDeviceMemory& operator=(const CudaDeviceMemory&) = delete;

    CudaDeviceMemory(CudaDeviceMemory&& other) noexcept
        : ptr_(other.ptr_), size_(other.size_) {
        other.ptr_ = nullptr;
        other.size_ = 0;
    }

    CudaDeviceMemory& operator=(CudaDeviceMemory&& other) noexcept {
        if (this != &other) {
            if (ptr_) cudaFree(ptr_);
            ptr_ = other.ptr_;
            size_ = other.size_;
            other.ptr_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }

    T* get() { return ptr_; }
    const T* get() const { return ptr_; }
    size_t size() const { return size_; }
};
```

### 2.3 Memory Transfer Best Practices
```cpp
// Host to device
cudaMemcpy(d_ptr, h_ptr, size, cudaMemcpyHostToDevice);

// Device to host
cudaMemcpy(h_ptr, d_ptr, size, cudaMemcpyDeviceToHost);

// Device to device
cudaMemcpy(d_dst, d_src, size, cudaMemcpyDeviceToDevice);

// Asynchronous transfer (with streams)
cudaMemcpyAsync(d_ptr, h_ptr, size, cudaMemcpyHostToDevice, stream);
```

### 2.4 Unified Memory
```cpp
// Allocate unified memory
float* unified_ptr;
cudaMallocManaged(&unified_ptr, size);

// Prefetch to device
cudaMemPrefetchAsync(unified_ptr, size, device_id);

// Prefetch to host
cudaMemPrefetchAsync(unified_ptr, size, cudaCpuDeviceId);

// Free unified memory
cudaFree(unified_ptr);
```

## 3. CUDA Error Handling

### 3.1 Mandatory Error Checking
**MANDATORY**: Check return value of EVERY CUDA API call

### 3.2 Error Checking Macro
```cpp
#define CUDA_CHECK(call) \
    do { \
        cudaError_t err = call; \
        if (err != cudaSuccess) { \
            throw std::runtime_error( \
                std::string("CUDA error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + " - " + \
                cudaGetErrorString(err)); \
        } \
    } while(0)

// Usage
CUDA_CHECK(cudaMalloc(&d_ptr, size));
CUDA_CHECK(cudaMemcpy(d_ptr, h_ptr, size, cudaMemcpyHostToDevice));
```

### 3.3 Kernel Launch Error Checking
```cpp
// Launch kernel
myKernel<<<blocks, threads>>>(args);

// Check launch errors
CUDA_CHECK(cudaGetLastError());

// Check execution errors
CUDA_CHECK(cudaDeviceSynchronize());
```

### 3.4 Complete Error Handling Example
```cpp
void processData(const float* h_input, float* h_output, size_t size) {
    float *d_input, *d_output;

    // Allocate device memory
    CUDA_CHECK(cudaMalloc(&d_input, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_output, size * sizeof(float)));

    // Copy input to device
    CUDA_CHECK(cudaMemcpy(d_input, h_input, size * sizeof(float),
                          cudaMemcpyHostToDevice));

    // Launch kernel
    int threads = 256;
    int blocks = (size + threads - 1) / threads;
    processKernel<<<blocks, threads>>>(d_input, d_output, size);

    // Check for launch errors
    CUDA_CHECK(cudaGetLastError());

    // Wait for kernel to complete
    CUDA_CHECK(cudaDeviceSynchronize());

    // Copy result back to host
    CUDA_CHECK(cudaMemcpy(h_output, d_output, size * sizeof(float),
                          cudaMemcpyDeviceToHost));

    // Free device memory
    CUDA_CHECK(cudaFree(d_input));
    CUDA_CHECK(cudaFree(d_output));
}
```

## 4. CUDA Kernel Development

### 4.1 Kernel Function Signature
```cpp
__global__ void kernelName(
    const float* input,
    float* output,
    int size) {
    // Kernel implementation
}
```

### 4.2 Thread Indexing
```cpp
__global__ void vectorAdd(const float* a, const float* b, float* c, int n) {
    // 1D indexing
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        c[idx] = a[idx] + b[idx];
    }
}

__global__ void matrixAdd(const float* a, const float* b, float* c,
                          int rows, int cols) {
    // 2D indexing
    int row = blockIdx.y * blockDim.y + threadIdx.y;
    int col = blockIdx.x * blockDim.x + threadIdx.x;

    if (row < rows && col < cols) {
        int idx = row * cols + col;
        c[idx] = a[idx] + b[idx];
    }
}
```

### 4.3 Shared Memory Usage
```cpp
__global__ void matrixMulShared(const float* A, const float* B, float* C,
                                int M, int K, int N) {
    __shared__ float As[TILE_SIZE][TILE_SIZE];
    __shared__ float Bs[TILE_SIZE][TILE_SIZE];

    int row = blockIdx.y * TILE_SIZE + threadIdx.y;
    int col = blockIdx.x * TILE_SIZE + threadIdx.x;

    float sum = 0.0f;

    for (int tile = 0; tile < (K + TILE_SIZE - 1) / TILE_SIZE; ++tile) {
        // Load tile into shared memory
        if (row < M && tile * TILE_SIZE + threadIdx.x < K) {
            As[threadIdx.y][threadIdx.x] = A[row * K + tile * TILE_SIZE + threadIdx.x];
        } else {
            As[threadIdx.y][threadIdx.x] = 0.0f;
        }

        if (col < N && tile * TILE_SIZE + threadIdx.y < K) {
            Bs[threadIdx.y][threadIdx.x] = B[(tile * TILE_SIZE + threadIdx.y) * N + col];
        } else {
            Bs[threadIdx.y][threadIdx.x] = 0.0f;
        }

        __syncthreads();

        // Compute partial sum
        for (int k = 0; k < TILE_SIZE; ++k) {
            sum += As[threadIdx.y][k] * Bs[k][threadIdx.x];
        }

        __syncthreads();
    }

    if (row < M && col < N) {
        C[row * N + col] = sum;
    }
}
```

### 4.4 Kernel Launch Configuration
```cpp
// Simple 1D launch
int threads = 256;
int blocks = (size + threads - 1) / threads;
kernel<<<blocks, threads>>>(args);

// 2D launch
dim3 threads(16, 16);
dim3 blocks((cols + threads.x - 1) / threads.x,
            (rows + threads.y - 1) / threads.y);
kernel<<<blocks, threads>>>(args);

// With shared memory and stream
size_t shared_mem_size = TILE_SIZE * TILE_SIZE * sizeof(float);
kernel<<<blocks, threads, shared_mem_size, stream>>>(args);
```

## 5. CUDA File Organization

### 5.1 File Structure
```
cuda/
|-- kernels/
|   |-- kernel1.cu
|   |-- kernel2.cu
|   `-- kernel_utils.cuh
`-- utils/
    |-- cuda_utils.cu
    `-- cuda_utils.cuh
```

### 5.2 Header Files (.cuh)
```cpp
// kernel.cuh
#pragma once

#include <cuda_runtime.h>

// Kernel declaration
__global__ void myKernel(const float* input, float* output, int size);

// Host function declaration
void launchMyKernel(const float* d_input, float* d_output, int size);
```

### 5.3 Implementation Files (.cu)
```cpp
// kernel.cu
#include "kernel.cuh"

__global__ void myKernel(const float* input, float* output, int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = input[idx] * 2.0f;
    }
}

void launchMyKernel(const float* d_input, float* d_output, int size) {
    int threads = 256;
    int blocks = (size + threads - 1) / threads;

    myKernel<<<blocks, threads>>>(d_input, d_output, size);
    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());
}
```

## 6. CUDA Kernel Documentation

### 6.1 Kernel Documentation Template
```cpp
/**
 * @brief Matrix multiplication kernel: C = A * B
 *
 * @param A Input matrix A (M x K)
 * @param B Input matrix B (K x N)
 * @param C Output matrix C (M x N)
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @note Launch configuration:
 *       - Block size: (TILE_SIZE, TILE_SIZE)
 *       - Grid size: ((N + TILE_SIZE - 1) / TILE_SIZE, (M + TILE_SIZE - 1) / TILE_SIZE)
 * @note Shared memory usage: 2 * TILE_SIZE * TILE_SIZE * sizeof(float)
 * @note Memory access pattern: Coalesced reads and writes
 */
__global__ void matrixMulKernel(const float* A, const float* B, float* C,
                                 int M, int K, int N);
```

### 6.2 Host Function Documentation
```cpp
/**
 * @brief Computes the dot product of two vectors on GPU
 *
 * @param d_a Device pointer to first vector
 * @param d_b Device pointer to second vector
 * @param n Number of elements in each vector
 * @return float The computed dot product
 *
 * @pre d_a and d_b must point to valid device memory of size n
 * @pre n must be positive
 * @post Device memory is not modified
 *
 * @throws std::runtime_error if CUDA operations fail
 *
 * @note This function synchronises the device
 * @note Time complexity: O(n)
 * @note Space complexity: O(1) device memory
 */
float cudaDotProduct(const float* d_a, const float* d_b, size_t n);
```

## 7. CUDA Performance Optimisation

### 7.1 Memory Coalescing
```cpp
// Good: Coalesced access
__global__ void coalesced(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        data[idx] = data[idx] * 2.0f;  // Sequential access
    }
}

// Bad: Strided access
__global__ void strided(float* data, int n, int stride) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        data[idx * stride] = data[idx * stride] * 2.0f;  // Non-coalesced
    }
}
```

### 7.2 Occupancy Optimisation
```cpp
// Check register usage and occupancy
// Compile with: nvcc -Xptxas=-v kernel.cu

// Limit register usage if needed
__global__ void __launch_bounds__(MAX_THREADS_PER_BLOCK, MIN_BLOCKS_PER_SM)
kernel(float* data, int n) {
    // Kernel implementation
}
```

### 7.3 Warp Divergence Minimisation
```cpp
// Bad: High divergence
__global__ void divergent(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        if (idx % 2 == 0) {
            // Even threads do this
            data[idx] = expf(data[idx]);
        } else {
            // Odd threads do this
            data[idx] = logf(data[idx]);
        }
    }
}

// Better: Reduce divergence
__global__ void lessdivergent(float* data, int n) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < n) {
        // All threads in a warp do the same thing
        data[idx] = expf(data[idx]);
    }
}
```

### 7.4 CUDA Streams
```cpp
void processWithStreams(float* h_data, int n, int num_streams) {
    cudaStream_t streams[num_streams];
    for (int i = 0; i < num_streams; ++i) {
        cudaStreamCreate(&streams[i]);
    }

    int chunk_size = n / num_streams;
    for (int i = 0; i < num_streams; ++i) {
        int offset = i * chunk_size;
        float *d_chunk;
        cudaMalloc(&d_chunk, chunk_size * sizeof(float));

        // Asynchronous operations on different streams
        cudaMemcpyAsync(d_chunk, h_data + offset, chunk_size * sizeof(float),
                        cudaMemcpyHostToDevice, streams[i]);

        kernel<<<blocks, threads, 0, streams[i]>>>(d_chunk, chunk_size);

        cudaMemcpyAsync(h_data + offset, d_chunk, chunk_size * sizeof(float),
                        cudaMemcpyDeviceToHost, streams[i]);

        cudaFree(d_chunk);
    }

    // Synchronise all streams
    for (int i = 0; i < num_streams; ++i) {
        cudaStreamSynchronize(streams[i]);
        cudaStreamDestroy(streams[i]);
    }
}
```

## 8. CUDA Debugging and Profiling

### 8.1 cuda-memcheck
```bash
# Check for memory errors
cuda-memcheck ./build/cuda_app

# Check for race conditions
cuda-memcheck --tool racecheck ./build/cuda_app

# Check for shared memory errors
cuda-memcheck --tool synccheck ./build/cuda_app
```

### 8.2 nvprof Profiling
```bash
# Profile application
nvprof ./build/cuda_app

# Detailed metrics
nvprof --metrics all ./build/cuda_app

# Timeline analysis
nvprof --print-gpu-trace ./build/cuda_app
```

### 8.3 Nsight Systems
```bash
# Profile with Nsight Systems
nsys profile --stats=true ./build/cuda_app

# Generate report
nsys profile -o report ./build/cuda_app
```

## 9. CUDA Testing Requirements

### 9.1 CUDA Test Structure
- Test with various input sizes (small, medium, large)
- Test edge cases (empty, boundary conditions)
- Verify correctness against CPU implementation
- Check for memory leaks with cuda-memcheck
- Profile performance with nvprof

### 9.2 CUDA Test Example
```cpp
TEST(CudaKernel, VectorAdd_LargeInput_CorrectOutput) {
    const size_t size = 1024 * 1024;
    std::vector<float> h_a(size, 1.0f);
    std::vector<float> h_b(size, 2.0f);
    std::vector<float> h_c(size);

    float *d_a, *d_b, *d_c;
    CUDA_CHECK(cudaMalloc(&d_a, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_b, size * sizeof(float)));
    CUDA_CHECK(cudaMalloc(&d_c, size * sizeof(float)));

    CUDA_CHECK(cudaMemcpy(d_a, h_a.data(), size * sizeof(float),
                          cudaMemcpyHostToDevice));
    CUDA_CHECK(cudaMemcpy(d_b, h_b.data(), size * sizeof(float),
                          cudaMemcpyHostToDevice));

    int threads = 256;
    int blocks = (size + threads - 1) / threads;
    vectorAdd<<<blocks, threads>>>(d_a, d_b, d_c, size);

    CUDA_CHECK(cudaGetLastError());
    CUDA_CHECK(cudaDeviceSynchronize());

    CUDA_CHECK(cudaMemcpy(h_c.data(), d_c, size * sizeof(float),
                          cudaMemcpyDeviceToHost));

    for (size_t i = 0; i < size; ++i) {
        EXPECT_FLOAT_EQ(h_c[i], 3.0f);
    }

    CUDA_CHECK(cudaFree(d_a));
    CUDA_CHECK(cudaFree(d_b));
    CUDA_CHECK(cudaFree(d_c));
}
```

## 10. CUDA Commit Requirements

### 10.1 Pre-Commit Checklist
When committing CUDA code:
- **Error Checking**: Every CUDA API call MUST be checked
- **Kernel Launches**: Check with `cudaGetLastError()` and `cudaDeviceSynchronize()`
- **Documentation**: Document thread/block dimensions and shared memory usage
- **Testing**: Test with various input sizes and edge cases
- **Profiling**: Profile with `nvprof` or Nsight for performance-critical changes

### 10.2 CUDA Commit Verification
```bash
# Compile with verbose ptxas output
nvcc -Xptxas=-v kernel.cu

# Check for register usage and occupancy
# Profile kernel
nvprof ./build/cuda_app

# Memory check
cuda-memcheck ./build/cuda_app
```

## 11. Forbidden CUDA Practices

**STRICTLY FORBIDDEN**:
- Ignoring CUDA error codes
- Launching kernels without error checking
- Using deprecated CUDA APIs without justification
- Skipping error handling in CUDA code
- Not documenting kernel launch configurations
- Not testing with various input sizes
- Not profiling performance-critical kernels

## 12. Enforcement

### 12.1 Code Review Checklist
- [ ] All CUDA API calls have error checking
- [ ] Kernel launches check for errors
- [ ] Memory management uses RAII or proper cleanup
- [ ] Kernels are documented with launch configuration
- [ ] Tests cover various input sizes
- [ ] Performance is profiled for critical kernels
- [ ] No memory leaks (verified with cuda-memcheck)
