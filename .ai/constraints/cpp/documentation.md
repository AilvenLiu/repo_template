# C++/CUDA Documentation Standards

> **This document defines mandatory documentation standards for C++/CUDA projects.**
> All public APIs and CUDA kernels must be documented using Doxygen-style comments.

## 1. Documentation Requirements

### 1.1 What Must Be Documented
**MANDATORY**: All public APIs MUST have Doxygen documentation:
- Public classes and structs
- Public member functions
- Public free functions
- CUDA kernels
- CUDA device functions (when part of public API)
- Template parameters
- Function parameters and return values
- Exceptions that can be thrown
- Preconditions and postconditions

### 1.2 What Should Be Documented
**RECOMMENDED**:
- Complex algorithms and their approach
- Performance characteristics
- Thread safety guarantees
- Memory ownership semantics
- CUDA-specific details (launch configuration, memory usage)

### 1.3 What Need Not Be Documented
- Private implementation details (unless complex)
- Obvious getters/setters (unless they have side effects)
- Self-explanatory code

## 2. Doxygen Comment Style

### 2.1 Comment Syntax
Use Javadoc-style comments:
```cpp
/**
 * @brief Brief description (one line)
 *
 * Detailed description (multiple lines if needed).
 * Can include multiple paragraphs.
 *
 * @param param1 Description of param1
 * @param param2 Description of param2
 * @return Description of return value
 */
```

### 2.2 Alternative Syntax
Qt-style comments are also acceptable:
```cpp
/*!
 * \brief Brief description
 *
 * Detailed description.
 *
 * \param param1 Description
 * \return Description
 */
```

Choose one style and use it consistently throughout the project.

## 3. Function Documentation

### 3.1 Basic Function Documentation
```cpp
/**
 * @brief Computes the sum of two integers
 *
 * @param a First integer
 * @param b Second integer
 * @return The sum of a and b
 */
int add(int a, int b);
```

### 3.2 Complex Function Documentation
```cpp
/**
 * @brief Computes the matrix product C = A * B using CUDA
 *
 * This function performs matrix multiplication on the GPU using
 * a tiled algorithm with shared memory optimisation.
 *
 * @param d_A Device pointer to matrix A (M x K)
 * @param d_B Device pointer to matrix B (K x N)
 * @param d_C Device pointer to output matrix C (M x N)
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @pre d_A, d_B, d_C must point to valid device memory
 * @pre M, K, N must be positive
 * @post d_C contains the matrix product A * B
 *
 * @throws std::runtime_error if CUDA operations fail
 *
 * @note This function synchronises the device
 * @note Time complexity: O(M * N * K)
 * @note Space complexity: O(1) additional device memory
 *
 * @see matrixMulKernel for kernel implementation details
 *
 * @par Example:
 * @code
 * float *d_A, *d_B, *d_C;
 * cudaMalloc(&d_A, M * K * sizeof(float));
 * cudaMalloc(&d_B, K * N * sizeof(float));
 * cudaMalloc(&d_C, M * N * sizeof(float));
 *
 * matrixMultiply(d_A, d_B, d_C, M, K, N);
 * @endcode
 */
void matrixMultiply(const float* d_A, const float* d_B, float* d_C,
                    int M, int K, int N);
```

## 4. CUDA Kernel Documentation

### 4.1 Kernel Documentation Template
```cpp
/**
 * @brief Matrix multiplication kernel using shared memory tiling
 *
 * @param A Input matrix A in row-major order
 * @param B Input matrix B in row-major order
 * @param C Output matrix C in row-major order
 * @param M Number of rows in A
 * @param K Number of columns in A / rows in B
 * @param N Number of columns in B
 *
 * @note Launch configuration:
 *       - Block size: (TILE_SIZE, TILE_SIZE) = (16, 16)
 *       - Grid size: ((N + TILE_SIZE - 1) / TILE_SIZE,
 *                     (M + TILE_SIZE - 1) / TILE_SIZE)
 *
 * @note Shared memory usage: 2 * TILE_SIZE * TILE_SIZE * sizeof(float)
 *
 * @note Memory access pattern:
 *       - Coalesced reads from global memory
 *       - Shared memory used to reduce global memory accesses
 *       - Each thread computes one element of C
 *
 * @note Performance characteristics:
 *       - Occupancy: ~75% on Volta (sm_70)
 *       - Register usage: 32 registers per thread
 *       - Achieves ~80% of peak FLOPS for large matrices
 */
__global__ void matrixMulKernel(const float* A, const float* B, float* C,
                                 int M, int K, int N);
```

