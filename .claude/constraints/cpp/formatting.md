# C++/CUDA Code Formatting and Style Standards

> **This document defines mandatory code formatting and style requirements for C++/CUDA projects.**
> All code must adhere to these standards before committing.

## 1. Code Formatting Tool

### 1.1 clang-format (Mandatory)
**MANDATORY**: Format code before committing:

```bash
# clang-format (use project .clang-format config)
clang-format -i src/**/*.cpp src/**/*.hpp src/**/*.cu

# Or format all changed files
git diff --name-only --cached | grep -E '\.(cpp|hpp|cu|cuh)$' | xargs clang-format -i
```

### 1.2 .clang-format Configuration
Create `.clang-format` in project root:
```yaml
BasedOnStyle: Google
IndentWidth: 4
ColumnLimit: 100
PointerAlignment: Left
DerivePointerAlignment: false
AlignConsecutiveAssignments: true
AlignConsecutiveDeclarations: true
AllowShortFunctionsOnASingleLine: Empty
AllowShortIfStatementsOnASingleLine: Never
```

## 2. Naming Conventions

### 2.1 General Naming Rules
- Use descriptive names that convey meaning
- Avoid abbreviations unless widely understood
- Use British English spelling (colour, behaviour, optimise, initialise)

### 2.2 File Naming
- **Header files**: `.h`, `.hpp` (prefer `.hpp` for C++)
- **Implementation files**: `.cpp`
- **CUDA files**: `.cu` (kernels and device code), `.cuh` (CUDA headers)
- **File names**: lowercase with underscores (e.g., `matrix_multiply.cpp`)

### 2.3 Variable Naming
- **Local variables**: `snake_case`
  ```cpp
  int buffer_size = 1024;
  float* device_memory = nullptr;
  ```

- **Member variables**: `snake_case_` with trailing underscore
  ```cpp
  class Buffer {
      size_t size_;
      float* data_;
  };
  ```

- **Constants**: `kPascalCase` or `UPPER_CASE`
  ```cpp
  constexpr int kMaxBufferSize = 4096;
  const float PI = 3.14159f;
  ```

### 2.4 Function Naming
- **Functions**: `camelCase` or `snake_case` (be consistent within project)
  ```cpp
  void processData();
  float calculateDotProduct();
  // OR
  void process_data();
  float calculate_dot_product();
  ```

### 2.5 Class and Type Naming
- **Classes/Structs**: `PascalCase`
  ```cpp
  class MatrixBuffer { };
  struct DeviceMemory { };
  ```

- **Type aliases**: `PascalCase` or `snake_case_t`
  ```cpp
  using BufferPtr = std::unique_ptr<Buffer>;
  using size_type = std::size_t;
  ```

### 2.6 Namespace Naming
- **Namespaces**: `snake_case` or `lowercase`
  ```cpp
  namespace cuda_utils { }
  namespace matrix_ops { }
  ```

### 2.7 Macro Naming
- **Macros**: `UPPER_CASE` with project prefix
  ```cpp
  #define PROJECT_CUDA_CHECK(call) ...
  #define PROJECT_MAX_THREADS 1024
  ```

## 3. Code Layout and Indentation

### 3.1 Indentation
- **Indent width**: 4 spaces (or 2 spaces, be consistent)
- **No tabs**: Use spaces only
- **Continuation indent**: 4 spaces

### 3.2 Line Length
- **Maximum line length**: 100 characters (or 80, be consistent)
- Break long lines at logical points
- Align continued lines for readability

### 3.3 Braces
- **Opening brace**: Same line (K&R style) or next line (Allman style)
- **Be consistent** within the project

K&R style (preferred):
```cpp
void function() {
    if (condition) {
        // code
    }
}
```

Allman style:
```cpp
void function()
{
    if (condition)
    {
        // code
    }
}
```

### 3.4 Spacing
- Space after keywords: `if (`, `for (`, `while (`
- Space around operators: `a + b`, `x = y`
- No space before semicolon: `statement;`
- Space after comma: `func(a, b, c)`

