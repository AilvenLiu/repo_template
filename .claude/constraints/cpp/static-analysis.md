# C++/CUDA Static Analysis Requirements

> **This document defines mandatory static analysis standards for C++/CUDA projects.**
> All code must pass static analysis checks before committing.

## 1. Static Analysis Tools

### 1.1 Mandatory Tools
- **clang-tidy**: Primary static analysis tool
- **cppcheck**: Additional static analysis
- **CUDA**: Use `cuda-memcheck` for memory errors

### 1.2 Tool Purpose
- **clang-tidy**: Detects bugs, performance issues, style violations
- **cppcheck**: Catches additional issues clang-tidy might miss
- **cuda-memcheck**: Detects CUDA-specific memory errors

## 2. clang-tidy Configuration

### 2.1 .clang-tidy File
Create `.clang-tidy` in project root:
```yaml
Checks: >
  -*,
  bugprone-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*,
  -modernize-use-trailing-return-type,
  -readability-identifier-length

WarningsAsErrors: '*'
HeaderFilterRegex: '.*'
FormatStyle: file
```

### 2.2 Check Categories

#### 2.2.1 bugprone-* Checks
Detects common programming errors:
- `bugprone-use-after-move`: Detects use after std::move
- `bugprone-dangling-handle`: Detects dangling references
- `bugprone-infinite-loop`: Detects infinite loops
- `bugprone-integer-division`: Detects unintended integer division

#### 2.2.2 cppcoreguidelines-* Checks
Enforces C++ Core Guidelines:
- `cppcoreguidelines-avoid-goto`: Avoid goto statements
- `cppcoreguidelines-no-malloc`: Prefer new/delete or smart pointers
- `cppcoreguidelines-owning-memory`: Enforce ownership semantics
- `cppcoreguidelines-pro-type-const-cast`: Avoid const_cast

#### 2.2.3 modernize-* Checks
Encourages modern C++ practices:
- `modernize-use-auto`: Use auto where appropriate
- `modernize-use-nullptr`: Use nullptr instead of NULL
- `modernize-use-override`: Use override keyword
- `modernize-make-unique`: Use std::make_unique
- `modernize-make-shared`: Use std::make_shared

#### 2.2.4 performance-* Checks
Detects performance issues:
- `performance-unnecessary-copy-initialization`: Avoid unnecessary copies
- `performance-for-range-copy`: Use const reference in range-for
- `performance-move-const-arg`: Don't move const arguments
- `performance-inefficient-vector-operation`: Optimise vector operations

#### 2.2.5 readability-* Checks
Improves code readability:
- `readability-const-return-type`: Avoid const return types
- `readability-container-size-empty`: Use empty() instead of size() == 0
- `readability-redundant-string-cstr`: Avoid redundant c_str() calls
- `readability-simplify-boolean-expr`: Simplify boolean expressions

### 2.3 Disabled Checks
Some checks are disabled for practical reasons:
- `modernize-use-trailing-return-type`: Not required for all functions
- `readability-identifier-length`: Allow short variable names in appropriate contexts

## 3. Running clang-tidy

### 3.1 Command Line Usage
```bash
# Run on specific files
clang-tidy src/module.cpp -p build/

# Run on all source files
clang-tidy src/**/*.cpp src/**/*.cu -p build/

# Run with fixes
clang-tidy src/module.cpp -p build/ --fix

# Run with specific checks
clang-tidy src/module.cpp -p build/ --checks='bugprone-*,modernize-*'
```

### 3.2 Integration with Build System
```cmake
# CMakeLists.txt
option(ENABLE_CLANG_TIDY "Enable clang-tidy checks" ON)

if(ENABLE_CLANG_TIDY)
    find_program(CLANG_TIDY_EXE NAMES clang-tidy)
    if(CLANG_TIDY_EXE)
        set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY_EXE})
    endif()
endif()
```

### 3.3 Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Get list of changed C++ files
FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(cpp|hpp|cu|cuh)$')

if [ -n "$FILES" ]; then
    echo "Running clang-tidy on changed files..."
    clang-tidy $FILES -p build/
    if [ $? -ne 0 ]; then
        echo "clang-tidy found issues. Please fix before committing."
        exit 1
    fi
fi
```

## 4. cppcheck Configuration

### 4.1 Running cppcheck
```bash
# Basic check
cppcheck src/

# Enable all checks
cppcheck --enable=all --suppress=missingIncludeSystem src/

# With specific checks
cppcheck --enable=warning,performance,portability src/

