import shutil
import subprocess
import sys
from pathlib import Path


prod_python_version = "3.12"
suggested_platform = "manylinux2014_x86_64"


def install_pip_tools():
    """
    Install pip-tools with a compatible pip version for dependency compilation.

    WORKAROUND FOR PIP 25.x INCOMPATIBILITY:
    =========================================

    As of January 2025, there's a compatibility issue between pip-tools and pip 25.x:
    - pip 25.0+ removed the internal `InstallRequirement.use_pep517` attribute
    - pip-tools 7.5.1 (and earlier) depends on this attribute, causing AttributeError
    - pip-tools 8.x (which will fix this) is not yet released

    This function implements a temporary workaround:
    1. Detect the current pip version
    2. If pip 25.x is installed, temporarily downgrade to pip 24.3.1
    3. Install pip-tools (which works fine with pip 24.x)
    4. The calling function will restore pip 25.x after pip-compile completes

    This ensures pip-compile can successfully resolve platform-specific dependencies
    (like pydantic_core) which is critical for production Lambda deployments.

    Once pip-tools 8.x is released with pip 25.x compatibility, this workaround
    can be removed and replaced with: pip install --upgrade pip-tools>=8.0.0

    Returns:
        str: The original pip version string (e.g., "pip 25.3 from ...")
    """
    print("Installing pip-tools with compatible pip version...")

    # Save current pip version
    pip_version_result = subprocess.run(
        ["pip", "--version"], capture_output=True, text=True, check=True
    )
    current_pip = pip_version_result.stdout.strip()
    print(f"Current pip: {current_pip}")

    # Temporarily use pip 24.3.1 for compilation (last stable before 25.x)
    print("Temporarily using pip 24.3.1 for pip-tools compatibility...")
    subprocess.run(["pip", "install", "pip==24.3.1"], check=True, capture_output=True)

    # Now install pip-tools (7.5.1 works fine with pip 24.x)
    subprocess.run(["pip", "install", "pip-tools"], check=True)

    return current_pip


def install_dependencies_to_path_prod(
    dependency_path: str, requirements_file: str, python_version: str
) -> tuple[subprocess.CompletedProcess, str]:
    """
    Install dependencies using pip-tools for production with platform targeting.

    This function performs several critical steps in sequence:
    1. Temporarily downgrades pip if needed for pip-tools compatibility
    2. Uses pip-compile to resolve the complete dependency tree with versions
    3. Determines the appropriate platform tag AFTER compilation
    4. Restores pip to original version
    5. Installs all dependencies with platform-specific wheels

    Platform Detection Timing:
        Platform detection MUST happen after pip-compile because:
        - The original requirements.txt may only list top-level packages (e.g., "pydantic")
        - Platform-specific dependencies are often transitive (e.g., pydantic_core)
        - Only the compiled requirements file contains the full resolved dependency tree
        - Without full resolution, we can't detect if platform-specific binaries are needed

    Example: If requirements.txt has "pydantic", we need pip-compile to discover that
    it depends on "pydantic_core", which requires platform-specific compiled wheels.

    Fallback Behavior:
        If pip-compile fails, falls back to direct pip installation without
        pre-compilation, but platform detection will be less accurate.

    Returns:
        tuple: (CompletedProcess result, platform tag used for installation)
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    # Install pip-tools first (this may temporarily downgrade pip for compatibility)
    original_pip = install_pip_tools()

    # Generate compiled requirements with pip-compile to resolve ALL dependencies
    # This is essential for accurate platform detection
    compiled_requirements = Path(requirements_file).with_suffix(".compiled.txt")
    print(f"Compiling requirements to {compiled_requirements}...")

    try:
        subprocess.run(
            [
                "pip-compile",
                requirements_file,
                "--output-file",
                str(compiled_requirements),
                "--verbose",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        use_compiled = True
        print("Successfully compiled requirements with pip-compile")
    except subprocess.CalledProcessError as e:
        print(f"Warning: pip-compile failed: {e.stderr}")
        print("Falling back to direct pip installation without pre-compilation...")
        use_compiled = False

    print(f"Installing packages with suggested platform tag: {suggested_platform}")

    # Restore pip to original version if we downgraded it for pip-tools compatibility
    # Only restore after successful compilation to ensure pip-compile ran with compatible pip
    if use_compiled and "pip 25" in original_pip:
        print("Restoring original pip version...")
        # Upgrade back to latest pip (25.x)
        subprocess.run(
            ["pip", "install", "--upgrade", "pip"], check=True, capture_output=True
        )

    # Install with platform targeting
    print(
        f"Installing dependencies for platform {suggested_platform} (Python {python_version})..."
    )

    install_args = [
        "pip",
        "install",
        "-r",
        str(compiled_requirements) if use_compiled else requirements_file,
        "--target",
        dependency_path,
        "--platform",
        suggested_platform,
        "--python-version",
        python_version,
        "--only-binary=:all:",
    ]

    # Only add --no-deps if we pre-compiled (already resolved dependencies)
    if use_compiled:
        install_args.append("--no-deps")

    result = subprocess.run(install_args, check=True)

    # Clean up compiled requirements if it was created
    if use_compiled and compiled_requirements.exists():
        compiled_requirements.unlink()

    return result, suggested_platform


def install_dependencies_to_path(
    dependency_path: str, requirements_file: str, platform: str | None = None
) -> tuple[subprocess.CompletedProcess, str | None]:
    """
    Install dependencies to the given path with pip using --target flag.
    Remove all files in the given path before installation.

    Returns:
        tuple: (CompletedProcess result, platform tag used or None for local)
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    if platform:
        # Production install - determines platform automatically
        return install_dependencies_to_path_prod(
            dependency_path, requirements_file, prod_python_version
        )
    else:
        # Local development - simple installation
        result = subprocess.run(
            ["pip", "install", "-r", requirements_file, "--target", dependency_path],
            check=True,
        )
        return result, None


