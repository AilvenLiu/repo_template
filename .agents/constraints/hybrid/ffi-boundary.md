---
id: hybrid/ffi-boundary
name: FFI Boundary Patterns
description: Python/C++/CUDA interop patterns for AI infrastructure projects
category: hybrid
status: draft
applies_to:
  - "*.py (when calling native extensions)"
  - "*.cpp (when exposing to Python)"
  - "*.cu (when exposing CUDA to Python)"
severity: advisory
---

# FFI Boundary Patterns

**Status**: DRAFT (advisory only, does not block commits)

This constraint defines patterns for Foreign Function Interface (FFI) boundaries between Python and C++/CUDA code in AI infrastructure projects. It covers binding library selection, GIL management, zero-copy tensor exchange, error propagation, async semantics, memory ownership, and type marshalling.

## Scope

This constraint applies to:
- Python extensions wrapping C++/CUDA code
- Tensor exchange between Python frameworks (PyTorch, JAX, NumPy) and native code
- Async operations crossing the Python/native boundary
- Memory management across language boundaries

## 1. Binding Library Selection

### 1.1 Library Comparison

| Library | C++ Std | Python | Compile Time | Binary Size | Runtime Overhead | Use Case |
|---------|---------|--------|--------------|-------------|------------------|----------|
| **pybind11** | C++11+ | 2.7+ | Baseline | Baseline | Baseline | Mature, feature-complete, legacy compat |
| **nanobind** | C++17+ | 3.8+ | 4x faster | 5x smaller | 10x lower | New projects, efficiency-critical |
| **ctypes** | N/A | Any | None (pure Python) | N/A | 10-100x slower | Simple C APIs, no compilation |
| **cffi** | C only | Any | Moderate | Moderate | ~2x slower | C library wrapping |
| **TVM-FFI** | C++11+ | 3.6+ | Moderate | Moderate | Competitive | TVM ecosystem only |

### 1.2 Selection Criteria

**Choose pybind11 when**:
- Working with legacy codebases (C++11 required)
- Need features not yet in nanobind (custom exception translators, multiple inheritance)
- Large existing pybind11 codebase
- Broad ecosystem compatibility required

**Choose nanobind when**:
- Starting new projects (C++17+ available)
- Binary size matters (embedded, mobile, edge deployment)
- Compile time is a bottleneck (large codebases)
- Memory efficiency critical (high object churn)

**Choose ctypes when**:
- Wrapping simple C APIs
- Cannot compile extensions (deployment constraints)
- Quick prototyping only

**Choose cffi when**:
- Wrapping C libraries (not C++)
- Need both compiled and dynamic loading modes
- PyPy compatibility required

**Avoid TVM-FFI** outside the TVM ecosystem - it's not a general-purpose binding library.

### 1.3 Migration Path

pybind11 and nanobind have nearly identical APIs. Migration example:

```cpp
// pybind11
#include <pybind11/pybind11.h>
namespace py = pybind11;

// nanobind (minimal changes)
#include <nanobind/nanobind.h>
namespace nb = nanobind;

// Most code unchanged
NB_MODULE(mymodule, m) {  // was PYBIND11_MODULE
    nb::class_<MyClass>(m, "MyClass")
        .def(nb::init<>())
        .def("method", &MyClass::method);
}
```

## 2. GIL Management

The Global Interpreter Lock (GIL) serializes Python bytecode execution. Release it for true parallelism in C++ code.

### 2.1 When to Release GIL

**MUST release GIL**:
- Long-running computations (>1ms)
- CUDA kernel launches and synchronization
- Blocking I/O operations
- Parallel work across multiple Python threads

**MUST hold GIL**:
- Accessing any Python object (PyObject*)
- Calling Python callbacks from C++
- Type conversions between Python and C++
- Raising Python exceptions

### 2.2 Release Patterns

**Manual release (pybind11)**:
```cpp
m.def("compute", [](py::array_t<double> data) {
    py::gil_scoped_release release;
    // Long computation here - GIL released
    return expensive_computation(data.data());
});
```

**Using call_guard (cleaner)**:
```cpp
m.def("compute", &expensive_computation, 
      py::call_guard<py::gil_scoped_release>());
```

