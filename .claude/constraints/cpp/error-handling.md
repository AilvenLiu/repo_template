# C++ Error Handling and Exceptions

> **This document defines mandatory error handling standards for C++/CUDA projects.**
> All code must follow these exception handling practices for robustness and maintainability.

## 1. Exception Handling Best Practices

### 1.1 Core Principles
- **RAII**: Use Resource Acquisition Is Initialisation for automatic cleanup
- **Specific Exceptions**: Catch specific exception types, not `catch(...)`
- **Custom Exceptions**: Define custom exception classes for domain-specific errors
- **noexcept**: Mark functions that don't throw with `noexcept`
- **Strong Exception Safety**: Ensure operations are atomic or leave state unchanged
- **Logging**: Log exceptions with context before re-throwing

### 1.2 Never Use Catch-All Without Re-throwing
```cpp
// Bad: Catch-all that swallows exceptions
try {
    risky_operation();
} catch (...) {  // FORBIDDEN without re-throw
    // Silent failure
}

// Good: Catch specific exceptions
try {
    risky_operation();
} catch (const std::invalid_argument& e) {
    std::cerr << "Invalid argument: " << e.what() << std::endl;
    throw;
} catch (const std::runtime_error& e) {
    std::cerr << "Runtime error: " << e.what() << std::endl;
    throw;
}

// Acceptable: Catch-all with re-throw for logging
try {
    risky_operation();
} catch (...) {
    std::cerr << "Unknown exception caught" << std::endl;
    throw;  // MUST re-throw
}
```

## 2. Specific Exception Handling

### 2.1 Catch Specific Exception Types
```cpp
// Good: Specific exception handling
#include <fstream>
#include <stdexcept>
#include <string>

std::string read_config(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Failed to open config file: " + path);
    }
    
    std::string content;
    try {
        std::getline(file, content, '\0');
        return content;
    } catch (const std::ios_base::failure& e) {
        throw std::runtime_error("Failed to read config file: " + std::string(e.what()));
    }
}

// Good: Multiple specific exceptions
class DataProcessor {
public:
    void process(const std::string& data) {
        try {
            validate(data);
            parse(data);
            store(data);
        } catch (const std::invalid_argument& e) {
            std::cerr << "Validation error: " << e.what() << std::endl;
            throw;
        } catch (const std::runtime_error& e) {
            std::cerr << "Processing error: " << e.what() << std::endl;
            throw;
        } catch (const std::bad_alloc& e) {
            std::cerr << "Memory allocation failed: " << e.what() << std::endl;
            throw;
        }
    }
};
```

### 2.2 Exception Safety Guarantees
```cpp
// Good: Strong exception safety with RAII
class ResourceManager {
private:
    std::unique_ptr<Resource> resource_;
    
public:
    void update(const Data& new_data) {
        // Create new resource first (may throw)
        auto new_resource = std::make_unique<Resource>(new_data);
        
        // Only update if creation succeeded (no-throw)
        resource_ = std::move(new_resource);
    }
};

// Good: Basic exception safety with proper cleanup
void process_file(const std::string& path) {
    std::ifstream file(path);
    if (!file.is_open()) {
        throw std::runtime_error("Cannot open file");
    }
    
    // RAII ensures file is closed even if exception thrown
    std::string line;
    while (std::getline(file, line)) {
        process_line(line);  // May throw
    }
    // file automatically closed by destructor
}
```

## 3. Custom Exception Classes

### 3.1 Define Custom Exception Hierarchy
```cpp
// Good: Custom exception hierarchy
class ApplicationError : public std::runtime_error {
public:
    explicit ApplicationError(const std::string& message)
        : std::runtime_error(message) {}
};

class DataValidationError : public ApplicationError {
public:
    explicit DataValidationError(const std::string& message)
        : ApplicationError("Data validation failed: " + message) {}
};

class ConfigurationError : public ApplicationError {
public:
    explicit ConfigurationError(const std::string& message)
        : ApplicationError("Configuration error: " + message) {}
};

class DatabaseError : public ApplicationError {
private:
    int error_code_;
    
public:
    DatabaseError(const std::string& message, int code)
        : ApplicationError(message), error_code_(code) {}
    
    int error_code() const noexcept { return error_code_; }
};
```

