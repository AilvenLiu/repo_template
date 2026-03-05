# Python Project Templates

This directory contains template files for Python projects.

## poetry.toml

This file configures Poetry to create virtual environments inside the project directory (`.venv/`) instead of in a centralized cache location.

### Usage

When initializing a new Python project with Poetry, copy this file to the project root:

```bash
cp templates/python/poetry.toml /path/to/your/project/
```

Or create it manually:

```bash
cd /path/to/your/project
poetry config virtualenvs.in-project true --local
```

### Why In-Project Virtual Environments?

Benefits of having `.venv/` inside the project:

1. **Easy to locate**: No need to search for where Poetry cached the venv
2. **IDE integration**: Most IDEs automatically detect `.venv/` in the project root
3. **Consistent with other tools**: Works well with pyenv, direnv, and other Python version managers
4. **Simpler cleanup**: Just delete the project directory to remove everything
5. **Better for Docker**: Easier to exclude from Docker builds with `.dockerignore`

### Configuration Details

The `poetry.toml` file contains:

```toml
[virtualenvs]
in-project = true
```

This is a **local** configuration that only affects the current project. It overrides any global Poetry settings.

### Automatic Configuration

The `/dependency` skill automatically:
- Detects if Poetry is using an external venv
- Removes external venvs if found
- Configures Poetry to use in-project venvs
- Creates `poetry.toml` in the project root

So you typically don't need to manually copy this file.