### 4.2 Device Function Documentation
```cpp
/**
 * @brief Computes the dot product of two vectors (device function)
 *
 * @param a Pointer to first vector
 * @param b Pointer to second vector
 * @param n Number of elements
 * @return The dot product of a and b
 *
 * @note This is a device function, callable only from kernels
 * @note Assumes a and b have at least n elements
 */
__device__ float dotProduct(const float* a, const float* b, int n);
```

## 5. Class Documentation

### 5.1 Class Documentation
```cpp
/**
 * @brief RAII wrapper for CUDA device memory
 *
 * This class provides automatic memory management for CUDA device
 * memory allocations. Memory is allocated in the constructor and
 * freed in the destructor.
 *
 * @tparam T Type of elements stored in device memory
 *
 * @note This class is move-only (copy operations are deleted)
 * @note Memory is automatically freed when the object is destroyed
 *
 * @par Example:
 * @code
 * CudaDeviceMemory<float> d_data(1024);
 * cudaMemcpy(d_data.get(), h_data, 1024 * sizeof(float),
 *            cudaMemcpyHostToDevice);
 * kernel<<<blocks, threads>>>(d_data.get(), 1024);
 * @endcode
 */
template<typename T>
class CudaDeviceMemory {
public:
    /**
     * @brief Constructs a CudaDeviceMemory object and allocates device memory
     *
     * @param count Number of elements to allocate
     * @throws std::runtime_error if cudaMalloc fails
     */
    explicit CudaDeviceMemory(size_t count);

    /**
     * @brief Destructor - frees device memory
     */
    ~CudaDeviceMemory();

    /**
     * @brief Gets the raw device pointer
     *
     * @return Pointer to device memory
     */
    T* get();

    /**
     * @brief Gets the number of elements allocated
     *
     * @return Number of elements
     */
    size_t size() const;
};
```

### 5.2 Member Function Documentation
```cpp
/**
 * @brief Resizes the buffer to a new size
 *
 * If the new size is larger than the current size, the buffer is
 * reallocated and existing data is copied. If smaller, the buffer
 * is truncated.
 *
 * @param new_size New size in number of elements
 * @throws std::bad_alloc if memory allocation fails
 *
 * @note This operation may invalidate existing pointers to the buffer
 * @note Time complexity: O(min(old_size, new_size)) for data copy
 */
void resize(size_t new_size);
```

## 6. Doxygen Tags Reference

### 6.1 Common Tags
- `@brief`: Brief description (one line)
- `@param`: Parameter description
- `@return`: Return value description
- `@throws` or `@exception`: Exception that can be thrown
- `@note`: Additional notes
- `@warning`: Important warnings
- `@see`: Cross-reference to related items
- `@code` / `@endcode`: Code examples

### 6.2 Preconditions and Postconditions
- `@pre`: Precondition (what must be true before calling)
- `@post`: Postcondition (what will be true after calling)
- `@invariant`: Class invariant

### 6.3 Template Documentation
- `@tparam`: Template parameter description

### 6.4 Grouping and Organisation
- `@defgroup`: Define a group
- `@ingroup`: Add to a group
- `@{` / `@}`: Group multiple items

### 6.5 Deprecation
- `@deprecated`: Mark as deprecated

## 7. Implementation Comments

### 7.1 Complex Algorithms
```cpp
void complexAlgorithm(const std::vector<float>& data) {
    // Phase 1: Sort data using quicksort
    // We use quicksort here because the data is typically
    // already partially sorted, giving O(n log n) performance
    std::sort(data.begin(), data.end());

    // Phase 2: Remove duplicates using two-pointer technique
    // This is more efficient than using std::unique because
    // we can avoid the erase operation
    size_t write_idx = 0;
    for (size_t read_idx = 0; read_idx < data.size(); ++read_idx) {
        if (read_idx == 0 || data[read_idx] != data[read_idx - 1]) {
            data[write_idx++] = data[read_idx];
        }
    }
}
```

### 7.2 Performance Optimisations
```cpp
// Use shared memory to reduce global memory accesses
// This optimisation improves performance by ~3x for large matrices
__shared__ float tile[TILE_SIZE][TILE_SIZE];

// Coalesced memory access pattern
// Threads in a warp access consecutive memory locations
int idx = blockIdx.x * blockDim.x + threadIdx.x;
data[idx] = input[idx];
```

### 7.3 CUDA-Specific Comments
```cpp
// Launch configuration chosen to maximise occupancy
// Block size of 256 gives 75% occupancy on Volta (sm_70)
// Grid size ensures all elements are processed
int threads = 256;
int blocks = (size + threads - 1) / threads;
kernel<<<blocks, threads>>>(data, size);

// Synchronise to ensure kernel completion before accessing results
cudaDeviceSynchronize();
```