## 4. Header File Organization

### 4.1 Include Guards
Use `#pragma once` (preferred) or traditional include guards:

```cpp
// Preferred
#pragma once

// Traditional
#ifndef PROJECT_MODULE_FILENAME_H
#define PROJECT_MODULE_FILENAME_H
// ...
#endif  // PROJECT_MODULE_FILENAME_H
```

### 4.2 Include Order
Organize includes in this order:
1. Related header (for .cpp files)
2. C system headers
3. C++ standard library headers
4. Third-party library headers
5. Project headers

```cpp
#include "module.hpp"  // Related header

#include <cuda_runtime.h>  // C system headers

#include <memory>  // C++ standard library
#include <vector>

#include <Eigen/Dense>  // Third-party libraries

#include "project/utils.hpp"  // Project headers
```

### 4.3 Forward Declarations
Use forward declarations to reduce compilation dependencies:
```cpp
// In header
class Buffer;  // Forward declaration

class Processor {
    void process(const Buffer& buf);  // Use reference/pointer
};
```

## 5. Function and Method Formatting

### 5.1 Function Declarations
```cpp
// Short declaration
void shortFunction(int a, int b);

// Long declaration - break at parameters
void longFunctionName(
    const std::vector<float>& input,
    std::vector<float>& output,
    size_t size);

// Very long - align parameters
void veryLongFunctionName(
    const std::vector<float>& input_data,
    const std::vector<float>& weights,
    std::vector<float>& output_data,
    size_t input_size,
    size_t output_size);
```

### 5.2 Function Definitions
```cpp
void function(int param1, int param2) {
    // Implementation
}

// Long parameter list
void longFunction(
    const std::vector<float>& input,
    std::vector<float>& output,
    size_t size) {
    // Implementation
}
```

## 6. Class Formatting

### 6.1 Class Declaration Order
```cpp
class MyClass {
public:
    // Public types and constants
    using ValueType = float;
    static constexpr int kMaxSize = 1024;

    // Constructors and destructor
    MyClass();
    explicit MyClass(int size);
    ~MyClass();

    // Public methods
    void publicMethod();

protected:
    // Protected members
    void protectedMethod();

private:
    // Private methods
    void privateMethod();

    // Private data members
    int size_;
    float* data_;
};
```

### 6.2 Constructor Initializer Lists
```cpp
// Short initializer list
MyClass::MyClass() : size_(0), data_(nullptr) { }

// Long initializer list
MyClass::MyClass(int size, float* data)
    : size_(size),
      data_(data),
      initialized_(true),
      capacity_(size * 2) {
    // Constructor body
}
```

## 7. CUDA-Specific Formatting

### 7.1 Kernel Launch Configuration
```cpp
// Simple launch
myKernel<<<blocks, threads>>>(args);

// Complex launch with formatting
myKernel<<<
    dim3(grid_x, grid_y),
    dim3(block_x, block_y),
    shared_mem_size,
    stream
>>>(arg1, arg2, arg3);
```

### 7.2 Kernel Function Formatting
```cpp
__global__ void kernelName(
    const float* input,
    float* output,
    int size) {
    int idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx < size) {
        output[idx] = input[idx] * 2.0f;
    }
}
```

## 8. Comments and Documentation

### 8.1 Comment Style
- Use `//` for single-line comments
- Use `/* */` for multi-line comments
- Use Doxygen style `/** */` for documentation

### 8.2 Inline Comments
```cpp
// Good: Explains why, not what
int buffer_size = 1024;  // Power of 2 for alignment

// Bad: States the obvious
int x = 5;  // Set x to 5
```

### 8.3 Block Comments
```cpp
// Multi-line explanation of complex logic
// This algorithm uses a two-phase approach:
// 1. First phase processes even indices
// 2. Second phase processes odd indices
```

## 9. Whitespace and Blank Lines

### 9.1 Blank Lines
- One blank line between function definitions
- One blank line between class sections (public/private)
- Two blank lines between major sections in a file