**Reacquiring when needed**:
```cpp
void process() {
    py::gil_scoped_release release;
    // C++ work without GIL
    
    {
        py::gil_scoped_acquire acquire;
        // Call Python callback
        python_callback();
    }
    
    // Continue C++ work without GIL
}
```

**nanobind equivalent**:
```cpp
m.def("compute", [](nb::ndarray<double> data) {
    nb::gil_scoped_release release;
    // Computation without GIL
    return result;
});
```

### 2.3 Common Pitfalls

**CRITICAL**: Accessing Python objects without GIL causes crashes or memory corruption.

```cpp
// WRONG - crashes
m.def("bad", [](py::list items) {
    py::gil_scoped_release release;
    for (auto item : items) {  // CRASH: accessing Python object without GIL
        process(item);
    }
});

// CORRECT - extract data first
m.def("good", [](py::list items) {
    std::vector<int> data;
    for (auto item : items) {
        data.push_back(item.cast<int>());
    }
    
    py::gil_scoped_release release;
    for (int val : data) {  // Safe: pure C++ data
        process(val);
    }
});
```

### 2.4 Python 3.13 nogil Implications

Python 3.13 experimental free-threaded build removes the GIL. C extensions must:
- Use new synchronization primitives for shared state
- Avoid assumptions about GIL-based thread safety
- Audit all global/static variable access

Both pybind11 and nanobind are adding support. Migration requires careful review.

## 3. DLPack Protocol

DLPack enables zero-copy tensor exchange between frameworks (NumPy, PyTorch, JAX, TensorFlow, CuPy).

### 3.1 Core Structures

```c
typedef struct {
    void* data;              // Pointer to data (256-byte aligned)
    DLDevice device;         // Device type and ID
    int32_t ndim;           // Number of dimensions
    DLDataType dtype;       // Data type (code, bits, lanes)
    int64_t* shape;         // Dimension sizes
    int64_t* strides;       // Strides (required in v1.2+)
    uint64_t byte_offset;   // Offset to actual data
} DLTensor;

typedef struct DLManagedTensor {
    DLTensor dl_tensor;
    void* manager_ctx;      // Framework-specific context
    void (*deleter)(struct DLManagedTensor*);
} DLManagedTensor;
```

### 3.2 Python Protocol

**Producer side**:
```python
class MyTensor:
    def __dlpack__(self, stream=None):
        # Create DLManagedTensor, wrap in PyCapsule
        capsule = PyCapsule_New(managed_tensor, "dltensor", deleter)
        return capsule
    
    def __dlpack_device__(self):
        return (device_type, device_id)
```

**Consumer side**:
```python
def from_dlpack(tensor):
    capsule = tensor.__dlpack__()
    # Extract DLManagedTensor
    managed = PyCapsule_GetPointer(capsule, "dltensor")
    
    # CRITICAL: Rename capsule to prevent double-free
    PyCapsule_SetName(capsule, "used_dltensor")
    
    # Create view on data
    return create_tensor_view(managed.dl_tensor)
```

### 3.3 Lifetime Management

**Rules**:
- Producer retains ownership
- Consumer borrows temporarily
- Consumer MUST call deleter when finished
- Deleter releases resources and frees DLManagedTensor

**Example**:
```python
# Zero-copy exchange
torch_tensor = torch.randn(100, 100, device='cuda')
numpy_view = np.from_dlpack(torch_tensor)  # No copy
jax_view = jax.dlpack.from_dlpack(torch_tensor)  # No copy

# All three share the same GPU memory
```

### 3.4 Common Pitfalls

**Mutation hazard**: Consumer and producer share memory. Treat exchanged arrays as read-only unless you control both sides.

```python
# DANGEROUS
torch_tensor = torch.ones(10)
numpy_view = np.from_dlpack(torch_tensor)
numpy_view[0] = 999  # Mutates torch_tensor too!
```

**Capsule renaming**: Always rename capsule after extraction to prevent double-free:
```c
PyCapsule_SetName(capsule, "used_dltensor");
```

## 4. PyCapsule Patterns

PyCapsules wrap opaque C/C++ pointers for safe cross-module passing.

### 4.1 Basic Usage