### 7.4 Avoid Obvious Comments
```cpp
// Bad: States the obvious
int x = 5;  // Set x to 5
x++;        // Increment x

// Good: Explains why
int buffer_size = 1024;  // Power of 2 for alignment
buffer_size *= 2;        // Double buffer for ping-pong technique
```

## 8. File-Level Documentation

### 8.1 Header File Documentation
```cpp
/**
 * @file matrix_ops.hpp
 * @brief Matrix operations using CUDA
 *
 * This file provides GPU-accelerated matrix operations including
 * multiplication, addition, and transpose.
 *
 * @author Project Team
 * @date 2024-01-15
 */

#pragma once

#include <cuda_runtime.h>

// ... declarations ...
```

### 8.2 Implementation File Documentation
```cpp
/**
 * @file matrix_ops.cu
 * @brief Implementation of CUDA matrix operations
 */

#include "matrix_ops.hpp"

// ... implementations ...
```

## 9. README.md Documentation

### 9.1 Project README Template
```markdown
# Project Name

Brief description of the project.

## Requirements

### Build Requirements
- CMake 3.20 or later
- C++17 compatible compiler:
  - GCC 9.0+
  - Clang 10.0+
  - MSVC 2019+
- CUDA Toolkit 11.0+ (for CUDA features)

### Runtime Requirements
- CUDA-capable GPU with compute capability 7.0+ (Volta or later)
- CUDA Runtime 11.0+

## Dependencies

- **Eigen3** (3.4.0+): Linear algebra operations
- **Google Test** (1.12.0+): Unit testing framework
- **spdlog** (1.10.0+): Logging library

## Building

```bash
# Clone repository
git clone https://github.com/user/project.git
cd project

# Create build directory
mkdir build && cd build

# Configure
cmake .. -DCMAKE_BUILD_TYPE=Release \
         -DCMAKE_CUDA_ARCHITECTURES="70;75;80;86"

# Build
cmake --build . -j$(nproc)

# Run tests
ctest --output-on-failure
```

## Usage

```cpp
#include "project/api.hpp"

int main() {
    // Example usage
    auto result = compute(input);
    return 0;
}
```

## Performance

Benchmark results on NVIDIA RTX 3090:
- Matrix multiplication (4096x4096): 2.3 ms
- Convolution (1024x1024, 3x3 kernel): 0.8 ms

## License

MIT Licence - see LICENCE file for details.
```

## 10. API Documentation Generation

### 10.1 Doxygen Configuration
Create `Doxyfile`:
```
PROJECT_NAME           = "Project Name"
PROJECT_BRIEF          = "Brief description"
OUTPUT_DIRECTORY       = docs
INPUT                  = include src
RECURSIVE              = YES
EXTRACT_ALL            = NO
EXTRACT_PRIVATE        = NO
EXTRACT_STATIC         = YES
GENERATE_HTML          = YES
GENERATE_LATEX         = NO
```

### 10.2 Generating Documentation
```bash
# Generate documentation
doxygen Doxyfile

# View documentation
open docs/html/index.html
```

## 11. Character Encoding Requirements

### 11.1 ASCII-Only Requirement
**STRICTLY FORBIDDEN**: Use of ANY Non-ASCII characters in documentation:
- Source code comments
- Doxygen documentation
- README files
- Any documentation files

**Allowed**: Only ASCII characters (0x00-0x7F)

### 11.2 British English Requirement
**MANDATORY**: All documentation MUST use British English spelling:
- colour (not color)
- behaviour (not behavior)
- optimise (not optimize)
- initialise (not initialize)
- synchronise (not synchronize)

Example:
```cpp
/**
 * @brief Initialises the colour buffer
 *
 * This function initialises the colour buffer with default values
 * and optimises memory usage.
 */
void initialiseColourBuffer();
```

## 12. Documentation Best Practices

### 12.1 Be Concise
- Keep brief descriptions to one line
- Use detailed descriptions for complex behaviour
- Avoid redundant information

### 12.2 Be Accurate
- Keep documentation in sync with code
- Update documentation when changing code
- Remove outdated comments

### 12.3 Be Helpful
- Explain why, not just what
- Provide examples for complex APIs
- Document edge cases and limitations

### 12.4 Be Consistent
- Use same style throughout project
- Follow team conventions
- Use consistent terminology

## 13. Pre-Commit Documentation Requirements

### 13.1 Before Every Commit
**MANDATORY**:
- All public APIs have Doxygen documentation
- CUDA kernels are documented with launch configuration
- Complex algorithms have explanatory comments
- README.md is updated if dependencies change

