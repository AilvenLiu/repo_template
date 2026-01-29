#!/usr/bin/env python3
"""Add a dependency to the project."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from utils import DependencyManager, ProjectType


def ensure_virtual_environment(manager: DependencyManager) -> Path:
    """Ensure a virtual environment exists and return its path.

    CRITICAL: NEVER install packages globally or to system Python.
    This function enforces the use of virtual environments.
    """
    # Check for existing virtual environments
    venv_candidates = [".venv", "venv", ".virtualenv"]

    for venv_name in venv_candidates:
        venv_path = manager.repo_root / venv_name
        if venv_path.exists() and (venv_path / "bin" / "pip").exists():
            print(f"[OK] Found existing virtual environment: {venv_name}")
            return venv_path

    # No virtual environment found - create one
    print("[WARNING] No virtual environment found")
    print("[ACTION] Creating virtual environment at .venv")
    print("=" * 50)

    venv_path = manager.repo_root / ".venv"
    returncode, stdout, stderr = manager.run_command(["python3", "-m", "venv", ".venv"])

    if returncode != 0:
        print(f"[ERROR] Failed to create virtual environment")
        print(f"Error: {stderr}")
        print("\nPlease create a virtual environment manually:")
        print("  python3 -m venv .venv")
        print("  source .venv/bin/activate")
        sys.exit(1)

    print(f"[OK] Virtual environment created at .venv")
    return venv_path


def add_python_dependency(
    manager: DependencyManager, package: str, version: str = None
) -> None:
    """Add a Python dependency.

    CRITICAL: This function enforces virtual environment usage.
    NEVER installs packages globally or to system Python.
    """
    print(f"Adding Python dependency: {package}")
    print("-" * 50)

    # CRITICAL: Ensure virtual environment exists
    venv_path = ensure_virtual_environment(manager)
    pip_path = venv_path / "bin" / "pip"

    if not pip_path.exists():
        print(f"[ERROR] pip not found in virtual environment: {pip_path}")
        sys.exit(1)

    # Add to requirements.txt
    if manager.add_to_requirements_txt(package, version):
        print(f"[OK] Added {package} to requirements.txt")
    else:
        print(f"[INFO] {package} already in requirements.txt")

    # Install the package using virtual environment pip
    print(f"\nInstalling {package} in virtual environment...")
    cmd = [str(pip_path), "install", package]
    if version:
        cmd[-1] = f"{package}>={version}"

    returncode, stdout, stderr = manager.run_command(cmd)
    if returncode == 0:
        print(f"[OK] {package} installed successfully in virtual environment")
        print(f"[INFO] Virtual environment: {venv_path}")
    else:
        print(f"[ERROR] Failed to install {package}")
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
    """Add a C++/CUDA dependency.

    CRITICAL: This function enforces package manager usage (Conan/vcpkg).
    NEVER installs C++ libraries system-wide (apt, yum, brew).
    """
    print(f"Adding C++/CUDA dependency: {package}")
    print("-" * 50)

    # Check for package manager configuration
    conan_file = manager.repo_root / "conanfile.txt"
    vcpkg_file = manager.repo_root / "vcpkg.json"
    cmake_file = manager.repo_root / "CMakeLists.txt"

    has_package_manager = conan_file.exists() or vcpkg_file.exists()

    if not has_package_manager:
        print("[ERROR] No package manager configuration found")
        print("=" * 50)
        print("CRITICAL: NEVER install C++ libraries system-wide")
        print("          (apt, yum, brew, or manual installation)")
        print()
        print("Please set up a package manager first:")
        print()
        print("Option 1: Conan (Recommended)")
        print("  1. Install Conan: pip install conan")
        print("  2. Create conanfile.txt:")
        print("     [requires]")
        print()
        print("     [generators]")
        print("     CMakeDeps")
        print("     CMakeToolchain")
        print()
        print("Option 2: vcpkg")
        print("  1. Install vcpkg: git clone https://github.com/microsoft/vcpkg")
        print("  2. Create vcpkg.json:")
        print("     {")
        print('       "dependencies": []')
        print("     }")
        print()
        print("Then run this command again.")
        sys.exit(1)

    # Use Conan if available
    if conan_file.exists():
        if manager.add_to_conanfile_txt(package, version):
            print(f"[OK] Added {package} to conanfile.txt")
        else:
            print(f"[INFO] {package} already in conanfile.txt")

        # Run conan install
        print(f"\nInstalling {package} via Conan...")
        returncode, stdout, stderr = manager.run_command(
            ["conan", "install", ".", "--build=missing"]
        )
        if returncode == 0:
            print(f"[OK] Conan install successful")
        else:
            print(f"[ERROR] Conan install failed")
            print(f"Error: {stderr}")
            print("\nIf Conan is not installed:")
            print("  pip install conan")
            sys.exit(1)

    # Use vcpkg if available (and Conan is not)
    elif vcpkg_file.exists():
        print(f"[INFO] Using vcpkg for dependency management")
        print(f"[ACTION] Please add {package} to vcpkg.json manually")
        print(f"         Then run: vcpkg install")

    # Add to CMakeLists.txt
    if cmake_file.exists():
        if manager.add_to_cmake(package, version):
            print(f"[OK] Added find_package({package}) to CMakeLists.txt")
        else:
            print(f"[INFO] {package} already in CMakeLists.txt")

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