#!/usr/bin/env python3
"""Initialize a new project from the repo_template.

Copies the shared template tree (.ai/, .claude/, bin/, agent_roadmaps/)
verbatim, then overlays the language-specific files from
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
    print()
    while True:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "1":
            return "python"
        elif choice == "2":
            return "cpp"
        else:
            print("Invalid choice. Please enter 1 or 2.")


# Files to copy from templates/<language>/<src> to <target>/<dst>.
# (The source directory is templates/<language>/, the dst path is relative to
# the target project root.)
_FILE_MAP = {
    "python": [
        ("AGENTS.md", "AGENTS.md"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        (".gitignore", ".gitignore"),
        ("project.yml", ".ai/project.yml"),
        ("poetry.toml", "poetry.toml"),
    ],
    "cpp": [
        ("AGENTS.md", "AGENTS.md"),
        ("CLAUDE.md", "CLAUDE.md"),
        ("CONTRIBUTING.md", "CONTRIBUTING.md"),
        (".gitignore", ".gitignore"),
        ("project.yml", ".ai/project.yml"),
    ],
}

# Directories to copy verbatim
_COPY_DIRS = [".ai", ".claude", "agent_roadmaps", "bin"]
_COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store")


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
    else:
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "include").mkdir(exist_ok=True)
        (target_dir / "tests").mkdir(exist_ok=True)
        cmake = target_dir / "CMakeLists.txt"
        if not cmake.exists():
            cmake.write_text(
                'cmake_minimum_required(VERSION 3.20)\n'
                'project(MyProject VERSION 1.0.0 LANGUAGES CXX)\n\n'
                'set(CMAKE_CXX_STANDARD 17)\n'
                'set(CMAKE_CXX_STANDARD_REQUIRED ON)\n'
                'set(CMAKE_CXX_EXTENSIONS OFF)\n\n'
                '# Add your targets here\n'
            )
        conanfile = target_dir / "conanfile.txt"
        if not conanfile.exists():
            conanfile.write_text(
                "[requires]\n\n"
                "[generators]\n"
                "CMakeDeps\n"
                "CMakeToolchain\n"
            )
    step += 1

    # 5. Create README.md
    print(f"[{step}] Creating README.md...")
    (target_dir / "README.md").write_text(
        "# Project Name\n\nSee [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.\n"
    )
    step += 1

    # 6. Remove create-project skill (template-only)
    create_skill = target_dir / ".claude" / "skills" / "create-project"
    if create_skill.is_dir():
        shutil.rmtree(create_skill)

    # 6b. Remove language-specific extras that do not help the generated project.
    if project_type == "cpp":
        for path in [
            target_dir / ".claude" / "skills" / "python-env-setup",
            target_dir / ".ai" / "skills" / "python-env-setup",
        ]:
            if path.is_dir():
                shutil.rmtree(path)

        python_env_doc = target_dir / ".claude" / "docs" / "python-env-quick-reference.md"
        if python_env_doc.exists():
            python_env_doc.unlink()

        python_env_wrapper = target_dir / "bin" / "agent-python-env-setup"
        if python_env_wrapper.exists():
            python_env_wrapper.unlink()

    # 7. Git init + initial commit
    print(f"[{step}] Initializing git repository...")
    try:
        subprocess.run(["git", "init"], cwd=target_dir, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=target_dir, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "chore: initialise project from repo_template"],
            cwd=target_dir, capture_output=True, check=True,
        )
        print("  Git repository initialized with initial commit")
    except subprocess.CalledProcessError:
        print("  Warning: git init/commit failed")

    print()
    print("=" * 50)
    print("Done. Next steps:")
    print(f"  cd {target_dir}")
    print("  # Claude Code: run /init")
    print("  # Codex / Cursor / Cline: run bin/agent-init --platform codex")


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