### 13.2 Documentation Review Checklist
- [ ] All public APIs documented
- [ ] CUDA kernels documented with launch configuration
- [ ] Parameters and return values documented
- [ ] Exceptions documented
- [ ] Examples provided for complex APIs
- [ ] British English spelling used
- [ ] ASCII-only characters used

## 14. Code Review Checklist

### 14.1 Documentation Review
- [ ] Documentation is clear and complete
- [ ] Documentation matches implementation
- [ ] Examples are correct and helpful
- [ ] No outdated comments
- [ ] British English spelling
- [ ] ASCII-only characters

## 15. Enforcement

### 15.1 Mandatory Documentation
- All public APIs must be documented
- PRs without documentation will be rejected
- Documentation is part of code review

### 15.2 Documentation Quality
- Documentation must be accurate
- Documentation must be helpful
- Documentation must follow style guide

## 16. Tools and Integration

### 16.1 Editor Integration
- Configure editor to show Doxygen comments
- Use plugins for Doxygen comment generation
- Enable spell-checking for comments (British English)

### 16.2 CI/CD Integration
```yaml
# Generate and publish documentation
documentation:
  stage: deploy
  script:
    - doxygen Doxyfile
    - rsync -av docs/html/ /var/www/docs/
```

## 17. Examples

### 17.1 Complete Function Example
```cpp
/**
 * @brief Performs convolution on GPU
 *
 * This function performs 2D convolution of an input image with a kernel
 * using CUDA. The implementation uses shared memory for the kernel and
 * handles boundary conditions with zero-padding.
 *
 * @param d_input Device pointer to input image (height x width)
 * @param d_kernel Device pointer to convolution kernel (kernel_size x kernel_size)
 * @param d_output Device pointer to output image (height x width)
 * @param width Width of input image
 * @param height Height of input image
 * @param kernel_size Size of convolution kernel (must be odd)
 *
 * @pre d_input, d_kernel, d_output must point to valid device memory
 * @pre width, height must be positive
 * @pre kernel_size must be odd and positive
 * @post d_output contains the convolved image
 *
 * @throws std::invalid_argument if kernel_size is even
 * @throws std::runtime_error if CUDA operations fail
 *
 * @note This function synchronises the device
 * @note Time complexity: O(width * height * kernel_size^2)
 * @note Shared memory usage: kernel_size^2 * sizeof(float)
 *
 * @see convolutionKernel for kernel implementation
 *
 * @par Example:
 * @code
 * const int width = 1024, height = 1024, kernel_size = 3;
 * float *d_input, *d_kernel, *d_output;
 *
 * cudaMalloc(&d_input, width * height * sizeof(float));
 * cudaMalloc(&d_kernel, kernel_size * kernel_size * sizeof(float));
 * cudaMalloc(&d_output, width * height * sizeof(float));
 *
 * // ... initialise input and kernel ...
 *
 * convolution(d_input, d_kernel, d_output, width, height, kernel_size);
 * @endcode
 */
void convolution(const float* d_input, const float* d_kernel, float* d_output,
                 int width, int height, int kernel_size);
```

### 17.2 Complete Class Example
```cpp
/**
 * @brief Thread-safe queue for GPU work items
 *
 * This class provides a thread-safe queue for managing GPU work items.
 * Multiple threads can safely enqueue and dequeue items concurrently.
 *
 * @tparam T Type of work items
 *
 * @note This class is thread-safe
 * @note Blocking operations will wait until items are available
 *
 * @par Example:
 * @code
 * WorkQueue<Task> queue;
 *
 * // Producer thread
 * queue.enqueue(task);
 *
 * // Consumer thread
 * Task task = queue.dequeue();  // Blocks until item available
 * @endcode
 */
template<typename T>
class WorkQueue {
public:
    /**
     * @brief Constructs an empty work queue
     */
    WorkQueue();

    /**
     * @brief Enqueues a work item
     *
     * @param item Work item to enqueue
     * @note Thread-safe
     */
    void enqueue(T item);

    /**
     * @brief Dequeues a work item
     *
     * Blocks until an item is available.
     *
     * @return The dequeued work item
     * @note Thread-safe
     * @note Blocking operation
     */
    T dequeue();

    /**
     * @brief Checks if the queue is empty
     *
     * @return true if empty, false otherwise
     * @note Thread-safe
     */
    bool empty() const;
};
```

## 18. Forbidden Practices

**STRICTLY FORBIDDEN**:
- Undocumented public APIs
- Outdated or incorrect documentation
- Non-ASCII characters in documentation
- American English spelling
- Obvious or redundant comments
- Documentation that contradicts code
