---
name: build
description: Orchestrate build workflows for Python and C++/CUDA projects. Handles environment setup, dependency installation, compilation, and testing. Use when setting up projects or running full build cycles.
---

# Build Orchestration Skill

This skill provides intelligent build orchestration for Python and C++/CUDA projects, automating the entire build workflow from environment setup to testing.

## When to Use

Automatically triggered when:
- User asks "how do I build this project?"
- User needs to set up development environment
- User wants to run full build + test cycle
- User encounters build errors
- Setting up CI/CD pipelines

## What It Does

1. **Detects project type** (Python, C++/CUDA, or mixed)
2. **Sets up environment** (virtual env, compilers, CUDA)
3. **Installs dependencies** (Poetry, Conan, system packages)
4. **Builds project** (compilation for C++, package for Python)
5. **Runs tests** (pytest, gtest, catch2)
6. **Reports results** with actionable error messages

## Available Commands

### /build setup

Set up development environment from scratch.

```bash
/build setup
```

**What it does:**
- Detects project type
- Creates virtual environment (Python)
- Installs dependencies
- Configures build tools
- Verifies toolchain

### /build compile

Compile C++/CUDA code (no-op for Python).

```bash
/build compile
/build compile --release
/build compile --debug --verbose
```

**Options:**
- `--release`: Release build with optimizations
- `--debug`: Debug build with symbols
- `--verbose`: Show detailed compiler output
- `--clean`: Clean before building

### /build test

Run all tests.

```bash
/build test
/build test --coverage
/build test --filter test_model
```

**Options:**
- `--coverage`: Generate coverage report
- `--filter <pattern>`: Run only matching tests
- `--verbose`: Show detailed test output

### /build full

Run complete build cycle: setup + compile + test.

```bash
/build full
```

Equivalent to:
```bash
/build setup && /build compile && /build test
```

### /build clean

Clean build artifacts.

```bash
/build clean
/build clean --all  # Also remove dependencies
```

### /build doctor

Diagnose build environment issues.

```bash
/build doctor
```

**Checks:**
- Compiler versions
- Python version
- CUDA toolkit (if applicable)
- Required system libraries
- Virtual environment status
- Dependency conflicts

## How It Works

### For Python Projects

1. **Environment Setup**
   ```bash
   # Detect Python version requirement
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate

   # Install dependencies via Poetry
   poetry install
   ```

2. **Testing**
   ```bash
   # Run pytest with coverage
   pytest --cov=src tests/
   ```

### For C++/CUDA Projects

1. **Environment Setup**
   ```bash
   # Install dependencies via Conan
   conan install . --build=missing

   # Configure CMake
   cmake -B build -DCMAKE_BUILD_TYPE=Release
   ```

2. **Compilation**
   ```bash
   # Build with CMake
   cmake --build build --parallel

   # For CUDA projects, checks nvcc availability
   ```

3. **Testing**
   ```bash
   # Run tests
   cd build && ctest --output-on-failure
   ```

### For Mixed Projects (Python + C++/CUDA)

Handles both workflows in correct order:
1. Build C++/CUDA extensions
2. Set up Python environment
3. Install Python package with compiled extensions
4. Run tests for both

## Integration with Other Skills

### With /init

```
[INFO] New project detected
[SUGGESTION] Run /build setup to configure environment
```

### With /dependency

```bash
$ /dependency add torch
[OK] torch added to pyproject.toml
[SUGGESTION] Run /build setup to install
```

### With /pre-commit

```bash
$ /build full
[OK] Build successful
[INFO] Running pre-commit checks...
```

## Examples

### Example 1: Setting Up Python Project

```bash
$ /build setup

Build Orchestration: Setup
========================================

[1/5] Detecting project type...
[OK] Python project detected (pyproject.toml found)

[2/5] Checking Python version...
[OK] Python 3.10.8 (required: >=3.9)

[3/5] Creating virtual environment...
[OK] Virtual environment created at .venv/

[4/5] Installing dependencies via Poetry...
[OK] Installed 25 packages

[5/5] Verifying installation...
[OK] All dependencies installed correctly

Setup complete! Activate environment:
  source .venv/bin/activate
```

### Example 2: Building C++/CUDA Project

