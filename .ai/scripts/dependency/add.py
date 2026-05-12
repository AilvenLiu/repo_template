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

from utils import DependencyManager, ProjectType, PythonProjectType, BuildSystem


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


def add_cpp_dependency_cmake(
    manager: DependencyManager, package: str, version: str = None
) -> None:
    """Add a C++/CUDA dependency using CMake with Conan/vcpkg.

    CRITICAL: This function enforces package manager usage (Conan/vcpkg).
    NEVER installs C++ libraries system-wide (apt, yum, brew).
    """
    print(f"Adding C++/CUDA dependency (CMake): {package}")
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


def add_dependency_scikit_build(manager: DependencyManager, package: str, version: str | None, dev: bool) -> None:
    """Add dependency to scikit-build-core project.

    scikit-build-core projects use pyproject.toml for Python dependencies.
    Dependencies are added directly to the [project.dependencies] or
    [project.optional-dependencies.dev] sections.
    """
    print(f"Adding Python dependency to scikit-build-core project: {package}")
    print("-" * 50)

    pyproject_path = manager.repo_root / "pyproject.toml"
    if not pyproject_path.exists():
        print("[ERROR] No pyproject.toml found")
        print()
        print("scikit-build-core projects require pyproject.toml")
        sys.exit(1)

    # Construct dependency string
    if version:
        dep_string = f'"{package}>={version}"'
    else:
        dep_string = f'"{package}"'

    # Read the file
    with open(pyproject_path, "r") as f:
        lines = f.readlines()

    # Find the appropriate section and add dependency
    modified = False
    in_dependencies = False
    in_optional_dev = False
    dependencies_line = -1
    optional_dev_line = -1

    for i, line in enumerate(lines):
        if line.strip() == "dependencies = [":
            in_dependencies = True
            dependencies_line = i
        elif line.strip() == "[project.optional-dependencies]":
            in_optional_dev = False
        elif line.strip() == "dev = [":
            in_optional_dev = True
            optional_dev_line = i
        elif line.strip().startswith("[") and (in_dependencies or in_optional_dev):
            in_dependencies = False
            in_optional_dev = False

    if not dev and dependencies_line >= 0:
        # Add to dependencies
        # Find the closing bracket
        for i in range(dependencies_line + 1, len(lines)):
            if "]" in lines[i]:
                # Insert before the closing bracket
                indent = "    "
                lines.insert(i, f'{indent}{dep_string},\n')
                modified = True
                print(f"[OK] Added {package} to [project.dependencies]")
                break
    elif dev and optional_dev_line >= 0:
        # Add to optional-dependencies.dev
        for i in range(optional_dev_line + 1, len(lines)):
            if "]" in lines[i]:
                indent = "    "
                lines.insert(i, f'{indent}{dep_string},\n')
                modified = True
                print(f"[OK] Added {package} to [project.optional-dependencies.dev]")
                break
    else:
        print(f"[ERROR] Could not find appropriate section in pyproject.toml")
        print()
        print("Please add manually:")
        if dev:
            print(f'  [project.optional-dependencies]')
            print(f'  dev = ["{package}"]')
        else:
            print(f'  dependencies = ["{package}"]')
        sys.exit(1)

    if modified:
        # Write back
        with open(pyproject_path, "w") as f:
            f.writelines(lines)

        print()
        print("Updated pyproject.toml")
        print()
        print("IMPORTANT: Commit the file:")
        print("  git add pyproject.toml")
        print()
        print("To install the dependency:")
        print("  pip install -e .")
    else:
        print(f"[INFO] {package} may already be present or section not found")
        sys.exit(1)


def add_dependency_scikit_build_stub(package: str) -> None:
    """Stub for scikit-build dependency management (not yet implemented)."""
    print(f"[ERROR] scikit-build dependency management not yet implemented")
    print("=" * 50)
    print()
    print("scikit-build projects use a hybrid Python/C++ dependency model:")
    print("  - Python dependencies: managed via Poetry/pip")
    print("  - C++ dependencies: managed via CMake/Conan")
    print()
    print("This build system will be implemented in Phase 2.")
    print()
    print("For now, please add dependencies manually:")
    print("  - Python packages: edit pyproject.toml")
    print("  - C++ libraries: edit conanfile.txt or CMakeLists.txt")
    print()
    print("See: docs/architecture/decisions/002-six-axis-project-profile.md")
    print("Roadmap: agent_roadmaps/phase-2-build-system-expansion/")
    sys.exit(1)


def add_dependency_bazel_stub(package: str) -> None:
    """Stub for Bazel dependency management (not yet implemented)."""
    print(f"[ERROR] Bazel dependency management not yet implemented")
    print("=" * 50)
    print()
    print("Bazel projects use WORKSPACE and BUILD files for dependencies.")
    print()
    print("This build system will be implemented in Phase 2.")
    print()
    print("For now, please add dependencies manually:")
    print("  - Edit WORKSPACE file")
    print("  - Add http_archive or git_repository rules")
    print()
    print("See: docs/architecture/decisions/002-six-axis-project-profile.md")
    print("Roadmap: agent_roadmaps/phase-2-build-system-expansion/")
    sys.exit(1)


def add_dependency_mixed_stub(package: str) -> None:
    """Stub for mixed build system dependency management (not yet implemented)."""
    print(f"[ERROR] Mixed build system dependency management not yet implemented")
    print("=" * 50)
    print()
    print("Mixed build systems combine multiple dependency backends.")
    print()
    print("This build system will be implemented in Phase 2.")
    print()
    print("For now, please add dependencies manually to the appropriate file:")
    print("  - Python: pyproject.toml or requirements.txt")
    print("  - C++: conanfile.txt or CMakeLists.txt")
    print("  - System: document in README.md")
    print()
    print("See: docs/architecture/decisions/002-six-axis-project-profile.md")
    print("Roadmap: agent_roadmaps/phase-2-build-system-expansion/")
    sys.exit(1)


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

    # Detect project profile and build system
    profile = manager.detect_project_profile()
    build_system = profile.build_system

    print("Dependency Management")
    print("=" * 50)
    print(f"Build System: {build_system.value}")
    print(f"Package: {package}")
    if version:
        print(f"Version: {version}")
    if dev:
        print(f"Group: dev")
    print()

    # Add dependency based on build system
    if build_system == BuildSystem.POETRY:
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

    elif build_system == BuildSystem.CMAKE:
        if dev:
            print("[WARNING] --dev flag ignored for C++/CUDA projects")
        add_cpp_dependency_cmake(manager, package, version)

    elif build_system in (BuildSystem.SCIKIT_BUILD, BuildSystem.SCIKIT_BUILD_CORE):
        if dev:
            print("[INFO] Adding to dev dependencies")
        add_dependency_scikit_build(manager, package, version, dev)

    elif build_system == BuildSystem.BAZEL:
        add_dependency_bazel_stub(package)

    elif build_system == BuildSystem.MIXED:
        add_dependency_mixed_stub(package)

    else:
        print("ERROR: Unknown build system")
        print("Could not detect project build system")
        print()
        print("Supported build systems:")
        print("  - poetry (Python with Poetry)")
        print("  - cmake (C++/CUDA with CMake)")
        print("  - scikit-build (Python/C++ hybrid)")
        print("  - bazel (Bazel build system)")
        print("  - mixed (multiple build systems)")
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
    if build_system == BuildSystem.POETRY:
        py_type = manager.detect_python_project_type()
        if py_type != PythonProjectType.TRIVIAL:
            print("   git add pyproject.toml poetry.lock <your-code>")


if __name__ == "__main__":
    main()
