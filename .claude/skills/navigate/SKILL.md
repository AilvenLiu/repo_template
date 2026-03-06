---
name: navigate
description: Navigate and analyze code structure. Find definitions, trace dependencies, analyze call graphs, and understand repository architecture. Use when exploring unfamiliar code or understanding code relationships.
version: 1.0.0
---

# Code Navigation and Analysis Skill

This skill provides intelligent code navigation and structural analysis for both Python and C++/CUDA projects. It helps Claude Code understand repository architecture and trace code relationships.

## When to Use

Automatically triggered when:
- User asks "where is [function/class] defined?"
- User needs to understand code dependencies
- User wants to see call graphs or usage patterns
- User asks about repository structure
- Exploring unfamiliar codebase

## What It Does

1. **Find Definitions**: Locate where functions, classes, or variables are defined
2. **Trace Dependencies**: Show what imports/includes what
3. **Analyze Call Graphs**: See who calls a function and what it calls
4. **Map Architecture**: Understand high-level repository structure
5. **Find Usages**: Locate all references to a symbol

## Available Commands

### /navigate find <symbol>

Find where a symbol is defined.

```bash
/navigate find CustomDataset
/navigate find process_data
/navigate find CUDA_KERNEL_SIZE
```

**Output:**
```
Symbol: CustomDataset
Type: class
Defined in: src/data/dataset.py:15
```

### /navigate uses <symbol>

Find all usages of a symbol.

```bash
/navigate uses CustomDataset
```

**Output:**
```
CustomDataset is used in:
- src/train.py:42 (instantiation)
- src/eval.py:28 (instantiation)
- tests/test_dataset.py:10 (import)
```

### /navigate deps <file>

Show dependencies for a file.

```bash
/navigate deps src/model.py
```

**Output:**
```
src/model.py depends on:
- torch (external)
- torch.nn (external)
- src/layers.py (internal)
- src/utils.py (internal)
```

### /navigate arch

Analyze repository architecture.

```bash
/navigate arch
```

**Output:**
```
Repository Architecture:

src/
  data/       - Data loading and preprocessing
  models/     - Model definitions
  training/   - Training loops and optimization
  utils/      - Utility functions

Key entry points:
- src/main.py (main application)
- src/train.py (training script)

Core modules:
- src/models/base.py (base model class)
- src/data/dataset.py (dataset implementations)
```

### /navigate calls <function>

Show call graph for a function.

```bash
/navigate calls train_model
```

**Output:**
```
train_model() calls:
- load_data()
- create_model()
- optimizer.step()
- save_checkpoint()

train_model() is called by:
- main()
- run_experiment()
```

## How It Works

### For Python Projects

Uses AST (Abstract Syntax Tree) analysis:

```python
import ast

# Parse Python file
tree = ast.parse(source_code)

# Find class definitions
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef):
        print(f"Found class: {node.name} at line {node.lineno}")
```

### For C++/CUDA Projects

Uses regex patterns and clang-based tools:

```bash
# Find function definitions
grep -rn "void.*function_name" src/

# Use clang-query for precise analysis
clang-query -c "match functionDecl(hasName('function_name'))" src/
```

## Integration with Other Skills

### With /init

When /init detects a large codebase:
```
[INFO] Large codebase detected (500+ files)
[SUGGESTION] Use /navigate arch to understand structure
```

### With Context7

When exploring unfamiliar libraries:
```
[INFO] Found import: from transformers import AutoModel
[SUGGESTION] /context7 transformers "AutoModel"
[SUGGESTION] /navigate uses AutoModel
```

## Examples

### Example 1: Finding a Function Definition

```bash
$ /navigate find process_batch

Searching for: process_batch

Found 1 definition:
----------------------------------------
Function: process_batch
File: src/data/processor.py
Line: 45
Signature: def process_batch(batch: List[Dict], config: Config) -> Tensor

Context:
    def process_batch(batch: List[Dict], config: Config) -> Tensor:
        """Process a batch of data samples."""
        tensors = [preprocess(item) for item in batch]
        return torch.stack(tensors)
```

### Example 2: Tracing Dependencies

```bash
$ /navigate deps src/model.py

Dependencies for src/model.py:
----------------------------------------

External dependencies:
- torch
- torch.nn
- numpy

Internal dependencies:
- src/layers.py (imports: CustomLayer, AttentionLayer)
- src/utils.py (imports: initialize_weights)
- src/config.py (imports: ModelConfig)

Dependency graph:
src/model.py
  -> src/layers.py
      -> torch.nn
  -> src/utils.py
      -> numpy
  -> src/config.py
```

### Example 3: Architecture Analysis

```bash
$ /navigate arch

Repository Architecture Analysis:
========================================

Project Type: Python (PyTorch)
Total Files: 127 Python files
Lines of Code: ~15,000

Directory Structure:
----------------------------------------
src/
  data/          (8 files, ~2000 LOC)
    - dataset.py       - Dataset implementations
    - loader.py        - Data loading utilities
    - transforms.py    - Data transformations

  models/        (12 files, ~5000 LOC)
    - base.py          - Base model class
    - resnet.py        - ResNet implementation
    - transformer.py   - Transformer model

  training/      (6 files, ~3000 LOC)
    - trainer.py       - Training loop
    - optimizer.py     - Optimization utilities
    - scheduler.py     - Learning rate scheduling

  utils/         (5 files, ~1500 LOC)
    - logging.py       - Logging utilities
    - metrics.py       - Evaluation metrics
    - checkpoint.py    - Model checkpointing

tests/          (15 files, ~3500 LOC)
  - test_data.py
  - test_models.py
  - test_training.py

Entry Points:
----------------------------------------
- src/main.py          - Main application entry
- src/train.py         - Training script
- src/eval.py          - Evaluation script

Core Dependencies:
----------------------------------------
- torch >= 2.0.0
- numpy >= 1.24.0
- transformers >= 4.30.0

Architecture Patterns:
----------------------------------------
- Factory pattern in models/
- Strategy pattern in training/
- Observer pattern for logging
```

## Advanced Features

### Symbol Search with Filters

```bash
# Find only class definitions
/navigate find CustomDataset --type class

# Find in specific directory
/navigate find process_data --path src/data/

# Case-insensitive search
/navigate find customdataset --ignore-case
```

### Dependency Visualization

```bash
# Generate dependency graph (requires graphviz)
/navigate deps --graph src/

# Output: dependency_graph.png
```

### Call Graph Analysis

```bash
# Show full call chain
/navigate calls train_model --depth 3

# Show only direct calls
/navigate calls train_model --depth 1
```

## Troubleshooting

### "Symbol not found"

- Check spelling
- Symbol might be in external library
- Try case-insensitive search: --ignore-case

### "Too many results"

- Be more specific with --path filter
- Use --type to filter by symbol type
- Check if symbol is too common (e.g., "data", "model")

### "Dependency analysis failed"

- Ensure project has proper import structure
- For C++, ensure compile_commands.json exists
- Check for circular dependencies

## Best Practices

1. **Start with architecture**: Run /navigate arch first
2. **Use filters**: Narrow down searches with --path and --type
3. **Combine with grep**: Use Grep tool for content search
4. **Understand before modifying**: Navigate code before making changes
5. **Document findings**: Add comments about discovered relationships

## Limitations

- Dynamic imports may not be detected
- Reflection/metaprogramming can hide relationships
- External library internals not analyzed
- Large codebases may take time to analyze

## Version History

- **1.0.0** (2026-03-06): Initial release
  - Symbol definition finding
  - Dependency tracing
  - Call graph analysis
  - Architecture mapping
  - Usage finding