### 3.2 Exception Class Best Practices
```cpp
// Good: Exception with context
class FileOperationError : public std::runtime_error {
private:
    std::string file_path_;
    std::string operation_;
    
public:
    FileOperationError(const std::string& path, 
                      const std::string& operation,
                      const std::string& reason)
        : std::runtime_error(format_message(path, operation, reason)),
          file_path_(path),
          operation_(operation) {}
    
    const std::string& file_path() const noexcept { return file_path_; }
    const std::string& operation() const noexcept { return operation_; }
    
private:
    static std::string format_message(const std::string& path,
                                     const std::string& operation,
                                     const std::string& reason) {
        return "File operation '" + operation + "' failed for '" + 
               path + "': " + reason;
    }
};
```

## 4. RAII and Exception Safety

### 4.1 Use RAII for Resource Management
```cpp
// Good: RAII ensures cleanup on exception
class FileHandler {
private:
    FILE* file_;
    
public:
    explicit FileHandler(const char* path, const char* mode) {
        file_ = fopen(path, mode);
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }
    
    ~FileHandler() {
        if (file_) {
            fclose(file_);
        }
    }
    
    // Delete copy operations
    FileHandler(const FileHandler&) = delete;
    FileHandler& operator=(const FileHandler&) = delete;
    
    // Allow move operations
    FileHandler(FileHandler&& other) noexcept : file_(other.file_) {
        other.file_ = nullptr;
    }
    
    FILE* get() const noexcept { return file_; }
};

// Usage: Automatic cleanup even if exception thrown
void process_file(const char* path) {
    FileHandler file(path, "r");  // RAII
    // Process file...
    // File automatically closed even if exception thrown
}
```

### 4.2 Smart Pointers for Exception Safety
```cpp
// Good: Smart pointers provide automatic cleanup
class DataProcessor {
private:
    std::unique_ptr<Database> db_;
    std::unique_ptr<Cache> cache_;
    
public:
    DataProcessor() {
        // If cache construction throws, db_ is automatically cleaned up
        db_ = std::make_unique<Database>();
        cache_ = std::make_unique<Cache>();
    }
    
    void process(const Data& data) {
        auto temp = std::make_unique<ProcessedData>(data);
        // If processing throws, temp is automatically cleaned up
        temp->validate();
        temp->transform();
        store(std::move(temp));
    }
};
```

## 5. noexcept Specification

### 5.1 Mark Non-Throwing Functions
```cpp
// Good: noexcept for functions that don't throw
class Container {
private:
    int* data_;
    size_t size_;
    
public:
    // Destructors should be noexcept (implicit)
    ~Container() noexcept {
        delete[] data_;
    }
    
    // Move operations should be noexcept
    Container(Container&& other) noexcept
        : data_(other.data_), size_(other.size_) {
        other.data_ = nullptr;
        other.size_ = 0;
    }
    
    Container& operator=(Container&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            data_ = other.data_;
            size_ = other.size_;
            other.data_ = nullptr;
            other.size_ = 0;
        }
        return *this;
    }
    
    // Getters are typically noexcept
    size_t size() const noexcept { return size_; }
    bool empty() const noexcept { return size_ == 0; }
    
    // Swap should be noexcept
    void swap(Container& other) noexcept {
        std::swap(data_, other.data_);
        std::swap(size_, other.size_);
    }
};
```

### 5.2 Conditional noexcept
```cpp
// Good: Conditional noexcept based on template parameter
template<typename T>
class Wrapper {
private:
    T value_;
    
public:
    // noexcept if T's move constructor is noexcept
    Wrapper(Wrapper&& other) noexcept(std::is_nothrow_move_constructible<T>::value)
        : value_(std::move(other.value_)) {}
    
    // noexcept if T's swap is noexcept
    void swap(Wrapper& other) noexcept(noexcept(std::swap(value_, other.value_))) {
        std::swap(value_, other.value_);
    }
};
```

## 6. CUDA Error Handling

### 6.1 CUDA API Error Checking
```cpp
// Good: Macro for CUDA error checking
#define CUDA_CHECK(call) \
    do { \
        cudaError_t error = call; \
        if (error != cudaSuccess) { \
            throw std::runtime_error( \
                std::string("CUDA error at ") + __FILE__ + ":" + \
                std::to_string(__LINE__) + " - " + \
                cudaGetErrorString(error)); \
        } \
    } while(0)

// Usage
void allocate_device_memory(void** ptr, size_t size) {
    CUDA_CHECK(cudaMalloc(ptr, size));
}

void copy_to_device(void* dst, const void* src, size_t size) {
    CUDA_CHECK(cudaMemcpy(dst, src, size, cudaMemcpyHostToDevice));
}
```

