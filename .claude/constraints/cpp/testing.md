# C++/CUDA Testing Requirements

> **This document defines mandatory testing standards for C++/CUDA projects.**
> All code contributions must meet these testing requirements.

## 1. Testing Framework

### 1.1 Preferred Framework
- **Primary**: Google Test (gtest/gmock)
- **Alternative**: Catch2
- **CUDA Testing**: Separate host and device tests

### 1.2 Framework Setup

Using Google Test:
```cpp
// test_module.cpp
#include <gtest/gtest.h>
#include "module.hpp"

class ModuleTest : public ::testing::Test {
protected:
    void SetUp() override {
        // Setup code
    }

    void TearDown() override {
        // Cleanup code
    }
};

TEST_F(ModuleTest, FunctionName_Condition_ExpectedBehavior) {
    // Arrange
    int input = 42;

    // Act
    int result = function_under_test(input);

    // Assert
    EXPECT_EQ(result, 84);
}

TEST_F(ModuleTest, FunctionName_InvalidInput_ThrowsException) {
    EXPECT_THROW(function_under_test(-1), std::invalid_argument);
}
```

## 2. Test Organization

### 2.1 Directory Structure
```
tests/
|-- unit/
|   |-- test_module1.cpp
|   |-- test_module2.cpp
|   `-- CMakeLists.txt
|-- integration/
|   |-- test_workflow.cpp
|   `-- CMakeLists.txt
|-- cuda/
|   |-- test_kernels.cu
|   |-- test_memory.cu
|   `-- CMakeLists.txt
`-- benchmarks/
    |-- benchmark_matrix_mul.cpp
    `-- CMakeLists.txt
```

### 2.2 Test File Naming
- Unit tests: `test_<module_name>.cpp`
- Integration tests: `test_<workflow_name>.cpp`
- CUDA tests: `test_<kernel_name>.cu`
- Benchmarks: `benchmark_<feature>.cpp`

## 3. Test Naming Convention

### 3.1 Test Case Naming
```cpp
TEST(ModuleName, FunctionName_Condition_ExpectedBehavior) {
    // Arrange
    // Act
    // Assert
}

// Examples
TEST(VectorMath, DotProduct_EmptyVectors_ReturnsZero) { }
TEST(CudaKernel, MatrixMultiply_SquareMatrices_CorrectResult) { }
```

### 3.2 Naming Guidelines
- **ModuleName**: The module or class being tested
- **FunctionName**: The specific function under test
- **Condition**: The input condition or scenario
- **ExpectedBehavior**: What should happen

## 4. CUDA Testing

### 4.1 CUDA Test Structure
```cpp
// test_cuda_kernel.cu
#include <gtest/gtest.h>
#include <cuda_runtime.h>
#include "kernels.cuh"

class CudaKernelTest : public ::testing::Test {
protected:
    void SetUp() override {
        cudaMalloc(&d_input, size * sizeof(float));
        cudaMalloc(&d_output, size * sizeof(float));
    }

    void TearDown() override {
        cudaFree(d_input);
        cudaFree(d_output);
    }

    float* d_input;
    float* d_output;
    size_t size = 1024;
};

TEST_F(CudaKernelTest, VectorAdd_ValidInput_CorrectOutput) {
    // Arrange
    std::vector<float> h_input(size, 1.0f);
    std::vector<float> h_output(size);

    cudaMemcpy(d_input, h_input.data(), size * sizeof(float),
               cudaMemcpyHostToDevice);

    // Act
    vectorAddKernel<<<(size + 255) / 256, 256>>>(d_input, d_output, size);
    cudaDeviceSynchronize();

    // Assert
    ASSERT_EQ(cudaGetLastError(), cudaSuccess);
    cudaMemcpy(h_output.data(), d_output, size * sizeof(float),
               cudaMemcpyDeviceToHost);

    for (size_t i = 0; i < size; ++i) {
        EXPECT_FLOAT_EQ(h_output[i], 2.0f);
    }
}
```

### 4.2 CUDA Testing Requirements
- **Error Checking**: Check CUDA errors after kernel launches
- **Synchronization**: Use `cudaDeviceSynchronize()` before assertions
- **Memory Management**: Use RAII or proper cleanup in TearDown
- **Various Input Sizes**: Test with edge cases (empty, small, large)
- **Device Capabilities**: Test on target compute capabilities

### 4.3 CUDA Test Checklist
```bash
# Compile with verbose ptxas output
nvcc -Xptxas=-v kernel.cu

# Check for register usage and occupancy
# Profile kernel
nvprof ./build/cuda_app

