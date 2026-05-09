#!/usr/bin/env python3
"""Add a dependency to the project."""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Add common utilities to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'common'))
from check_session import check_session_initialized

# Check session initialization before proceeding
session_state = check_session_initialized('dependency')

from utils import DependencyManager, ProjectType, PythonProjectType


def ensure_python_version(manager: DependencyManager) -> str:
    """Ensure Python 3.10+ is available for Poetry.

    CRITICAL: Poetry MUST use Python 3.10+ to avoid version conflicts.

    Returns:
        Python executable path that meets requirements
    """
    meets_req, python_exec, version = manager.check_python_version(min_version=(3, 10))

    if not meets_req:
        print("[ERROR] Python 3.10+ is required for Poetry")
        print("=" * 50)
        print()
        if version != (0, 0):
            print(f"Current Python version: {version[0]}.{version[1]}")
            print()
        print("Poetry requires Python 3.10 or higher to ensure:")
        print("  - Modern dependency resolution")
        print("  - Compatibility with latest packages")
        print("  - Consistent virtual environment management")
        print()
        print("Please install Python 3.10+ using one of these methods:")
        print()
        print("Option 1: Using pyenv (Recommended)")
        print("  # Install pyenv")
        print("  curl https://pyenv.run | bash")
        print()
        print("  # Install Python 3.10+")
        print("  pyenv install 3.10")
        print("  pyenv global 3.10")
        print()
        print("Option 2: Using system package manager")
        print("  # macOS")
        print("  brew install python@3.10")
        print()
        print("  # Ubuntu/Debian")
        print("  sudo apt update")
        print("  sudo apt install python3.10 python3.10-venv")
        print()
        print("  # Fedora/RHEL")
        print("  sudo dnf install python3.10")
        print()
        print("Option 3: Download from python.org")
        print("  https://www.python.org/downloads/")
        print()
        print("After installation, verify:")
        print("  python3.10 --version")
        print()
        sys.exit(1)

    print(f"[OK] Using Python {version[0]}.{version[1]} ({python_exec})")
    return python_exec


def ensure_poetry_available(manager: DependencyManager) -> None:
    """Ensure Poetry is installed and available.

    CRITICAL: Poetry is the mandatory tool for Python dependency management.
    """
    if not manager.is_poetry_available():
        print("[ERROR] Poetry is not installed or not available in PATH")
        print("=" * 50)
        print()
        print("Poetry is MANDATORY for Python dependency management.")
        print()
        print("Install Poetry:")
        print("  curl -sSL https://install.python-poetry.org | python3 -")
        print()
        print("Or see: https://python-poetry.org/docs/#installation")
        print()
        sys.exit(1)

    # Check if there's an existing external venv
    is_in_project, venv_path = manager.check_poetry_venv_location()
    if venv_path and not is_in_project:
        print(f"[WARNING] Found external virtual environment at: {venv_path}")
        print("          Poetry should use in-project venvs (.venv)")
        print()
        print("[ACTION] Removing external venv and reconfiguring...")
        success, message = manager.remove_external_poetry_venv()
        if success:
            print(f"[OK] {message}")
        else:
            print(f"[WARNING] {message}")
            print("          You may need to manually remove it:")
            print(f"          poetry env remove --all")
        print()

    # Configure Poetry to use in-project virtualenvs
    success, message = manager.configure_poetry_in_project()
    if success:
        print(f"[OK] {message}")
    else:
        print(f"[WARNING] Could not configure Poetry for in-project venv: {message}")
        print("          Poetry may use centralized venv location")