**Producer**:
```c
MyClass* obj = new MyClass();
PyObject* capsule = PyCapsule_New(
    obj,                    // Pointer
    "mymodule.MyClass",    // Name (for type safety)
    [](PyObject* cap) {    // Destructor
        MyClass* p = (MyClass*)PyCapsule_GetPointer(cap, "mymodule.MyClass");
        delete p;
    }
);
```

**Consumer**:
```c
void* ptr = PyCapsule_GetPointer(capsule, "mymodule.MyClass");
if (!ptr) {
    // Handle error - wrong name or invalid capsule
    return;
}
MyClass* obj = static_cast<MyClass*>(ptr);
```

### 4.2 Cross-Module API Export

**Module A (exporter)**:
```c
static int my_api_function(int x) { return x * 2; }

static void* api_table[] = {
    (void*)my_api_function
};

PyObject* c_api = PyCapsule_New(api_table, "mymodule._C_API", NULL);
PyModule_AddObject(module, "_C_API", c_api);
```

**Module B (importer)**:
```c
PyObject* c_api = PyCapsule_Import("mymodule._C_API", 0);
void** api = (void**)c_api;
int (*func)(int) = (int(*)(int))api[0];
int result = func(42);
```

### 4.3 Best Practices

- Always use descriptive names for type safety (module.attribute convention)
- Validate with `PyCapsule_IsValid()` before access
- Set destructors for resource cleanup
- Handle NULL returns (distinguish valid NULL from errors using `PyErr_Occurred()`)

## 5. Error Propagation

### 5.1 C++ to Python Exception Mapping

**Automatic translation (pybind11/nanobind)**:
```cpp
std::out_of_range      -> IndexError
std::invalid_argument  -> ValueError
std::bad_alloc         -> MemoryError
std::exception         -> RuntimeError
```

**Custom exceptions**:
```cpp
static py::exception<MyError> exc(m, "MyError");

m.def("risky", []() {
    throw MyError("something failed");  // Becomes Python MyError
});
```

**Manual exception setting**:
```cpp
PyErr_SetString(PyExc_ValueError, "Invalid input");
return nullptr;
```

### 5.2 CUDA Error Handling

**Macro for automatic checking**:
```cpp
#define CUDA_CHECK(call) do { \
    cudaError_t err = call; \
    if (err != cudaSuccess) { \
        throw std::runtime_error( \
            std::string("CUDA error: ") + cudaGetErrorString(err)); \
    } \
} while(0)
```

**In bindings**:
```cpp
m.def("cuda_operation", []() {
    py::gil_scoped_release release;
    
    CUDA_CHECK(cudaMalloc(&ptr, size));
    CUDA_CHECK(cudaMemcpy(ptr, data, size, cudaMemcpyHostToDevice));
    
    kernel<<<blocks, threads>>>(ptr);
    CUDA_CHECK(cudaGetLastError());      // Check kernel launch
    CUDA_CHECK(cudaDeviceSynchronize()); // Check execution
});
```

**Key distinction**:
- `cudaPeekAtLastError()`: queries without clearing
- `cudaGetLastError()`: queries and clears

Always check both kernel launch and execution.

### 5.3 Exception Chaining

**pybind11**:
```cpp
try {
    risky_operation();
} catch (const std::exception& e) {
    py::raise_from(PyExc_RuntimeError, "Operation failed");
}
```

**nanobind**:
```cpp
nb::raise_from(nb::type_error("Invalid type"), "During conversion");
```

### 5.4 Context Preservation

Both libraries preserve exception messages and support chaining. Use `error_already_set` to catch Python exceptions in C++ and inspect them:

```cpp
try {
    py::object result = python_function();
} catch (py::error_already_set& e) {
    // Inspect Python exception
    if (e.matches(PyExc_ValueError)) {
        // Handle ValueError
    }
    throw;  // Re-raise
}
```

## 6. Async Semantics

CUDA operations are asynchronous by default. Synchronizing with Python async/await requires careful coordination.

### 6.1 CUDA Stream Patterns

**Basic stream usage**:
```python
import torch

# Create stream
stream = torch.cuda.Stream()

# Launch async operations
with torch.cuda.stream(stream):
    result = model(input)  # Async kernel launches

# Synchronize
stream.synchronize()  # Blocks until complete
```

