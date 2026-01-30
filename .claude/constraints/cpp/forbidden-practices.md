# C++/CUDA Forbidden Practices

> **This document defines absolutely forbidden practices for C++/CUDA development.**
> These rules apply to all C++/CUDA projects without exception.
> Violations are considered critical failures.

## Overview

This document consolidates all forbidden practices that Claude Code MUST NEVER perform
when working on C++/CUDA projects. These are non-negotiable constraints that apply
regardless of context or user instructions.

## 1. Git and Version Control

### 1.1 Protected Branch Commits

**ABSOLUTELY FORBIDDEN**: Committing directly to protected branches.

Protected branches include:
- `master`
- `main`
- `develop`
- `release/*`
- `hotfix/*`

**Always** work on feature branches and create pull requests.

### 1.2 Committing Without Validation

**FORBIDDEN**:
- Committing code with compiler warnings
- Committing code without running clang-format
- Committing code without static analysis (clang-tidy, cppcheck)
- Committing code with failing tests
- Skipping pre-commit validation

## 2. Memory Management

### 2.1 Raw Pointers for Ownership

**ABSOLUTELY FORBIDDEN**: Using raw pointers for ownership.

```cpp
// FORBIDDEN: Raw pointer ownership
class ResourceManager {
    Resource* resource;  // Who owns this? Who deletes it?
public:
    ResourceManager() : resource(new Resource()) {}
    ~ResourceManager() { delete resource; }  // Manual management
};

// REQUIRED: Smart pointers for ownership
class ResourceManager {
    std::unique_ptr<Resource> resource;
public:
    ResourceManager() : resource(std::make_unique<Resource>()) {}
    // Automatic cleanup, no manual delete needed
};
```

### 2.2 Manual new/delete

**FORBIDDEN**: Using manual `new`/`delete` in application code.

```cpp
// FORBIDDEN: Manual memory management
void process() {
    int* data = new int[100];
    // ... processing ...
    delete[] data;  // Easy to forget, exception-unsafe
}

// REQUIRED: RAII and smart pointers
void process() {
    auto data = std::make_unique<int[]>(100);
    // ... processing ...
    // Automatic cleanup
}

// Or use containers
void process() {
    std::vector<int> data(100);
    // ... processing ...
}
```

### 2.3 Ignoring RAII

**FORBIDDEN**: Implementing manual resource management when RAII is possible.

```cpp
// FORBIDDEN: Manual resource management
void processFile() {
    FILE* file = fopen("data.txt", "r");
    if (!file) return;
    // ... processing ...
    fclose(file);  // Easy to miss on early returns
}

// REQUIRED: RAII wrappers
void processFile() {
    std::ifstream file("data.txt");
    if (!file) return;
    // ... processing ...
    // Automatic close on scope exit
}
```

## 3. Type Safety

### 3.1 C-Style Casts

**ABSOLUTELY FORBIDDEN**: Using C-style casts.

```cpp
// FORBIDDEN: C-style casts
void* ptr = getData();
int* intPtr = (int*)ptr;  // Dangerous, no compile-time checks

double value = 3.14159;
int truncated = (int)value;  // Unclear intent

Base* base = getBase();
Derived* derived = (Derived*)base;  // Unsafe downcast

// REQUIRED: C++ casts with explicit intent
void* ptr = getData();
int* intPtr = static_cast<int*>(ptr);  // Clear intent

double value = 3.14159;
int truncated = static_cast<int>(value);  // Explicit truncation

Base* base = getBase();
Derived* derived = dynamic_cast<Derived*>(base);  // Safe downcast
if (derived) {
    // Use derived
}
```

### 3.2 const_cast Abuse

**FORBIDDEN**: Using `const_cast` to modify const data.

```cpp
// FORBIDDEN: Removing const to modify
void modify(const std::string& str) {
    const_cast<std::string&>(str) = "modified";  // Undefined behaviour
}

// ALLOWED: Only for interfacing with legacy C APIs
void legacyApi(char* str);  // C API that doesn't modify

void wrapper(const std::string& str) {
    // Only if legacyApi truly doesn't modify
    legacyApi(const_cast<char*>(str.c_str()));
}
```

## 4. Namespace and Scope

### 4.1 using namespace in Headers

**ABSOLUTELY FORBIDDEN**: Using `using namespace` in header files.

```cpp
// FORBIDDEN: In header files
// myheader.hpp
#pragma once
using namespace std;  // Pollutes all includers' namespaces

// REQUIRED: Explicit qualification in headers
// myheader.hpp
#pragma once
std::string processData(const std::string& input);
std::vector<int> getData();
```

### 4.2 using namespace std in Implementation

**DISCOURAGED**: Using `using namespace std;` even in implementation files.

```cpp
// DISCOURAGED: Global using namespace
using namespace std;

// PREFERRED: Specific using declarations
using std::string;
using std::vector;
using std::cout;

// BEST: Explicit qualification
std::string name = "example";
std::vector<int> data;
```

### 4.3 Macro Collisions

**FORBIDDEN**: Defining macros that could collide with user code.