def ensure_poetry_project(manager: DependencyManager, python_exec: str) -> None:
    """Ensure the project is initialised as a Poetry project.

    Args:
        python_exec: Python executable to use for Poetry environment
    """
    pyproject = manager.repo_root / "pyproject.toml"

    if not pyproject.exists():
        print("[WARNING] No pyproject.toml found")
        print("[ACTION] Initialising Poetry project...")
        print("=" * 50)

        success, message = manager.poetry_init(python_exec)
        if not success:
            print(f"[ERROR] Failed to initialise Poetry project")
            print(f"Error: {message}")
            print()
            print("Please initialise manually:")
            print(f"  {python_exec} -m poetry init --python=^3.10")
            sys.exit(1)

        print("[OK] Poetry project initialised")
        print()


def add_python_dependency_poetry(
    manager: DependencyManager, package: str, version: str = None, dev: bool = False
) -> None:
    """Add a Python dependency using Poetry.

    CRITICAL: This is the standard method for all Python projects.
    Poetry automatically manages virtual environments and lock files.
    """
    print(f"Adding Python dependency via Poetry: {package}")
    print("-" * 50)

    # Ensure Python 3.10+ is available
    python_exec = ensure_python_version(manager)

    # Ensure Poetry is available
    ensure_poetry_available(manager)

    # Ensure project is initialised
    ensure_poetry_project(manager, python_exec)

    # Add the package
    group_str = " (dev)" if dev else ""
    print(f"Installing {package}{group_str}...")

    success, message = manager.poetry_add(package, version, dev)

    if success:
        print(f"[OK] {package} installed successfully via Poetry")
        print()
        print("Poetry automatically updated:")
        print("  - pyproject.toml (dependency declaration)")
        print("  - poetry.lock (locked versions)")
        print()
        print("IMPORTANT: Commit BOTH files:")
        print("  git add pyproject.toml poetry.lock")
    else:
        print(f"[ERROR] Failed to install {package}")
        print(f"Error: {message}")
        print()
        print("Common issues:")
        print("  - Package name is incorrect")
        print("  - Version constraint is invalid")
        print("  - Network connectivity issues")
        print("  - Dependency conflicts")
        print()
        print("Try manually:")
        if dev:
            print(f"  poetry add --group dev {package}")
        else:
            print(f"  poetry add {package}")
        sys.exit(1)

    # Remind about README
    readme_path = manager.repo_root / "README.md"
    if readme_path.exists():
        print()
        print(f"REMINDER: Update README.md to document {package}")
        print("Add to Dependencies section:")
        if version:
            print(f"  - **{package}** (^{version}): [description]")
        else:
            print(f"  - **{package}**: [description]")


def add_python_dependency_trivial(
    manager: DependencyManager, package: str, version: str = None
) -> None:
    """Add a Python dependency for trivial projects (manual venv).

    WARNING: This is ONLY for trivial projects meeting strict criteria:
    - Single Python file or fewer than 3 files
    - Fewer than 3 dependencies total
    - No packaging or distribution requirements
    - No development dependencies needed
    """
    print(f"Adding Python dependency (trivial project): {package}")
    print("-" * 50)
    print()
    print("[WARNING] Using manual venv mode for trivial project")
    print("          Consider migrating to Poetry for better management")
    print()

    # Check for existing virtual environment
    venv_candidates = [".venv", "venv", ".virtualenv"]
    venv_path = None

    for venv_name in venv_candidates:
        candidate = manager.repo_root / venv_name
        if candidate.exists() and (candidate / "bin" / "pip").exists():
            venv_path = candidate
            print(f"[OK] Found existing virtual environment: {venv_name}")
            break

    if not venv_path:
        print("[WARNING] No virtual environment found")
        print("[ACTION] Creating virtual environment at .venv")
        print()

        venv_path = manager.repo_root / ".venv"
        returncode, stdout, stderr = manager.run_command(
            ["python3", "-m", "venv", ".venv"]
        )

        if returncode != 0:
            print(f"[ERROR] Failed to create virtual environment")
            print(f"Error: {stderr}")
            print()
            print("Please create manually:")
            print("  python3 -m venv .venv")
            print("  source .venv/bin/activate")
            sys.exit(1)

        print(f"[OK] Virtual environment created at .venv")

    pip_path = venv_path / "bin" / "pip"

    # Add to requirements.txt
    if manager.add_to_requirements_txt(package, version):
        print(f"[OK] Added {package} to requirements.txt")
    else:
        print(f"[INFO] {package} already in requirements.txt")

    # Install the package
    print(f"\nInstalling {package} in virtual environment...")
    cmd = [str(pip_path), "install", package]
    if version:
        cmd[-1] = f"{package}>={version}"

    returncode, stdout, stderr = manager.run_command(cmd)
    if returncode == 0:
        print(f"[OK] {package} installed successfully")
    else:
        print(f"[ERROR] Failed to install {package}")
        print(f"Error: {stderr}")
        sys.exit(1)

    # Remind about README
    readme_path = manager.repo_root / "README.md"
    if readme_path.exists():
        print()
        print(f"REMINDER: Update README.md to document {package}")
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

    # Remind about README
    readme_path = manager.repo_root / "README.md"
    if readme_path.exists():
        print()
        print(f"REMINDER: Update README.md to document {package}")
        print("Add to Dependencies section:")
        if version:
            print(f"  - {package} >= {version}")
        else:
            print(f"  - {package}")


