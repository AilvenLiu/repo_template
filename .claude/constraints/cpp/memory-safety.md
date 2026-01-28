# C++/CUDA Memory Safety Requirements

> **This document defines mandatory memory safety standards for C++/CUDA projects.**
> All code must follow these principles to prevent memory leaks, undefined behaviour, and resource management issues.

## 1. RAII Principle (Resource Acquisition Is Initialisation)

### 1.1 RAII Definition
**RAII Principle**: All resources MUST be managed via RAII
- Resources are acquired in constructors
- Resources are released in destructors
- No manual resource management in application code

### 1.2 RAII Benefits
- Automatic resource cleanup
- Exception safety
- No memory leaks
- Clear ownership semantics
- Deterministic resource lifetime

### 1.3 RAII Example
```cpp
class FileHandle {
    FILE* file_;
public:
    explicit FileHandle(const char* filename)
        : file_(fopen(filename, "r")) {
        if (!file_) {
            throw std::runtime_error("Failed to open file");
        }
    }

    ~FileHandle() {
        if (file_) {
            fclose(file_);
        }
    }

    // Delete copy, implement move
    FileHandle(const FileHandle&) = delete;
    FileHandle& operator=(const FileHandle&) = delete;

    FileHandle(FileHandle&& other) noexcept
        : file_(other.file_) {
        other.file_ = nullptr;
    }

    FileHandle& operator=(FileHandle&& other) noexcept {
        if (this != &other) {
            if (file_) fclose(file_);
            file_ = other.file_;
            other.file_ = nullptr;
        }
        return *this;
    }

    FILE* get() { return file_; }
};
```

## 2. Smart Pointers

### 2.1 Smart Pointer Guidelines
- Use `std::unique_ptr` for exclusive ownership
- Use `std::shared_ptr` only when shared ownership is necessary
- Use `std::weak_ptr` to break circular references
- Avoid raw `new`/`delete` in application code

### 2.2 std::unique_ptr
**Use for exclusive ownership**:
```cpp
// Good: Clear ownership
std::unique_ptr<Resource> createResource() {
    return std::make_unique<Resource>(args);
}

void processResource(const Resource& res) {
    // Non-owning access via reference
}

void takeOwnership(std::unique_ptr<Resource> res) {
    // Takes ownership, will delete when out of scope
}

// Usage
auto resource = createResource();
processResource(*resource);
takeOwnership(std::move(resource));  // Transfer ownership
```

### 2.3 std::shared_ptr
**Use only when shared ownership is necessary**:
```cpp
// Shared ownership scenario
class Cache {
    std::map<std::string, std::shared_ptr<Data>> cache_;
public:
    std::shared_ptr<Data> get(const std::string& key) {
        return cache_[key];  // Multiple owners
    }

    void put(const std::string& key, std::shared_ptr<Data> data) {
        cache_[key] = data;
    }
};

// Usage
auto data = std::make_shared<Data>(args);
cache.put("key", data);
auto retrieved = cache.get("key");  // Shared ownership
```

### 2.4 std::weak_ptr
**Use to break circular references**:
```cpp
class Node {
    std::shared_ptr<Node> next_;      // Strong reference
    std::weak_ptr<Node> prev_;        // Weak reference (breaks cycle)
public:
    void setNext(std::shared_ptr<Node> next) {
        next_ = next;
        if (next) {
            next->prev_ = shared_from_this();
        }
    }

    std::shared_ptr<Node> getPrev() {
        return prev_.lock();  // Convert weak to shared
    }
};
```

### 2.5 Avoiding Raw new/delete
```cpp
// Bad: Manual memory management
Resource* res = new Resource();
// ... use res ...
delete res;  // Easy to forget, exception-unsafe

// Good: Automatic memory management
auto res = std::make_unique<Resource>();
// ... use res ...
// Automatically deleted when out of scope
```

## 3. Ownership Semantics

### 3.1 Clear Ownership Documentation
**Document ownership explicitly in function signatures and comments**:

```cpp
// Good: Clear ownership semantics
std::unique_ptr<Resource> createResource();  // Caller owns
void processResource(const Resource& res);   // Non-owning
void takeOwnership(std::unique_ptr<Resource> res);  // Transfer ownership

// Bad: Unclear ownership
Resource* createResource();  // Who owns this?
void processResource(Resource* res);  // Does this take ownership?
```

### 3.2 Ownership Transfer
```cpp
// Transfer ownership with std::move
std::unique_ptr<Resource> source = createResource();
std::unique_ptr<Resource> dest = std::move(source);
// source is now nullptr, dest owns the resource

// Function taking ownership
void consume(std::unique_ptr<Resource> res) {
    // res is owned here, will be deleted at end of scope
}

consume(std::move(dest));  // Transfer ownership to function
```