**Event-based synchronization**:
```python
event = torch.cuda.Event()
event.record(stream)
event.synchronize()

# Or check without blocking
if event.query():
    print("Stream completed")
```

### 6.2 C++ Side with Callbacks

**CUDA callback (runs on device thread)**:
```cpp
void CUDART_CB stream_callback(cudaStream_t stream, cudaError_t status, void* userData) {
    // WARNING: Cannot call Python here without GIL
    // Must queue work for main thread
    auto* queue = static_cast<WorkQueue*>(userData);
    queue->push([status]() {
        py::gil_scoped_acquire acquire;
        python_callback(status);
    });
}

// Register callback
cudaStreamAddCallback(stream, stream_callback, userData, 0);
```

**CRITICAL**: CUDA callbacks execute on a driver thread without the GIL. You cannot call Python directly - must queue work for the main thread.

### 6.3 Integration with Python async

**Polling pattern (not ideal)**:
```python
import asyncio
import torch

async def async_cuda_operation():
    stream = torch.cuda.Stream()
    with torch.cuda.stream(stream):
        result = model(input)
    
    # Poll for completion
    while not stream.query():
        await asyncio.sleep(0)  # Yield to event loop
    
    return result
```

**Thread pool pattern (better)**:
```python
async def async_cuda_operation_better():
    stream = torch.cuda.Stream()
    with torch.cuda.stream(stream):
        result = model(input)
    
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, stream.synchronize)
    return result
```

### 6.4 Common Pitfalls

- CUDA callbacks run on driver threads without GIL - cannot call Python directly
- PyTorch doesn't expose `cudaStreamAddCallback` directly - use events instead
- Polling with `asyncio.sleep(0)` is inefficient - prefer thread pool executor
- Always synchronize before accessing results from async operations

## 7. Memory Ownership

### 7.1 pybind11 Return Value Policies

```cpp
// take_ownership: Python owns, will delete
.def("create", []() { return new Object(); }, 
     py::return_value_policy::take_ownership)

// reference: C++ owns, Python just references
.def("get_global", []() { return &global_object; },
     py::return_value_policy::reference)

// reference_internal: Keep parent alive while child referenced
.def_property_readonly("data", &Container::get_data,
     py::return_value_policy::reference_internal)

// copy: Make Python-owned copy
.def("get_value", &get_value,
     py::return_value_policy::copy)

// move: Transfer via move semantics
.def("take_value", &take_value,
     py::return_value_policy::move)
```

### 7.2 nanobind Intrusive Reference Counting

**Most efficient approach**:
```cpp
#include <nanobind/intrusive/counter.h>

class MyClass {
    NB_INTRUSIVE_COUNTER(MyClass);  // Adds ref counting
public:
    // ...
};

// Binding
nb::class_<MyClass>(m, "MyClass")
    .def(nb::init<>());

// Automatic ref counting across boundary
```

### 7.3 Smart Pointer Integration

**Shared ownership**:
```cpp
py::class_<Widget, std::shared_ptr<Widget>>(m, "Widget")
    .def(py::init<>());
```

**Unique ownership transfer**:
```cpp
m.def("create_widget", []() {
    return std::make_unique<Widget>();
});
```

### 7.4 RAII Patterns

**C++ side**:
```cpp
class CudaBuffer {
    void* ptr_;
    size_t size_;
public:
    CudaBuffer(size_t size) : size_(size) {
        cudaMalloc(&ptr_, size);
    }
    ~CudaBuffer() {
        cudaFree(ptr_);
    }
    void* data() { return ptr_; }
};
```

**Python binding**:
```cpp
py::class_<CudaBuffer>(m, "CudaBuffer")
    .def(py::init<size_t>())
    .def("data", &CudaBuffer::data);
```

**Python side**:
```python
buffer = CudaBuffer(1024)  # Allocates
# ... use buffer ...
# Automatically freed when garbage collected
```

### 7.5 Memory Leak Prevention

- Use smart pointers or RAII wrappers for all resources
- Match every `new` with appropriate return value policy
- Be cautious with `reference` policy - ensure C++ object outlives Python references
- Use `keep_alive` policy to tie lifetimes together:

```cpp
.def("set_parent", &Child::set_parent, py::keep_alive<1, 2>())
// Keep arg 2 (parent) alive as long as arg 1 (self) is alive
```

## 8. Type Marshalling

### 8.1 NumPy Array to C++ Pointer (pybind11)

```cpp
m.def("process", [](py::array_t<double> input) {
    py::buffer_info buf = input.request();
    
    if (buf.ndim != 2)
        throw std::runtime_error("Expected 2D array");
    
    double* ptr = static_cast<double*>(buf.ptr);
    size_t rows = buf.shape[0];
    size_t cols = buf.shape[1];
    
    // Process data
    for (size_t i = 0; i < rows * cols; i++)
        ptr[i] *= 2.0;
});
```

### 8.2 nanobind Tensor Marshalling

**Accept any framework, any device**:
```cpp
#include <nanobind/ndarray.h>

void process(nb::ndarray<float> input) {
    float* data = input.data();
    size_t size = input.size();
    // ...
}
```

**Constrained: NumPy only, CPU, 2D, contiguous**:
```cpp
void process_strict(
    nb::ndarray<double, nb::shape<-1, -1>, nb::c_contig, nb::device::cpu> input
) {
    // Guaranteed properties
}
```

**Return PyTorch tensor**:
```cpp
nb::ndarray<nb::pytorch, float> create_tensor() {
    float* data = new float[100];
    return nb::ndarray<nb::pytorch, float>(data, {10, 10});
}
```

### 8.3 Scalar Type Conversions

**Automatic for basic types**:
```cpp
int, float, double, bool, std::string
```

**Complex types require registration**:
```cpp
py::class_<Vec3>(m, "Vec3")
    .def(py::init<float, float, float>())
    .def_readwrite("x", &Vec3::x)
    .def_readwrite("y", &Vec3::y)
    .def_readwrite("z", &Vec3::z);
```

**Custom type caster**:
```cpp
namespace pybind11 { namespace detail {
    template <> struct type_caster<MyType> {
        PYBIND11_TYPE_CASTER(MyType, _("MyType"));
        
        bool load(handle src, bool convert) {
            // Python -> C++
            return true;
        }
        
        static handle cast(MyType src, return_value_policy policy, handle parent) {
            // C++ -> Python
            return handle();
        }
    };
}}
```

### 8.4 Struct Passing

**Define structured dtype**:
```cpp
struct Particle {
    float x, y, z;
    int id;
};

PYBIND11_NUMPY_DTYPE(Particle, x, y, z, id);

// Now can pass structured arrays
m.def("process_particles", [](py::array_t<Particle> particles) {
    auto buf = particles.request();
    Particle* ptr = static_cast<Particle*>(buf.ptr);
    // Direct access to structured data
});
```

### 8.5 Performance Considerations

- **Zero-copy via buffer protocol** when possible
- Use `unchecked<N>()` for bounds-check-free access in hot loops:
  ```cpp
  auto r = input.unchecked<2>();  // 2D array
  for (size_t i = 0; i < rows; i++)
      for (size_t j = 0; j < cols; j++)
          result += r(i, j);  // No bounds check
  ```
- Prefer contiguous arrays (C or Fortran order)
- DLPack for GPU tensors to avoid host-device copies
- nanobind's ndarray is more efficient than pybind11's array_t

## Enforcement

**Status**: DRAFT - advisory only, does not block commits.

This constraint is enforced through:
1. **Code review**: Reviewers check FFI patterns against this document
2. **AI agent guidance**: Loaded into agent context when working with Python/C++/CUDA interop
3. **Testing**: Verify memory safety, GIL correctness, and zero-copy semantics

Common issues to watch for:
- Accessing Python objects without GIL
- Memory leaks from incorrect return value policies
- DLPack capsule not renamed (double-free risk)
- CUDA errors not checked after kernel launch
- Blocking synchronization in async contexts

## References

- pybind11 documentation: https://pybind11.readthedocs.io/
- nanobind documentation: https://nanobind.readthedocs.io/
- DLPack specification: https://github.com/dmlc/dlpack
- Python C API: https://docs.python.org/3/c-api/
- CUDA Runtime API: https://docs.nvidia.com/cuda/cuda-runtime-api/
- Python 3.13 nogil: https://peps.python.org/pep-0703/