# Generate XML report
cppcheck --enable=all --xml --xml-version=2 src/ 2> cppcheck-report.xml
```

### 4.2 cppcheck Suppressions
Create `.cppcheck-suppressions` file:
```
missingIncludeSystem
unusedFunction:tests/*
```

Usage:
```bash
cppcheck --enable=all --suppressions-list=.cppcheck-suppressions src/
```

### 4.3 cppcheck Categories
- **error**: Errors that should be fixed
- **warning**: Potential issues
- **style**: Style issues
- **performance**: Performance issues
- **portability**: Portability issues
- **information**: Informational messages

## 5. CUDA Static Analysis

### 5.1 cuda-memcheck
```bash
# Check for memory errors
cuda-memcheck ./build/cuda_app

# Check for race conditions
cuda-memcheck --tool racecheck ./build/cuda_app

# Check for shared memory errors
cuda-memcheck --tool synccheck ./build/cuda_app

# Check for initialisation errors
cuda-memcheck --tool initcheck ./build/cuda_app
```

### 5.2 CUDA Compiler Warnings
```cmake
# Enable CUDA warnings
target_compile_options(mylib PRIVATE
    $<$<COMPILE_LANGUAGE:CUDA>:
        -Xcompiler=-Wall,-Wextra
        --ptxas-options=-v
    >
)
```

### 5.3 CUDA Static Analysis Tools
- **cuda-memcheck**: Runtime memory checker
- **compute-sanitizer**: Modern replacement for cuda-memcheck
- **Nsight Compute**: Profiling and analysis

## 6. Common Issues Detected

### 6.1 Memory Issues
```cpp
// Bad: Memory leak
void leak() {
    int* ptr = new int(42);
    // clang-tidy: bugprone-unused-raii
}

// Good: Use smart pointer
void noLeak() {
    auto ptr = std::make_unique<int>(42);
    // clang-tidy: OK
}
```

### 6.2 Use After Move
```cpp
// Bad: Use after move
std::vector<int> vec{1, 2, 3};
auto vec2 = std::move(vec);
vec.push_back(4);  // clang-tidy: bugprone-use-after-move

// Good: Don't use after move
std::vector<int> vec{1, 2, 3};
auto vec2 = std::move(vec);
// Don't use vec anymore
```

### 6.3 Unnecessary Copies
```cpp
// Bad: Unnecessary copy
for (auto item : container) {  // clang-tidy: performance-for-range-copy
    process(item);
}

// Good: Use const reference
for (const auto& item : container) {
    process(item);
}
```

### 6.4 Null Pointer Dereference
```cpp
// Bad: Potential null dereference
int* ptr = getPointer();
*ptr = 42;  // clang-tidy: bugprone-null-dereference

// Good: Check for null
int* ptr = getPointer();
if (ptr) {
    *ptr = 42;
}
```

### 6.5 Integer Division
```cpp
// Bad: Unintended integer division
float result = 1 / 2;  // clang-tidy: bugprone-integer-division

// Good: Use floating-point literals
float result = 1.0f / 2.0f;
```

## 7. Pre-Commit Static Analysis Requirements

### 7.1 Before Every Commit
**MANDATORY**: Run static analysis before committing:
1. Run `clang-tidy` on modified files
2. Run `cppcheck` on modified files
3. Ensure all tests pass
4. Verify no compiler warnings

### 7.2 Static Analysis Script
```bash
#!/bin/bash
# run-static-analysis.sh

echo "Running clang-tidy..."
clang-tidy src/**/*.cpp src/**/*.cu -p build/
if [ $? -ne 0 ]; then
    echo "clang-tidy found issues"
    exit 1
fi

echo "Running cppcheck..."
cppcheck --enable=all --suppress=missingIncludeSystem src/
if [ $? -ne 0 ]; then
    echo "cppcheck found issues"
    exit 1
fi

echo "Static analysis passed"
```

## 8. CI/CD Integration

### 8.1 GitHub Actions Example
```yaml
name: Static Analysis

on: [push, pull_request]

jobs:
  static-analysis:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Install tools
      run: |
        sudo apt-get update
        sudo apt-get install -y clang-tidy cppcheck

    - name: Configure
      run: cmake -B build

    - name: Run clang-tidy
      run: |
        clang-tidy src/**/*.cpp -p build/

    - name: Run cppcheck
      run: |
        cppcheck --enable=all --suppress=missingIncludeSystem \
                 --error-exitcode=1 src/