```bash
$ /build compile --release

Build Orchestration: Compile
========================================

[1/6] Detecting project type...
[OK] C++/CUDA project detected (CMakeLists.txt found)

[2/6] Checking toolchain...
[OK] g++ 11.4.0
[OK] nvcc 12.1
[OK] cmake 3.25.0

[3/6] Installing dependencies (Conan)...
[OK] Installed: Eigen/3.4, OpenCV/4.7

[4/6] Configuring CMake (Release)...
[OK] Build directory: build/

[5/6] Compiling...
[OK] Compiled 45 source files
[OK] Linked 3 targets

[6/6] Build artifacts...
[OK] build/bin/main_app
[OK] build/lib/libcore.so

Build complete! Run tests:
  /build test
```

### Example 3: Full Build Cycle

```bash
$ /build full

Build Orchestration: Full Cycle
========================================

Phase 1: Setup
----------------------------------------
[OK] Environment configured

Phase 2: Compile
----------------------------------------
[OK] Build successful (2m 34s)

Phase 3: Test
----------------------------------------
Running tests...
test_data.py::test_loader PASSED
test_model.py::test_forward PASSED
test_training.py::test_epoch PASSED

[OK] 45 tests passed, 0 failed

Coverage Report:
----------------------------------------
src/data.py         95%
src/model.py        88%
src/training.py     92%
----------------------------------------
Total coverage:     91%

Build cycle complete!
```

### Example 4: Diagnosing Issues

```bash
$ /build doctor

Build Environment Diagnostics
========================================

Python Environment:
----------------------------------------
[OK] Python 3.10.8 (required: >=3.9)
[OK] Virtual environment: .venv/
[OK] Poetry 1.5.1

C++ Toolchain:
----------------------------------------
[OK] g++ 11.4.0
[OK] cmake 3.25.0
[WARN] clang-format not found (optional)

CUDA Toolkit:
----------------------------------------
[OK] nvcc 12.1
[OK] CUDA runtime 12.1
[WARN] cuDNN not found (optional for some projects)

Dependencies:
----------------------------------------
[OK] All Python dependencies installed
[OK] All Conan dependencies installed

Potential Issues:
----------------------------------------
None detected

Environment is healthy!
```

## Advanced Features

### Parallel Builds

```bash
# Use all CPU cores
/build compile --parallel

# Specify core count
/build compile --parallel 8
```

### Custom Build Targets

```bash
# Build specific target
/build compile --target main_app

# Build multiple targets
/build compile --target "main_app;tests"
```

### Cross-Compilation

```bash
# Cross-compile for different architecture
/build compile --arch arm64
```

### Incremental Builds

```bash
# Only rebuild changed files (default)
/build compile

# Force full rebuild
/build compile --clean
```

## Troubleshooting

### "Compiler not found"

Install required compiler:
```bash
# Ubuntu/Debian
sudo apt install build-essential

# macOS
xcode-select --install

# For CUDA
# Download from: https://developer.nvidia.com/cuda-downloads
```

### "Dependency installation failed"

1. Check internet connection
2. Verify package names in manifest
3. Try manual installation:
   ```bash
   poetry install --verbose
   conan install . --build=missing
   ```

### "Tests failing"

1. Check if build succeeded: `/build compile`
2. Run specific test: `/build test --filter test_name --verbose`
3. Check test logs in build/Testing/

### "CUDA not found"

1. Verify CUDA installation: `nvcc --version`
2. Set CUDA_HOME: `export CUDA_HOME=/usr/local/cuda`
3. Add to PATH: `export PATH=$CUDA_HOME/bin:$PATH`

## Best Practices

1. **Always run /build setup first** in new projects
2. **Use /build doctor** when encountering issues
3. **Run /build test** before committing
4. **Use --verbose** for debugging build failures
5. **Keep dependencies updated** regularly

## CI/CD Integration

The build skill can be used in CI/CD pipelines:

```yaml
# .github/workflows/build.yml
- name: Build and Test
  run: |
    python3 .claude/skills/build/scripts/full.py
```

Exit codes:
- 0: Success
- 1: Build failed
- 2: Tests failed
- 3: Environment setup failed

## Limitations

- Requires build tools to be installed
- Cannot install system packages (requires sudo)
- Cross-compilation support is basic
- Some complex build systems may need manual configuration

## Version History

- **1.0.0** (2026-03-06): Initial release
  - Python project support (Poetry)
  - C++/CUDA project support (CMake + Conan)
  - Mixed project support
  - Environment diagnostics
  - Parallel builds
  - Test orchestration
