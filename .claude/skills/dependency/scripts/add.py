#!/usr/bin/env python3
"""Add a dependency to the project."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import DependencyManager, ProjectType


def add_python_dependency(
    manager: DependencyManager, package: str, version: str = None
) -> None:
    """Add a Python dependency."""
    print(f"Adding Python dependency: {package}")
    print("-" * 50)

    # Add to requirements.txt
    if manager.add_to_requirements_txt(package, version):
        print(f"[✓] Added {package} to requirements.txt")
    else:
        print(f"[!] {package} already in requirements.txt")

    # Install the package
    print(f"\nInstalling {package}...")
    cmd = ["pip3", "install", package]
    if version:
        cmd[-1] = f"{package}>={version}"

    returncode, stdout, stderr = manager.run_command(cmd)
    if returncode == 0:
        print(f"[✓] {package} installed successfully")
    else:
        print(f"[✗] Failed to install {package}")
        print(f"Error: {stderr}")
        sys.exit(1)

    # Update README.md
    readme_path = manager.repo_root / "README.md"
    if readme_path.exists():
        print(f"\nREMINDER: Update README.md to document {package}")
        print("Add to Dependencies section:")
        if version:
            print(f"  - {package} >= {version}")
        else:
            print(f"  - {package}")


def add_cpp_dependency(
    manager: DependencyManager, package: str, version: str = None
) -> None:
    """Add a C++/CUDA dependency."""
    print(f"Adding C++/CUDA dependency: {package}")
    print("-" * 50)

    # Check for conanfile.txt first
    conan_file = manager.repo_root / "conanfile.txt"
    if conan_file.exists():
        if manager.add_to_conanfile_txt(package, version):
            print(f"[✓] Added {package} to conanfile.txt")
        else:
            print(f"[!] {package} already in conanfile.txt")

        # Run conan install
        print(f"\nInstalling {package} via Conan...")
        returncode, stdout, stderr = manager.run_command(
            ["conan", "install", ".", "--build=missing"]
        )
        if returncode == 0:
            print(f"[✓] Conan install successful")
        else:
            print(f"[✗] Conan install failed")
            print(f"Error: {stderr}")

    # Add to CMakeLists.txt
    cmake_file = manager.repo_root / "CMakeLists.txt"
    if cmake_file.exists():
        if manager.add_to_cmake(package, version):
            print(f"[✓] Added find_package({package}) to CMakeLists.txt")
        else:
            print(f"[!] {package} already in CMakeLists.txt")

    # Update README.md
    readme_path = manager.repo_root / "README.md"
    if readme_path.exists():
        print(f"\nREMINDER: Update README.md to document {package}")
        print("Add to Dependencies section:")
        if version:
            print(f"  - {package} >= {version}")
        else:
            print(f"  - {package}")


def main():
    """Main entry point for add command."""
    if len(sys.argv) < 2:
        print("Usage: python3 add.py <package> [version]")
        print()
        print("Examples:")
        print("  python3 add.py requests")
        print("  python3 add.py requests 2.31.0")
        print("  python3 add.py Eigen 3.4")
        sys.exit(1)

    package = sys.argv[1]
    version = sys.argv[2] if len(sys.argv) > 2 else None

    repo_root = Path.cwd()
    manager = DependencyManager(repo_root)

    # Detect project type
    project_type = manager.detect_project_type()

    print("Dependency Management")
    print("=" * 50)
    print(f"Project Type: {project_type.value}")
    print(f"Package: {package}")
    if version:
        print(f"Version: {version}")
    print()

    # Add dependency
    if project_type == ProjectType.PYTHON:
        add_python_dependency(manager, package, version)
    elif project_type == ProjectType.CPP_CUDA:
        add_cpp_dependency(manager, package, version)
    else:
        print("ERROR: Unknown project type")
        print("Could not detect Python or C++/CUDA project")
        sys.exit(1)

    print()
    print("Dependency added successfully!")
    print()
    print("Next steps:")
    print("1. Update README.md with dependency documentation")
    print("2. Run tests to verify compatibility")
    print("3. Commit changes to version control")


if __name__ == "__main__":
    main()