### 6.2 CUDA Kernel Error Checking
```cpp
// Good: Check for kernel launch errors
void launch_kernel(const float* input, float* output, size_t n) {
    dim3 block(256);
    dim3 grid((n + block.x - 1) / block.x);
    
    // Launch kernel
    my_kernel<<<grid, block>>>(input, output, n);
    
    // Check for launch errors
    CUDA_CHECK(cudaGetLastError());
    
    // Wait for kernel to complete and check for execution errors
    CUDA_CHECK(cudaDeviceSynchronize());
}
```

### 6.3 CUDA RAII Wrapper
```cpp
// Good: RAII wrapper for CUDA memory
template<typename T>
class CudaMemory {
private:
    T* device_ptr_;
    size_t size_;
    
public:
    explicit CudaMemory(size_t count) : size_(count * sizeof(T)) {
        CUDA_CHECK(cudaMalloc(&device_ptr_, size_));
    }
    
    ~CudaMemory() {
        if (device_ptr_) {
            cudaFree(device_ptr_);  // Don't throw in destructor
        }
    }
    
    // Delete copy operations
    CudaMemory(const CudaMemory&) = delete;
    CudaMemory& operator=(const CudaMemory&) = delete;
    
    // Allow move operations
    CudaMemory(CudaMemory&& other) noexcept
        : device_ptr_(other.device_ptr_), size_(other.size_) {
        other.device_ptr_ = nullptr;
        other.size_ = 0;
    }
    
    T* get() const noexcept { return device_ptr_; }
    size_t size() const noexcept { return size_; }
    
    void copy_from_host(const T* host_ptr) {
        CUDA_CHECK(cudaMemcpy(device_ptr_, host_ptr, size_, 
                             cudaMemcpyHostToDevice));
    }
    
    void copy_to_host(T* host_ptr) const {
        CUDA_CHECK(cudaMemcpy(host_ptr, device_ptr_, size_, 
                             cudaMemcpyDeviceToHost));
    }
};
```

## 7. Error Handling Patterns

### 7.1 Constructor Error Handling
```cpp
// Good: Constructor with proper error handling
class DatabaseConnection {
private:
    void* connection_;
    bool connected_;
    
public:
    explicit DatabaseConnection(const std::string& connection_string) 
        : connection_(nullptr), connected_(false) {
        connection_ = create_connection(connection_string.c_str());
        if (!connection_) {
            throw DatabaseError("Failed to create connection", 0);
        }
        
        try {
            if (!connect(connection_)) {
                throw DatabaseError("Failed to connect to database", 0);
            }
            connected_ = true;
        } catch (...) {
            // Clean up on failure
            destroy_connection(connection_);
            throw;
        }
    }
    
    ~DatabaseConnection() {
        if (connected_) {
            disconnect(connection_);
        }
        if (connection_) {
            destroy_connection(connection_);
        }
    }
};
```

### 7.2 Two-Phase Initialisation
```cpp
// Good: Two-phase initialisation for complex objects
class ComplexObject {
private:
    bool initialised_;
    std::unique_ptr<Resource> resource_;
    
public:
    ComplexObject() : initialised_(false) {}
    
    void initialise(const Config& config) {
        if (initialised_) {
            throw std::logic_error("Already initialised");
        }
        
        resource_ = std::make_unique<Resource>(config);
        resource_->setup();
        initialised_ = true;
    }
    
    void process() {
        if (!initialised_) {
            throw std::logic_error("Not initialised");
        }
        resource_->process();
    }
};
```

## 8. Exception Safety Levels

### 8.1 No-Throw Guarantee
```cpp
// Functions that must not throw
class Container {
public:
    // Destructors must not throw
    ~Container() noexcept {
        // Cleanup code that doesn't throw
    }
    
    // Move operations should not throw
    Container(Container&& other) noexcept {
        // Move implementation
    }
    
    // Swap should not throw
    void swap(Container& other) noexcept {
        // Swap implementation
    }
};
```