### 3.3 Non-Owning References
```cpp
// Use references or raw pointers for non-owning access
void process(const Resource& res) {
    // Non-owning, read-only access
}

void modify(Resource& res) {
    // Non-owning, modifiable access
}

void optional(Resource* res) {
    // Non-owning, can be nullptr
    if (res) {
        // Use res
    }
}
```

## 4. Move Semantics

### 4.1 Move Constructor and Assignment
**Implement move constructors and move assignment for resource-owning types**:

```cpp
class Buffer {
    size_t size_;
    float* data_;
public:
    // Constructor
    explicit Buffer(size_t size)
        : size_(size), data_(new float[size]) { }

    // Destructor
    ~Buffer() { delete[] data_; }

    // Delete copy operations
    Buffer(const Buffer&) = delete;
    Buffer& operator=(const Buffer&) = delete;

    // Move constructor
    Buffer(Buffer&& other) noexcept
        : size_(other.size_), data_(other.data_) {
        other.size_ = 0;
        other.data_ = nullptr;
    }

    // Move assignment
    Buffer& operator=(Buffer&& other) noexcept {
        if (this != &other) {
            delete[] data_;
            size_ = other.size_;
            data_ = other.data_;
            other.size_ = 0;
            other.data_ = nullptr;
        }
        return *this;
    }

    size_t size() const { return size_; }
    float* data() { return data_; }
};
```

### 4.2 Using Move Semantics
```cpp
// Return by value (move optimisation)
Buffer createBuffer(size_t size) {
    return Buffer(size);  // Move, not copy
}

// Store in container (move)
std::vector<Buffer> buffers;
buffers.push_back(createBuffer(1024));  // Move into vector

// Transfer ownership
Buffer buf1(1024);
Buffer buf2 = std::move(buf1);  // buf1 is now empty
```

## 5. CUDA Memory Safety

### 5.1 CUDA RAII Wrapper
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

    ~CudaDeviceMemory() {
        if (ptr_) cudaFree(ptr_);
    }

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

### 5.2 CUDA Memory Management Best Practices
```cpp
// Good: RAII wrapper
void processData(const std::vector<float>& h_data) {
    CudaDeviceMemory<float> d_data(h_data.size());

    cudaMemcpy(d_data.get(), h_data.data(),
               h_data.size() * sizeof(float),
               cudaMemcpyHostToDevice);

    kernel<<<blocks, threads>>>(d_data.get(), h_data.size());

    // d_data automatically freed when out of scope
}

// Bad: Manual memory management
void processData(const std::vector<float>& h_data) {
    float* d_data;
    cudaMalloc(&d_data, h_data.size() * sizeof(float));

    cudaMemcpy(d_data, h_data.data(),
               h_data.size() * sizeof(float),
               cudaMemcpyHostToDevice);

    kernel<<<blocks, threads>>>(d_data, h_data.size());

    cudaFree(d_data);  // Easy to forget, exception-unsafe
}
```

## 6. Container Usage

### 6.1 Standard Containers
**Use standard containers for automatic memory management**:

```cpp
// Good: Automatic memory management
std::vector<float> data(1024);
std::array<int, 10> fixed_size;
std::unique_ptr<float[]> dynamic_array(new float[size]);

// Bad: Manual array management
float* data = new float[1024];
// ... use data ...
delete[] data;  // Easy to forget
```

### 6.2 Container of Smart Pointers
```cpp
// Container of unique_ptr
std::vector<std::unique_ptr<Resource>> resources;
resources.push_back(std::make_unique<Resource>());

// Container of shared_ptr
std::vector<std::shared_ptr<Data>> shared_data;
shared_data.push_back(std::make_shared<Data>());
```

## 7. Exception Safety

### 7.1 Exception-Safe Resource Management
```cpp
// Good: Exception-safe
void processFile(const std::string& filename) {
    std::ifstream file(filename);
    if (!file) {
        throw std::runtime_error("Failed to open file");
    }

    std::vector<float> data;
    // Read data...

    // If exception thrown, file and data are automatically cleaned up
}

// Bad: Not exception-safe
void processFile(const std::string& filename) {
    FILE* file = fopen(filename.c_str(), "r");
    float* data = new float[1024];

    // If exception thrown here, file and data leak!

    fclose(file);
    delete[] data;
}
```

### 7.2 RAII for Exception Safety
```cpp
class Transaction {
    Database& db_;
    bool committed_ = false;
public:
    explicit Transaction(Database& db) : db_(db) {
        db_.beginTransaction();
    }

    ~Transaction() {
        if (!committed_) {
            db_.rollback();  // Automatic rollback if not committed
        }
    }

    void commit() {
        db_.commit();
        committed_ = true;
    }
};

// Usage
void updateDatabase(Database& db) {
    Transaction txn(db);

    // Perform updates...

    txn.commit();  // Explicit commit
    // If exception thrown before commit, automatic rollback
}
```