```

### 8.2 GitLab CI Example
```yaml
static-analysis:
  stage: test
  script:
    - apt-get update && apt-get install -y clang-tidy cppcheck
    - cmake -B build
    - clang-tidy src/**/*.cpp -p build/
    - cppcheck --enable=all --suppress=missingIncludeSystem --error-exitcode=1 src/
```

## 9. Suppressing False Positives

### 9.1 Inline Suppressions
```cpp
// Suppress specific warning
// NOLINTNEXTLINE(bugprone-suspicious-semicolon)
if (condition);
    doSomething();

// Suppress multiple warnings
// NOLINTNEXTLINE(bugprone-*, performance-*)
complexCode();

// Suppress for entire function
// NOLINTBEGIN(modernize-use-auto)
void legacyFunction() {
    int* ptr = new int(42);
    delete ptr;
}
// NOLINTEND(modernize-use-auto)
```

### 9.2 Configuration-Based Suppressions
```yaml
# .clang-tidy
CheckOptions:
  - key: readability-identifier-naming.VariableCase
    value: lower_case
  - key: readability-identifier-naming.FunctionCase
    value: camelBack
```

## 10. Static Analysis Best Practices

### 10.1 Fix Issues, Don't Suppress
- Fix issues rather than suppressing warnings
- Only suppress false positives
- Document why suppressions are necessary

### 10.2 Regular Updates
- Keep clang-tidy and cppcheck up to date
- Review and update .clang-tidy configuration
- Add new checks as they become available

### 10.3 Team Consistency
- Use same .clang-tidy configuration across team
- Enforce static analysis in CI/CD
- Make static analysis part of code review

## 11. Advanced clang-tidy Features

### 11.1 Custom Checks
```yaml
# .clang-tidy
Checks: >
  -*,
  bugprone-*,
  cppcoreguidelines-*,
  modernize-*,
  performance-*,
  readability-*,
  project-*  # Custom project-specific checks

CheckOptions:
  - key: project-naming-convention.VariablePrefix
    value: m_
```

### 11.2 Check-Specific Options
```yaml
CheckOptions:
  - key: modernize-use-nullptr.NullMacros
    value: 'NULL'
  - key: performance-unnecessary-value-param.AllowedTypes
    value: 'std::shared_ptr;std::unique_ptr'
  - key: readability-identifier-naming.ClassCase
    value: CamelCase
```

## 12. Troubleshooting

### 12.1 Compilation Database
clang-tidy requires a compilation database (`compile_commands.json`):
```bash
# Generate with CMake
cmake -B build -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# Symlink to root
ln -s build/compile_commands.json .
```

### 12.2 Header Filter
```yaml
# .clang-tidy
HeaderFilterRegex: '.*'  # Check all headers
# Or specific pattern
HeaderFilterRegex: 'include/myproject/.*'
```

### 12.3 Performance
```bash
# Run in parallel
run-clang-tidy -j$(nproc) src/

# Check specific files only
clang-tidy $(git diff --name-only --cached | grep -E '\.(cpp|hpp)$') -p build/
```

## 13. Code Review Checklist

### 13.1 Static Analysis Review
- [ ] clang-tidy passes with project configuration
- [ ] cppcheck shows no issues
- [ ] No compiler warnings
- [ ] CUDA code checked with cuda-memcheck
- [ ] All suppressions are justified and documented
- [ ] Static analysis integrated in CI/CD

## 14. Enforcement

### 14.1 Mandatory Checks
- All code must pass clang-tidy
- All code must pass cppcheck
- No warnings allowed in production code
- CI/CD must enforce static analysis

### 14.2 Violation Handling
- PRs with static analysis failures cannot be merged
- Suppressions require justification in code review
- Regular audits of suppressed warnings

## 15. Tool Versions

### 15.1 Recommended Versions
- **clang-tidy**: 14.0 or later
- **cppcheck**: 2.7 or later
- **cuda-memcheck**: Included with CUDA Toolkit 11.0+

### 15.2 Version Compatibility
Document tool versions in README.md:
```markdown
## Static Analysis Tools

- clang-tidy 14.0+
- cppcheck 2.7+
- cuda-memcheck (CUDA Toolkit 11.0+)
```

## 16. Forbidden Practices

**STRICTLY FORBIDDEN**:
- Committing code with static analysis warnings
- Suppressing warnings without justification
- Disabling static analysis checks globally
- Ignoring static analysis in code review
- Not running static analysis before committing
