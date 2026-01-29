#!/usr/bin/env python3
"""Initialize a new project from the repo_template."""

import shutil
import subprocess
import sys
from pathlib import Path


def prompt_project_type() -> str:
    """Prompt user for project type."""
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


def create_project(template_root: Path, target_dir: Path, project_type: str) -> None:
    """Create a new project from the template."""
    print(f"\nCreating {project_type.upper()} project at: {target_dir}")
    print("=" * 50)

    # Create target directory
    target_dir.mkdir(parents=True, exist_ok=True)

    # Copy .claude directory
    print("[1/8] Copying .claude directory...")
    shutil.copytree(
        template_root / ".claude",
        target_dir / ".claude",
        dirs_exist_ok=True,
    )

    # Copy agent_roadmaps directory
    print("[2/8] Copying agent_roadmaps directory...")
    shutil.copytree(
        template_root / "agent_roadmaps",
        target_dir / "agent_roadmaps",
        dirs_exist_ok=True,
    )

    # Copy and rename language-specific files
    print("[3/8] Copying language-specific files...")
    if project_type == "python":
        shutil.copy2(
            template_root / "CLAUDE_PYTHON.md",
            target_dir / "CLAUDE.md",
        )
        shutil.copy2(
            template_root / "CONTRIBUTING_PYTHON.md",
            target_dir / "CONTRIBUTING.md",
        )
        shutil.copy2(
            template_root / ".gitignore_python",
            target_dir / ".gitignore",
        )
    else:  # cpp
        shutil.copy2(
            template_root / "CLAUDE_CPP.md",
            target_dir / "CLAUDE.md",
        )
        shutil.copy2(
            template_root / "CONTRIBUTING_CPP.md",
            target_dir / "CONTRIBUTING.md",
        )
        shutil.copy2(
            template_root / ".gitignore_cpp",
            target_dir / ".gitignore",
        )

    # Create directory structure
    print("[4/8] Creating directory structure...")
    if project_type == "python":
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "tests").mkdir(exist_ok=True)
        # Create empty requirements.txt
        (target_dir / "requirements.txt").touch()
    else:  # cpp
        (target_dir / "src").mkdir(exist_ok=True)
        (target_dir / "include").mkdir(exist_ok=True)
        (target_dir / "tests").mkdir(exist_ok=True)
        # Create basic CMakeLists.txt
        cmake_content = """cmake_minimum_required(VERSION 3.20)
project(MyProject VERSION 1.0.0 LANGUAGES CXX)

# C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add your targets here
"""
        (target_dir / "CMakeLists.txt").write_text(cmake_content)

    # Create README.md
    print("[5/8] Creating README.md...")
    readme_content = f"""# Project Name

## Description

[Add project description here]

## Setup

"""
    if project_type == "python":
        readme_content += """### Python Project

1. Create virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run tests:
   ```bash
   pytest
   ```
"""
    else:  # cpp
        readme_content += """### C++/CUDA Project

1. Configure build:
   ```bash
   cmake -B build -DCMAKE_BUILD_TYPE=Release
   ```

2. Build:
   ```bash
   cmake --build build
   ```

3. Run tests:
   ```bash
   cd build && ctest
   ```
"""

    readme_content += """
## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

## License

[Add license information here]
"""
    (target_dir / "README.md").write_text(readme_content)

    # Initialize git repository
    print("[6/8] Initializing git repository...")
    try:
        subprocess.run(
            ["git", "init"],
            cwd=target_dir,
            capture_output=True,
            check=True,
        )
        print("  Git repository initialized")
    except subprocess.CalledProcessError:
        print("  Warning: Failed to initialize git repository")

    # Create initial commit
    print("[7/8] Creating initial commit...")
    try:
        subprocess.run(
            ["git", "add", "."],
            cwd=target_dir,
            capture_output=True,
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit from repo_template"],
            cwd=target_dir,
            capture_output=True,
            check=True,
        )
        print("  Initial commit created")
    except subprocess.CalledProcessError:
        print("  Warning: Failed to create initial commit")

    # Final instructions
    print("[8/8] Project created successfully!")
    print()
    print("=" * 50)
    print("Next steps:")
    print(f"1. cd {target_dir}")
    print("2. Run: /init (to load constraints)")
    if project_type == "python":
        print("3. Create virtual environment: python3 -m venv .venv")
        print("4. Activate: source .venv/bin/activate")
    else:
        print("3. Set up package manager (Conan or vcpkg)")
        print("4. Configure build: cmake -B build")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python3 init.py <target_directory>")
        print()
        print("Example:")
        print("  python3 init.py /path/to/new/project")
        sys.exit(1)

    # Get template root (3 levels up from this script)
    template_root = Path(__file__).parent.parent.parent.parent
    target_dir = Path(sys.argv[1]).resolve()

    # Check if target directory already has files
    if target_dir.exists() and any(target_dir.iterdir()):
        print(f"Warning: {target_dir} already exists and is not empty")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != "y":
            print("Aborted")
            sys.exit(0)

    # Prompt for project type
    project_type = prompt_project_type()

    # Create project
    # create_project(template_root, target_dir, project_type)


if __name__ == "__main__":
    main()
