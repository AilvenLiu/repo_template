---
name: context7
description: Retrieve documentation and API references from Context7 MCP server. Use when you need official documentation for libraries, frameworks, or APIs. Automatically triggered when user asks about library documentation or API usage.
version: 1.0.0
---

# Context7 Documentation Retrieval Skill

This skill provides intelligent documentation retrieval through the Context7 MCP server, giving Claude Code access to official documentation for thousands of libraries and frameworks.

## When to Use

This skill is automatically triggered when:
- User asks "how do I use [library]?"
- User requests API documentation
- User needs examples for a specific library function
- User asks about framework best practices
- Code references an unfamiliar library

## What It Does

1. **Detects documentation needs** from user queries or code context
2. **Queries Context7 MCP** for relevant documentation
3. **Retrieves focused content** (not entire docs, just relevant sections)
4. **Formats for readability** with code examples highlighted

## MCP Server Setup

Context7 MCP server must be configured at the project level.

### Step 1: Add Context7 MCP Server

Run this command in your project directory:

```bash
claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
```

### Step 2: Enable Auto-Activation

Add this to your project's CLAUDE.md:

```markdown
Always use context7 when I need code generation, setup or configuration steps, or library/API documentation. This means you should automatically use the Context7 MCP tools to resolve library id and get library docs without me having to explicitly ask.
```

### Step 3: Verify Setup

Check if Context7 is available:
```bash
python3 .claude/skills/context7/scripts/check_mcp.py
```

## Usage

### Automatic Mode (Recommended)

With the CLAUDE.md configuration above, Claude Code will automatically use Context7 when needed. No manual invocation required.

### Manual Mode

If you need to explicitly query documentation:

```bash
/context7 <library> <query>
```

**Examples:**
```bash
/context7 pytorch "custom dataset"
/context7 fastapi "dependency injection"
/context7 react "useEffect hook"
```

## Supported Libraries

Context7 provides documentation for 1000+ libraries including:
- **Python**: pytorch, tensorflow, fastapi, django, flask, pandas, numpy, scikit-learn
- **JavaScript/TypeScript**: react, vue, angular, express, next.js
- **C++**: boost, eigen, opencv, cuda
- **And many more**

## How It Works

### 1. Library Resolution

First, resolve the library ID:
```python
# MCP tool: context7_resolve_library
result = mcp.call_tool("context7_resolve_library", {
    "library_name": "pytorch"
})
# Returns: library_id for use in documentation queries
```

### 2. Documentation Retrieval

Then fetch relevant documentation:
```python
# MCP tool: context7_get_docs
result = mcp.call_tool("context7_get_docs", {
    "library_id": library_id,
    "query": "custom dataset",
    "max_results": 3
})
# Returns: formatted documentation with code examples
```

### 3. Result Processing

The skill formats results for readability:
- Extracts relevant code examples
- Highlights key concepts
- Provides direct links to full documentation

## Integration with Other Skills

### With /init

When /init detects unfamiliar imports:
```
[INFO] Detected import: from transformers import AutoModel
[SUGGESTION] Context7 can provide documentation for transformers
```

### With /dependency

When adding a new dependency:
```bash
$ /dependency add fastapi
[OK] fastapi installed
[INFO] Use Context7 to learn FastAPI basics
```

## Examples

### Example 1: PyTorch Custom Dataset

Query: "How do I create a custom PyTorch dataset?"

Context7 returns:

```
PyTorch Documentation: Custom Datasets

Creating a Custom Dataset:
----------------------------------------

from torch.utils.data import Dataset

class CustomDataset(Dataset):
    def __init__(self, data, labels):
        self.data = data
        self.labels = labels

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx], self.labels[idx]

Key Points:
- Inherit from torch.utils.data.Dataset
- Implement __len__() to return dataset size
- Implement __getitem__() to return a single sample

Full documentation: https://pytorch.org/tutorials/beginner/basics/data_tutorial.html
```

### Example 2: FastAPI Dependency Injection

Query: "How does dependency injection work in FastAPI?"

Context7 returns:

```
FastAPI Documentation: Dependency Injection

Basic Dependency:
----------------------------------------

from fastapi import Depends, FastAPI

def get_db():
    db = Database()
    try:
        yield db
    finally:
        db.close()

@app.get("/items/")
async def read_items(db = Depends(get_db)):
    return db.query_items()

Key Points:
- Use Depends() to declare dependencies
- Dependencies can be functions or classes
- Supports nested dependencies
- Automatic cleanup with context managers

Full documentation: https://fastapi.tiangolo.com/tutorial/dependencies/
```

## Troubleshooting

### "Context7 MCP server not available"

1. Verify MCP server is added:
   ```bash
   claude mcp list
   ```

2. Re-add if missing:
   ```bash
   claude mcp add --transport http context7 https://mcp.context7.com/mcp --header "CONTEXT7_API_KEY: ctx7sk-0eaf81b0-48fa-418f-9e7f-181103e50665"
   ```

3. Restart Claude Code session

### "Library not found"

- Try alternative names (e.g., "sklearn" vs "scikit-learn")
- Check spelling
- Verify library is in Context7's database

### "Query too broad"

Be more specific:
- Bad: /context7 pytorch "usage"
- Good: /context7 pytorch "DataLoader batch_size"

## Best Practices

1. **Be specific**: "custom loss function" > "loss"
2. **Include context**: "pytorch custom loss function" > "loss function"
3. **Use for learning**: Great for understanding new libraries
4. **Combine with code**: Read docs, then implement
5. **Let it auto-activate**: Add to CLAUDE.md for automatic usage

## Limitations

- Requires internet connection
- Documentation may be slightly outdated
- Not all libraries are covered
- Code examples may need adaptation to your specific use case

## Version History

- **1.0.0** (2026-03-06): Initial release
  - Context7 MCP integration
  - Library resolution and documentation retrieval
  - Formatted output with examples
  - Auto-activation support