def main():
    """Main entry point for add command."""
    if len(sys.argv) < 2:
        print("Usage: python3 add.py <package> [version] [--dev]")
        print()
        print("Options:")
        print("  --dev    Add as development dependency (Poetry only)")
        print()
        print("Examples:")
        print("  python3 add.py requests")
        print("  python3 add.py requests 2.31.0")
        print("  python3 add.py pytest --dev")
        print("  python3 add.py pytest 7.3.0 --dev")
        print("  python3 add.py Eigen 3.4  (C++)")
        sys.exit(1)

    # Parse arguments
    args = sys.argv[1:]
    dev = "--dev" in args
    if dev:
        args.remove("--dev")

    package = args[0]
    version = args[1] if len(args) > 1 else None

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
    if dev:
        print(f"Group: dev")
    print()

    # Add dependency based on project type
    if project_type == ProjectType.PYTHON:
        # Detect Python project type (Poetry vs trivial)
        py_type = manager.detect_python_project_type()

        if py_type == PythonProjectType.TRIVIAL:
            # Check if this is truly a trivial project
            print("[INFO] Detected trivial project (requirements.txt only)")
            print()

            if dev:
                print("[ERROR] Development dependencies require Poetry")
                print()
                print("Trivial projects do not support --dev flag.")
                print("Please migrate to Poetry:")
                print("  poetry init")
                print("  poetry add --group dev " + package)
                sys.exit(1)

            add_python_dependency_trivial(manager, package, version)
        else:
            # Default to Poetry (including UNKNOWN - will init Poetry)
            add_python_dependency_poetry(manager, package, version, dev)

    elif project_type == ProjectType.CPP:
        if dev:
            print("[WARNING] --dev flag ignored for C++/CUDA projects")
        add_cpp_dependency(manager, package, version)

    else:
        print("ERROR: Unknown project type")
        print("Could not detect Python or C++/CUDA project")
        print()
        print("For Python projects, ensure you have:")
        print("  - pyproject.toml (Poetry - recommended)")
        print("  - requirements.txt (trivial projects only)")
        print()
        print("For C++/CUDA projects, ensure you have:")
        print("  - CMakeLists.txt")
        print("  - conanfile.txt or vcpkg.json")
        sys.exit(1)

    print()
    print("Dependency added successfully!")
    print()
    print("Next steps:")
    print("1. Update README.md with dependency documentation")
    print("2. Run tests to verify compatibility")
    print("3. Commit changes to version control")
    if project_type == ProjectType.PYTHON:
        py_type = manager.detect_python_project_type()
        if py_type != PythonProjectType.TRIVIAL:
            print("   git add pyproject.toml poetry.lock <your-code>")


if __name__ == "__main__":
    main()
