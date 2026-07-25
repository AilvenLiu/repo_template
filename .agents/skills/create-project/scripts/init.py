#!/usr/bin/env python3
"""Initialize a new project from the repo_template.

Copies the shared template tree (.agents/, .claude/, .codex/, .github/, agent_roadmaps/) verbatim,
then overlays the language-specific files from
templates/<language>/ onto the target directory using the language's
generic file names (CLAUDE.md, AGENTS.md, CONTRIBUTING.md, .gitignore).
"""

import shutil
import subprocess
import sys
from pathlib import Path


def prompt_project_type() -> str:
    print("Select project type:")
    print("1. Python")
    print("2. C++/CUDA")
    print("3. Hybrid (Python/C++/CUDA)")
    print()
    while True:
        choice = input("Enter choice (1, 2, or 3): ").strip()
        if choice == "1":
            return "python"
        elif choice == "2":
            return "cpp"
        elif choice == "3":
            return "hybrid"
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


# Files to copy from templates/<language>/<src> to <target>/<dst>.
# (The source directory is templates/<language>/, the dst path is relative to
# the target project root.)
_FILE_MAP = {
    "python": [
        ("AGENTS.md", "AGENTS.md"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        (".gitignore", ".gitignore"),
        ("project.yml", ".agents/project.yml"),
        ("poetry.toml", "poetry.toml"),
    ],
    "cpp": [
        ("AGENTS.md", "AGENTS.md"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        (".gitignore", ".gitignore"),
        ("project.yml", ".agents/project.yml"),
    ],
    "hybrid": [
        ("AGENTS.md", "AGENTS.md"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        (".gitignore", ".gitignore"),
        ("project.yml", ".agents/project.yml"),
    ],
}

# Directories to copy verbatim
_COPY_DIRS = [".agents", ".claude", ".codex", ".github", "agent_roadmaps"]
_COPY_IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", "*.pyo", ".DS_Store", "session_state.json"
)


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)


def _create_cpm_layout(target_dir: Path) -> None:
    for dirname in [
        "cmake/Toolchains",
        "3rdparty/cpm-cache",
        "3rdparty/patches",
        "3rdparty/licenses",
        "cpp/include",
        "cpp/src",
        "cuda/include",
        "cuda/src",
        "benchmarks",
    ]:
        (target_dir / dirname).mkdir(parents=True, exist_ok=True)

    for keep in [
        "3rdparty/.gitkeep",
        "3rdparty/cpm-cache/.gitkeep",
        "cpp/include/.gitkeep",
        "cpp/src/.gitkeep",
        "cuda/include/.gitkeep",
        "cuda/src/.gitkeep",
        "benchmarks/.gitkeep",
    ]:
        _write_if_missing(target_dir / keep, "")

    _write_if_missing(
        target_dir / "3rdparty" / "README.md",
        "# Third-Party Dependencies\n\n"
        "CPM-managed source caches live under `cpm-cache/` and are normally "
        "ignored by Git except for `.gitkeep`.\n\n"
        "- Store local patches under `patches/`.\n"
        "- Store licence notes or snapshots under `licenses/`.\n"
        "- Do not silently vendor large dependency trees.\n",
    )

    _write_if_missing(
        target_dir / "cmake" / "CPM.cmake",
        "# Project-local CPM entrypoint.\n"
        "# Replace this placeholder with a pinned CPM.cmake release when adding\n"
        "# the first CPM-managed dependency.\n",
    )

    _write_if_missing(
        target_dir / "cmake" / "Dependencies.cmake",
        "set(CPM_SOURCE_CACHE\n"
        '    "${CMAKE_SOURCE_DIR}/3rdparty/cpm-cache"\n'
        '    CACHE PATH "CPM source cache")\n',
    )

    _write_if_missing(
        target_dir / "cmake" / "Options.cmake",
        'option(PROJECT_ENABLE_TESTS "Build native tests" ON)\n'
        'option(PROJECT_ENABLE_BENCHMARKS "Build benchmarks" OFF)\n'
        'option(PROJECT_ENABLE_PYTHON "Build Python bindings" OFF)\n',
    )


def create_project(template_root: Path, target_dir: Path, project_type: str) -> None:
    print(f"\nCreating {project_type.upper()} project at: {target_dir}")
    print("=" * 50)

    target_dir.mkdir(parents=True, exist_ok=True)

    # 1. Copy shared directories
    step = 1
    for dirname in _COPY_DIRS:
        src = template_root / dirname
        if src.is_dir():
            print(f"[{step}] Copying {dirname}/...")
            shutil.copytree(
                src,
                target_dir / dirname,
                dirs_exist_ok=True,
                ignore=_COPY_IGNORE,
            )
            step += 1

    # 2. Overlay language-specific files from templates/<language>/
    print(f"[{step}] Applying {project_type} template overlay...")
    language_dir = template_root / "templates" / project_type
    if not language_dir.is_dir():
        raise FileNotFoundError(
            f"Template directory missing: {language_dir}. "
            f"Expected templates/{project_type}/ at the template root."
        )

    for src_name, dst_name in _FILE_MAP[project_type]:
        src = language_dir / src_name
        if src.exists():
            dst = target_dir / dst_name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    step += 1

    # 3. Copy LICENSE if present
    license_file = template_root / "LICENSE"
    if license_file.exists():
        shutil.copy2(license_file, target_dir / "LICENSE")

    # 4. Create directory structure
    print(f"[{step}] Creating directory structure...")
    if project_type == "python":
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "tests").mkdir(exist_ok=True)
    elif project_type == "cpp":
        _create_cpm_layout(target_dir)
        (target_dir / "tests").mkdir(exist_ok=True)
        _write_if_missing(target_dir / "tests" / ".gitkeep", "")
        _write_if_missing(
            target_dir / "CMakeLists.txt",
            "cmake_minimum_required(VERSION 3.24)\n"
            "project(myproject VERSION 0.1.0 LANGUAGES CXX CUDA)\n\n"
            "include(cmake/Options.cmake)\n"
            "include(cmake/CPM.cmake)\n"
            "include(cmake/Dependencies.cmake)\n\n"
            "add_subdirectory(cpp)\n\n"
            "if(PROJECT_ENABLE_TESTS)\n"
            "  enable_testing()\n"
            "  add_subdirectory(tests)\n"
            "endif()\n\n"
            "if(PROJECT_ENABLE_BENCHMARKS)\n"
            "  add_subdirectory(benchmarks)\n"
            "endif()\n",
        )
        _write_if_missing(
            target_dir / "cpp" / "CMakeLists.txt",
            "add_library(myproject_core INTERFACE)\n"
            "target_compile_features(myproject_core INTERFACE cxx_std_17)\n"
            "target_include_directories(myproject_core INTERFACE\n"
            "  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>\n"
            "  $<INSTALL_INTERFACE:include>)\n",
        )
        _write_if_missing(target_dir / "tests" / "CMakeLists.txt", "")
    elif project_type == "hybrid":
        _create_cpm_layout(target_dir)
        for dirname in [
            "bindings/python",
            "python/myproject",
            "tests/cpp",
            "tests/python",
        ]:
            (target_dir / dirname).mkdir(parents=True, exist_ok=True)
        for keep in [
            "bindings/python/.gitkeep",
            "tests/cpp/.gitkeep",
            "tests/python/.gitkeep",
        ]:
            _write_if_missing(target_dir / keep, "")

        # Create pyproject.toml for scikit-build-core
        _write_if_missing(
            target_dir / "pyproject.toml",
            "[build-system]\n"
            "requires = [\n"
            '  "scikit-build-core",\n'
            '  "pybind11",\n'
            '  "ninja",\n'
            '  "cmake"\n'
            "]\n"
            'build-backend = "scikit_build_core.build"\n\n'
            "[project]\n"
            'name = "myproject"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.10"\n\n'
            "[tool.scikit-build]\n"
            'cmake.build-type = "RelWithDebInfo"\n'
            'build-dir = "build/{wheel_tag}"\n'
            'wheel.packages = ["python/myproject"]\n',
        )
        _write_if_missing(
            target_dir / "poetry.toml",
            "[virtualenvs]\nin-project = true\n",
        )

        # Create CMakeLists.txt for hybrid build
        _write_if_missing(
            target_dir / "CMakeLists.txt",
            "cmake_minimum_required(VERSION 3.24)\n"
            "project(myproject VERSION 0.1.0 LANGUAGES CXX CUDA)\n\n"
            "include(cmake/Options.cmake)\n"
            "include(cmake/CPM.cmake)\n"
            "include(cmake/Dependencies.cmake)\n\n"
            "add_subdirectory(cpp)\n\n"
            "if(PROJECT_ENABLE_PYTHON)\n"
            "  add_subdirectory(bindings/python)\n"
            "endif()\n\n"
            "if(PROJECT_ENABLE_TESTS)\n"
            "  enable_testing()\n"
            "  add_subdirectory(tests/cpp)\n"
            "endif()\n\n"
            "if(PROJECT_ENABLE_BENCHMARKS)\n"
            "  add_subdirectory(benchmarks)\n"
            "endif()\n",
        )
        _write_if_missing(
            target_dir / "cpp" / "CMakeLists.txt",
            "add_library(myproject_core INTERFACE)\n"
            "target_compile_features(myproject_core INTERFACE cxx_std_17)\n"
            "target_include_directories(myproject_core INTERFACE\n"
            "  $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>\n"
            "  $<INSTALL_INTERFACE:include>)\n",
        )
        _write_if_missing(
            target_dir / "bindings" / "python" / "CMakeLists.txt",
            "find_package(Python REQUIRED COMPONENTS Interpreter Development.Module)\n"
            "find_package(pybind11 CONFIG REQUIRED)\n\n"
            "pybind11_add_module(_core_ext bindings.cpp)\n"
            "target_link_libraries(_core_ext PRIVATE myproject_core)\n"
            "install(TARGETS _core_ext DESTINATION myproject)\n",
        )
        _write_if_missing(
            target_dir / "bindings" / "python" / "bindings.cpp",
            "#include <pybind11/pybind11.h>\n\n"
            "PYBIND11_MODULE(_core_ext, module) {\n"
            '  module.doc() = "myproject native bindings";\n'
            "}\n",
        )
        _write_if_missing(
            target_dir / "python" / "myproject" / "__init__.py",
            "from ._core_ext import *  # noqa: F403\n",
        )
        _write_if_missing(target_dir / "tests" / "cpp" / "CMakeLists.txt", "")
    step += 1

    # 5. Create README.md
    print(f"[{step}] Creating README.md...")
    (target_dir / "README.md").write_text(
        "# Project Name\n\nSee [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.\n"
    )
    step += 1

    # 6. Remove create-project skill (template-only)
    for create_skill in [
        target_dir / ".agents" / "skills" / "create-project",
        target_dir / ".claude" / "skills" / "create-project",
    ]:
        if create_skill.is_dir():
            shutil.rmtree(create_skill)

    # 6b. Remove language-specific extras that do not help the generated project.
    if project_type == "cpp":
        for path in [
            target_dir / ".claude" / "skills" / "python-env-setup",
            target_dir / ".agents" / "skills" / "python-env-setup",
        ]:
            if path.is_dir():
                shutil.rmtree(path)

        python_env_wrapper = target_dir / ".agents" / "bin" / "agent-python-env-setup"
        if python_env_wrapper.exists():
            python_env_wrapper.unlink()

    # For hybrid projects, keep all skills (both Python and C++ are needed)

    # 7. Git init + initial commit
    print(f"[{step}] Initializing git repository...")
    try:
        subprocess.run(["git", "init"], cwd=target_dir, capture_output=True, check=True)
        subprocess.run(
            ["git", "add", "."], cwd=target_dir, capture_output=True, check=True
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: initialise project from repo_template"],
            cwd=target_dir,
            capture_output=True,
            check=True,
        )
        print("  Git repository initialized with initial commit")
    except subprocess.CalledProcessError:
        print("  Warning: git init/commit failed")

    print()
    print("=" * 50)
    print("Done. Next steps:")
    print(f"  cd {target_dir}")
    print("  # Claude Code: run /init")
    print("  # Codex / Cursor / Cline: run .agents/bin/agent-init --platform codex")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 init.py <target_directory>")
        sys.exit(1)

    template_root = Path(__file__).resolve().parents[4]
    target_dir = Path(sys.argv[1]).resolve()

    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"Warning: {target_dir} already exists and is not empty")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted")
            sys.exit(0)

    project_type = prompt_project_type()
    create_project(template_root, target_dir, project_type)


if __name__ == "__main__":
    main()