# Memory check
cuda-memcheck ./build/cuda_app
```

## 5. Test Coverage Requirements

### 5.1 Coverage Targets
- **Minimum Coverage**: 70% line coverage
- **Target Coverage**: 80%+ line coverage
- **Critical Paths**: 90%+ coverage for core algorithms
- **CUDA Kernels**: Test with various input sizes and edge cases

### 5.2 Coverage Tools
- **C++ Coverage**: Use `gcov`/`lcov` for C++
- **CUDA Profiling**: Use `nvprof`/`nsight` for CUDA

### 5.3 Generating Coverage Reports
```bash
# Generate coverage report
cmake .. -DCMAKE_BUILD_TYPE=Debug -DCMAKE_CXX_FLAGS="--coverage"
cmake --build .
ctest
lcov --capture --directory . --output-file coverage.info
lcov --remove coverage.info '/usr/*' '*/tests/*' --output-file coverage.info
genhtml coverage.info --output-directory coverage_report
```

## 6. Test Requirements

### 6.1 Mandatory Testing Rules
**MANDATORY**:
- All new features MUST include unit tests
- Bug fixes MUST include regression tests
- CUDA kernels MUST have correctness tests
- Performance-critical code SHOULD have benchmarks

### 6.2 Test Compilation
**MANDATORY**: Every commit MUST:
- Compile successfully with the project's supported compilers
- Produce no warnings with strict warning flags enabled
- Pass all existing tests

```bash
# Verify before committing
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug \
         -DCMAKE_CXX_FLAGS="-Wall -Wextra -Wpedantic -Werror"
cmake --build .
ctest --output-on-failure
```

## 7. Test Patterns

### 7.1 Arrange-Act-Assert Pattern
All tests should follow the AAA pattern:
```cpp
TEST(Module, Function_Condition_Behavior) {
    // Arrange: Set up test data and preconditions
    int input = 42;

    // Act: Execute the function under test
    int result = function_under_test(input);

    // Assert: Verify the expected outcome
    EXPECT_EQ(result, 84);
}
```

### 7.2 Edge Case Testing
Always test edge cases:
- Empty inputs
- Null pointers (if applicable)
- Boundary values (min, max)
- Invalid inputs
- Large inputs

Example:
```cpp
TEST(VectorMath, DotProduct_EmptyVectors_ReturnsZero) {
    std::vector<float> empty;
    EXPECT_EQ(dotProduct(empty, empty), 0.0f);
}

TEST(VectorMath, DotProduct_DifferentSizes_ThrowsException) {
    std::vector<float> v1{1.0f, 2.0f};
    std::vector<float> v2{1.0f};
    EXPECT_THROW(dotProduct(v1, v2), std::invalid_argument);
}
```

## 8. CMake Test Integration

### 8.1 Test Target Configuration
```cmake
# In tests/CMakeLists.txt
enable_testing()

# Unit tests
add_executable(unit_tests
    unit/test_module1.cpp
    unit/test_module2.cpp
)
target_link_libraries(unit_tests PRIVATE
    mylib
    GTest::gtest_main
)
add_test(NAME UnitTests COMMAND unit_tests)

# CUDA tests
add_executable(cuda_tests
    cuda/test_kernels.cu
    cuda/test_memory.cu
)
target_link_libraries(cuda_tests PRIVATE
    mylib
    GTest::gtest_main
    CUDA::cudart
)
add_test(NAME CudaTests COMMAND cuda_tests)
```

## 9. Pre-Commit Test Requirements

### 9.1 Before Every Commit
Before EVERY commit operation, Claude Code MUST:
1. Ensure all tests pass
2. Verify no compiler warnings
3. Check test coverage meets minimum threshold

### 9.2 Test Execution
```bash
# Run all tests
cd build
ctest --output-on-failure

# Run specific test suite
./unit_tests
./cuda_tests

# Run with verbose output
ctest -V
```

## 10. Continuous Integration Testing

### 10.1 CI Requirements
All PRs MUST pass CI checks:
- Compilation on all supported platforms
- All tests pass
- Coverage threshold met (if configured)

### 10.2 Example CI Test Configuration
```yaml
- name: Test
  run: cd build && ctest --output-on-failure

- name: Coverage
  run: |
    lcov --capture --directory . --output-file coverage.info
    lcov --list coverage.info
```

## 11. Performance Testing

### 11.1 Benchmark Requirements
Performance-critical code SHOULD have benchmarks:
- Measure execution time
- Compare against baseline
- Test with realistic data sizes
- Profile memory usage

### 11.2 CUDA Performance Testing
- **Profiling**: Profile with `nvprof` or Nsight for performance-critical changes
- **Occupancy**: Check occupancy with `--ptxas-options=-v`
- **Memory Bandwidth**: Measure effective bandwidth
- **Kernel Timing**: Use CUDA events for accurate timing

## 12. Test Documentation

### 12.1 Test Comments
Document complex test scenarios:
```cpp
// Test that the kernel correctly handles matrices where dimensions
// are not multiples of the tile size, ensuring proper boundary checks
TEST(MatrixMul, NonTileSizeDimensions_CorrectResult) {
    // Test with 1023x1023 matrices (not divisible by 16)
    // ...
}
```

## 13. Enforcement

### 13.1 Test Failures
- Tests MUST pass before committing
- Failing tests MUST be fixed or disabled with justification
- Disabled tests MUST have tracking issues

### 13.2 Code Review Checklist
- [ ] All tests pass
- [ ] New features have unit tests
- [ ] Bug fixes have regression tests
- [ ] CUDA kernels have correctness tests
- [ ] Test coverage meets minimum threshold
- [ ] Tests follow naming conventions
- [ ] Edge cases are tested