def clean_up_depedency_path(dependency_path: str, print_warnings: bool = True):
    """
    Remove files that are not needed in the dependency directory:
    - binary files
    - dist-info files (leaves METADATA)
    - egg-info files (leaves PKG-INFO)
    """
    dep_path = Path(dependency_path)
    bin_dir = dep_path / "bin"
    if bin_dir.exists():
        shutil.rmtree(bin_dir)

    for dist_info in dep_path.glob("*.dist-info"):
        for file_path in dist_info.iterdir():
            if file_path.name.endswith("WHEEL"):
                platform_tag = get_package_platform_tag(str(file_path))
                if platform_tag != "py3-none-any":
                    package_name = dist_info.name.split("-")[0]
                    if print_warnings:
                        print_error(
                            f"platform-warning: package '{package_name}' is not platform-agnostic (wheel tag '{platform_tag}'). You can proceed with testing it in the simulator, but for production you need to run the dependency installing script on a machine with x86_64 architecture. See the template README for more details."
                        )

            if not file_path.name.endswith("METADATA"):
                remove(str(file_path))

    for egg_info in dep_path.glob("*.egg-info"):
        for file_path in egg_info.iterdir():
            if not file_path.name.endswith("PKG-INFO"):
                remove(str(file_path))


def print_error(message: str):
    print(
        f"\033[31m{message}\033[0m",
        file=sys.stderr,
    )


def remove(path: str):
    path_obj = Path(path)
    if path_obj.is_file():
        path_obj.unlink()
    else:
        shutil.rmtree(path_obj)


def get_package_platform_tag(wheel_file_path: str):
    wheel_file_lines = []
    with Path(wheel_file_path).open("r") as f:
        wheel_file_lines = f.readlines()

    for line in wheel_file_lines:
        line = line.strip()
        if line.startswith("Tag: "):
            # Extract the part after "Tag: "
            return line[5:]  # len("Tag: ") = 5

    # Return None if no Tag line was found
    return None


def main():
    requirements_file = Path(__file__).parent / "requirements.txt"
    lib_dir = Path(__file__).parent.parent / "lib"

    is_prod_install = len(sys.argv) > 1 and sys.argv[1] == "prod"

    if is_prod_install:
        # Install for production - platform tag will be determined after compilation
        print("Installing dependencies for production...")
        _, prod_platform = install_dependencies_to_path(
            str(lib_dir), str(requirements_file), "prod"
        )
        print(
            f"Prod dependencies installed to {lib_dir} with platform tag {prod_platform}"
        )
    else:
        install_dependencies_to_path(str(lib_dir), str(requirements_file))
        print(f"Local development dependencies installed to {lib_dir}")

    clean_up_depedency_path(str(lib_dir), print_warnings=not is_prod_install)


if __name__ == "__main__":
    main()