### 8.2 Strong Exception Safety
```cpp
// Good: Strong exception safety - operation succeeds or has no effect
class DataStore {
private:
    std::vector<Data> data_;
    
public:
    void add(const Data& item) {
        // Create copy first (may throw)
        std::vector<Data> new_data = data_;
        new_data.push_back(item);  // May throw
        
        // Only update if successful (no-throw)
        data_ = std::move(new_data);
    }
    
    void update(size_t index, const Data& item) {
        if (index >= data_.size()) {
            throw std::out_of_range("Index out of range");
        }
        
        // Create copy first
        Data old_data = data_[index];
        
        try {
            data_[index] = item;  // May throw
        } catch (...) {
            // Restore old value on failure
            data_[index] = old_data;
            throw;
        }
    }
};
```

### 8.3 Basic Exception Safety
```cpp
// Good: Basic exception safety - no resource leaks
class FileProcessor {
public:
    void process(const std::string& path) {
        std::ifstream file(path);  // RAII
        if (!file.is_open()) {
            throw std::runtime_error("Cannot open file");
        }
        
        std::string line;
        while (std::getline(file, line)) {
            process_line(line);  // May throw, but file is cleaned up
        }
        // file automatically closed
    }
};
```

## 9. Logging and Error Reporting

### 9.1 Log Before Re-throwing
```cpp
// Good: Log exceptions with context
#include <iostream>
#include <sstream>

void process_request(const Request& request) {
    try {
        validate_request(request);
        execute_request(request);
    } catch (const ValidationError& e) {
        std::cerr << "Validation failed for request " 
                  << request.id() << ": " << e.what() << std::endl;
        throw;
    } catch (const ExecutionError& e) {
        std::cerr << "Execution failed for request " 
                  << request.id() << ": " << e.what() << std::endl;
        throw;
    } catch (const std::exception& e) {
        std::cerr << "Unexpected error processing request " 
                  << request.id() << ": " << e.what() << std::endl;
        throw;
    }
}
```

### 9.2 Error Context Accumulation
```cpp
// Good: Accumulate error context through call stack
class ContextualError : public std::runtime_error {
private:
    std::vector<std::string> context_;
    
public:
    explicit ContextualError(const std::string& message)
        : std::runtime_error(message) {}
    
    void add_context(const std::string& context) {
        context_.push_back(context);
    }
    
    std::string full_message() const {
        std::ostringstream oss;
        oss << what();
        for (const auto& ctx : context_) {
            oss << "\n  at " << ctx;
        }
        return oss.str();
    }
};

void high_level_function() {
    try {
        mid_level_function();
    } catch (ContextualError& e) {
        e.add_context("high_level_function");
        throw;
    }
}
```

## 10. Enforcement and Best Practices

### 10.1 Violations
**STRICTLY FORBIDDEN**:
- Using bare `catch(...)` without re-throwing
- Throwing exceptions from destructors
- Throwing exceptions from `noexcept` functions
- Swallowing exceptions without logging
- Using exceptions for control flow
- Throwing non-exception types (e.g., `throw 42;`)
- Ignoring CUDA API errors
- Memory leaks on exception paths

### 10.2 Required Practices
**STRICTLY REQUIRED**:
- Use RAII for all resource management
- Check all CUDA API calls for errors
- Mark non-throwing functions with `noexcept`
- Provide strong exception safety where possible
- Log exceptions before re-throwing
- Use custom exception classes for domain errors
- Document exception specifications in comments
- Test exception paths thoroughly

## 11. Pre-Commit Checklist

Before committing, verify:
- [ ] All resources managed with RAII
- [ ] All CUDA API calls checked for errors
- [ ] No bare `catch(...)` without re-throw
- [ ] Destructors are `noexcept` (implicit or explicit)
- [ ] Move operations are `noexcept` where possible
- [ ] Custom exceptions inherit from `std::exception`
- [ ] Exception messages are descriptive
- [ ] Exceptions logged before re-throwing
- [ ] No exceptions thrown from destructors
- [ ] Exception paths tested
- [ ] British English spelling used
- [ ] ASCII-only characters used

## 12. Code Review Checklist

During code review, check for:
- [ ] Proper RAII usage
- [ ] CUDA error checking
- [ ] Appropriate exception types
- [ ] Exception safety guarantees
- [ ] No resource leaks on exception paths
- [ ] Proper `noexcept` specifications
- [ ] Meaningful error messages
- [ ] Exception logging
- [ ] Test coverage for exception paths