### 9.2 Trailing Whitespace
- **Remove all trailing whitespace**
- Configure editor to remove on save

## 10. Const Correctness

### 10.1 Const Usage
- Mark variables `const` when they don't change
- Mark methods `const` when they don't modify state
- Use `const` references for read-only parameters

```cpp
class Buffer {
public:
    // Const method - doesn't modify state
    size_t size() const { return size_; }

    // Non-const method - modifies state
    void resize(size_t new_size) { size_ = new_size; }

private:
    size_t size_;
};

// Const reference parameter
void process(const std::vector<float>& data);
```

## 11. Pointer and Reference Formatting

### 11.1 Pointer/Reference Alignment
Be consistent with pointer/reference alignment:

```cpp
// Left alignment (preferred in this project)
int* ptr;
int& ref;

// Right alignment
int *ptr;
int &ref;

// Middle alignment
int * ptr;
int & ref;
```

Choose one style and use it consistently throughout the project.

## 12. Namespace Formatting

### 12.1 Namespace Declaration
```cpp
namespace project {
namespace module {

class MyClass {
    // ...
};

}  // namespace module
}  // namespace project
```

### 12.2 Using Declarations
- **Never** use `using namespace` in headers
- Avoid `using namespace std;` in implementation files
- Prefer explicit namespace qualification or specific `using` declarations

```cpp
// Bad in header
using namespace std;

// Good in implementation
using std::vector;
using std::string;

// Or use explicit qualification
std::vector<int> data;
```

## 13. Pre-Commit Formatting Requirements

### 13.1 Before Every Commit
Before EVERY commit operation, Claude Code MUST:
1. Run `clang-format` on modified files
2. Verify no formatting warnings
3. Check for trailing whitespace

### 13.2 Automated Formatting Check
```bash
# Format check (don't modify files)
clang-format --dry-run --Werror src/**/*.cpp

# Format and fix
clang-format -i src/**/*.cpp src/**/*.hpp src/**/*.cu
```

## 14. Character Encoding Requirements

### 14.1 ASCII-Only Requirement
**STRICTLY FORBIDDEN**: Use of ANY Non-ASCII characters in:
- Source code files (`.cpp`, `.hpp`, `.cu`, `.cuh`, `.h`)
- Comments (inline, block, or documentation comments)
- Any text content in the repository

This includes but is not limited to:
- Non-English characters (Chinese, Japanese, Arabic, Cyrillic, etc.)
- Special marks and symbols (checkmark, crossmark, bullet points, arrows)
- Emoji and emoticons
- Accented characters (e, a, o, etc.)
- Mathematical symbols beyond basic ASCII
- Currency symbols beyond $ (dollar sign)
- Typographic quotes (" " ' ') - use straight quotes (" ')

**Allowed**: Only ASCII characters (0x00-0x7F)

Example violations:
```cpp
// FORBIDDEN: Non-ASCII characters
// TODO: Fix this bug  (contains special dash)
int result = 42;  // checkmark emoji

// ALLOWED: ASCII only
// TODO: Fix this bug
int result = 42;  // Correct implementation
```

### 14.2 British English Requirement
**MANDATORY**: All English text MUST use British English spelling:

**Spelling differences** (British vs American):
- colour (not color)
- behaviour (not behavior)
- optimise (not optimize)
- initialise (not initialize)
- analyse (not analyze)
- centre (not center)

**Examples**:
```cpp
// CORRECT: British English
void initialiseColourBuffer() {
    // Initialise the colour buffer with default values
    // This optimises memory usage
}

// INCORRECT: American English
void initializeColorBuffer() {
    // Initialize the color buffer with default values
    // This optimizes memory usage
}
```

## 15. Enforcement

### 15.1 Automated Checks
- Configure git hooks to check formatting
- CI/CD must verify formatting compliance
- Reject commits with formatting violations

### 15.2 Code Review
- Reviewers should verify formatting compliance
- Use automated tools to catch formatting issues
- Don't waste review time on style issues - automate them