```cpp
// FORBIDDEN: Generic macro names
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define ERROR -1
#define SUCCESS 0

// REQUIRED: Namespaced or prefixed macros
#define MYLIB_MAX(a, b) ((a) > (b) ? (a) : (b))
#define MYLIB_ERROR -1

// BETTER: Use constexpr and templates
template<typename T>
constexpr T myMax(T a, T b) { return (a > b) ? a : b; }

namespace mylib {
    constexpr int kError = -1;
    constexpr int kSuccess = 0;
}
```

## 5. Concurrency

### 5.1 Unsynchronised Global State

**ABSOLUTELY FORBIDDEN**: Modifying global state without synchronisation.

```cpp
// FORBIDDEN: Unsynchronised global access
int globalCounter = 0;

void increment() {
    globalCounter++;  // Data race in multithreaded code
}

// REQUIRED: Proper synchronisation
std::atomic<int> globalCounter{0};

void increment() {
    globalCounter++;  // Atomic operation
}

// Or use mutex
std::mutex counterMutex;
int globalCounter = 0;

void increment() {
    std::lock_guard<std::mutex> lock(counterMutex);
    globalCounter++;
}
```

## 6. CUDA-Specific

### 6.1 Ignoring CUDA Error Codes

**ABSOLUTELY FORBIDDEN**: Ignoring CUDA error codes.

```cpp
// FORBIDDEN: Ignoring errors
cudaMalloc(&ptr, size);
cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice);
myKernel<<<blocks, threads>>>();

// REQUIRED: Check all CUDA calls
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            throw std::runtime_error( \
                std::string("CUDA error: ") + cudaGetErrorString(error)); \
        } \
    } while(0)

CUDA_CHECK(cudaMalloc(&ptr, size));
CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice));
myKernel<<<blocks, threads>>>();
CUDA_CHECK(cudaGetLastError());
CUDA_CHECK(cudaDeviceSynchronize());
```

### 6.2 Kernel Launch Without Error Check

**FORBIDDEN**: Launching CUDA kernels without error checking.

```cpp
// FORBIDDEN: No error check after kernel
myKernel<<<blocks, threads>>>(args);
// Errors are silently ignored

// REQUIRED: Always check after kernel launch
myKernel<<<blocks, threads>>>(args);
CUDA_CHECK(cudaGetLastError());  // Check launch errors
CUDA_CHECK(cudaDeviceSynchronize());  // Check execution errors
```

### 6.3 Deprecated CUDA APIs

**FORBIDDEN**: Using deprecated CUDA APIs without justification.

```cpp
// FORBIDDEN: Deprecated APIs
cudaThreadSynchronize();  // Deprecated
cudaThreadExit();  // Deprecated

// REQUIRED: Modern equivalents
cudaDeviceSynchronize();
cudaDeviceReset();
```

## 7. Code Quality

### 7.1 Compiler Warnings

**ABSOLUTELY FORBIDDEN**: Committing code with compiler warnings.

All code MUST compile cleanly with:
```bash
-Wall -Wextra -Wpedantic -Werror
```

### 7.2 Ignoring Static Analysis

**FORBIDDEN**: Ignoring clang-tidy or cppcheck warnings without justification.

```cpp
// FORBIDDEN: Blanket suppression
// NOLINT

// ALLOWED: Specific suppression with justification
// NOLINTNEXTLINE(cppcoreguidelines-pro-type-reinterpret-cast) - Required for hardware interface
auto* hwPtr = reinterpret_cast<HardwareRegister*>(address);
```

## 8. Summary Table

| Practice | Status | Alternative |
|----------|--------|-------------|
| Direct commits to protected branches | FORBIDDEN | Use feature branches |
| Raw pointers for ownership | FORBIDDEN | Smart pointers |
| Manual new/delete | FORBIDDEN | RAII, containers |
| C-style casts | FORBIDDEN | C++ casts |
| `using namespace` in headers | FORBIDDEN | Explicit qualification |
| Generic macro names | FORBIDDEN | Prefixed/namespaced |
| Unsynchronised global state | FORBIDDEN | Atomics or mutexes |
| Ignoring CUDA errors | FORBIDDEN | Check all calls |
| Kernel launch without check | FORBIDDEN | Check after launch |
| Deprecated CUDA APIs | FORBIDDEN | Modern equivalents |
| Compiler warnings | FORBIDDEN | Fix all warnings |

## 9. Enforcement

### 9.1 Pre-Commit Checks

All forbidden practices MUST be caught by pre-commit validation:
- clang-format (formatting)
- clang-tidy (static analysis)
- cppcheck (additional checks)
- Compiler with -Werror (warnings as errors)

### 9.2 Code Review

Pull requests MUST be rejected if they contain any forbidden practices.

### 9.3 CI/CD

CI pipelines MUST fail if any forbidden practice is detected.

## 10. Exceptions

There are NO exceptions to these rules unless:
1. Explicitly documented in the codebase with justification
2. Approved by the project maintainer
3. Tracked in a technical debt register

Even then, the following are NEVER acceptable:
- Ignoring CUDA error codes
- Raw pointer ownership without RAII wrapper
- Direct commits to protected branches
- Compiler warnings in committed code