## 8. Memory Leak Detection

### 8.1 Valgrind
```bash
# Check for memory leaks
valgrind --leak-check=full --show-leak-kinds=all ./build/app

# With suppressions
valgrind --leak-check=full --suppressions=valgrind.supp ./build/app
```

### 8.2 Address Sanitizer
```bash
# Compile with address sanitizer
cmake .. -DCMAKE_CXX_FLAGS="-fsanitize=address -g"
cmake --build .

# Run application
./build/app
```

### 8.3 CUDA Memory Checker
```bash
# Check for CUDA memory leaks
cuda-memcheck --leak-check full ./build/cuda_app

# Check for race conditions
cuda-memcheck --tool racecheck ./build/cuda_app
```

## 9. Common Memory Safety Pitfalls

### 9.1 Dangling Pointers
```cpp
// Bad: Dangling pointer
int* getDanglingPointer() {
    int x = 42;
    return &x;  // Returns pointer to local variable
}

// Good: Return by value or use heap allocation
int getValue() {
    return 42;
}

std::unique_ptr<int> getHeapValue() {
    return std::make_unique<int>(42);
}
```

### 9.2 Double Free
```cpp
// Bad: Double free
int* ptr = new int(42);
delete ptr;
delete ptr;  // Undefined behaviour

// Good: Use smart pointers
auto ptr = std::make_unique<int>(42);
// Automatically deleted once, no double free possible
```

### 9.3 Memory Leaks
```cpp
// Bad: Memory leak
void leak() {
    int* ptr = new int(42);
    // Forgot to delete
}

// Good: Automatic cleanup
void noLeak() {
    auto ptr = std::make_unique<int>(42);
    // Automatically deleted
}
```

### 9.4 Use After Free
```cpp
// Bad: Use after free
int* ptr = new int(42);
delete ptr;
*ptr = 10;  // Undefined behaviour

// Good: Smart pointer prevents use after free
auto ptr = std::make_unique<int>(42);
int value = *ptr;
ptr.reset();  // Explicitly delete
// ptr is now nullptr, dereferencing will crash (better than UB)
```

## 10. Const Correctness for Safety

### 10.1 Const References
```cpp
// Prevent accidental modification
void process(const std::vector<float>& data) {
    // data cannot be modified
    // Compiler enforces const correctness
}
```

### 10.2 Const Methods
```cpp
class Buffer {
    size_t size_;
    float* data_;
public:
    // Const method - doesn't modify state
    size_t size() const { return size_; }
    const float* data() const { return data_; }

    // Non-const method - can modify state
    float* data() { return data_; }
    void resize(size_t new_size);
};
```

## 11. Pre-Commit Memory Safety Checks

### 11.1 Before Every Commit
**MANDATORY** checks before committing:
1. Run Valgrind for C++ memory issues
2. Run cuda-memcheck for CUDA memory issues
3. Compile with address sanitizer
4. Verify no memory leaks

### 11.2 Memory Safety Verification
```bash
# Valgrind for C++ memory issues
valgrind --leak-check=full --show-leak-kinds=all ./build/tests/test_suite

# CUDA memory checker
cuda-memcheck --leak-check full ./build/tests/test_cuda_suite

# Address sanitizer (compile with -fsanitize=address)
cmake .. -DCMAKE_CXX_FLAGS="-fsanitize=address -g"
./build/tests/test_suite
```

## 12. Forbidden Memory Practices

**STRICTLY FORBIDDEN**:
- Using raw pointers for ownership
- Manual `new`/`delete` in application code
- Ignoring memory leaks
- Not using RAII for resource management
- Returning pointers to local variables
- Double free
- Use after free
- Memory leaks

## 13. Code Review Checklist

### 13.1 Memory Safety Review
- [ ] All resources managed via RAII
- [ ] Smart pointers used for ownership
- [ ] No raw `new`/`delete` in application code
- [ ] Move semantics implemented for resource-owning types
- [ ] Ownership semantics clearly documented
- [ ] No memory leaks (verified with Valgrind/cuda-memcheck)
- [ ] Exception-safe resource management
- [ ] Const correctness enforced

## 14. Enforcement

### 14.1 Automated Checks
- Configure CI/CD to run Valgrind
- Configure CI/CD to run cuda-memcheck
- Use address sanitizer in debug builds
- Reject commits with memory leaks

### 14.2 Static Analysis
- Use clang-tidy to detect memory issues
- Use cppcheck for additional checks
- Configure tools to enforce RAII and smart pointer usage
