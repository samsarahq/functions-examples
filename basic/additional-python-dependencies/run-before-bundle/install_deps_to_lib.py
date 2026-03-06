import shutil
import subprocess
import sys
from pathlib import Path


prod_python_version = "3.12"
suggested_platform = "manylinux2014_x86_64"


def install_dependencies_to_path_prod(
    dependency_path: str, requirements_file: str
) -> subprocess.CompletedProcess:
    """
    Install dependencies using pip-tools for production with platform targeting.

    This function performs the following steps:
    1. Installs pip-tools
    2. Uses pip-compile to resolve the complete dependency tree with versions
    2. Determines the appropriate platform tag AFTER compilation
    3. Installs all dependencies with platform-specific wheels

    Returns:
        CompletedProcess result
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    # Install pip-tools
    subprocess.run(["pip", "install", "pip-tools"], check=True)

    # Generate compiled requirements with pip-compile to resolve ALL dependencies
    # This is essential for accurate platform detection
    compiled_requirements = Path(requirements_file).with_suffix(".compiled.txt")
    print(f"Compiling requirements to {compiled_requirements}...")

    subprocess.run(
        [
            "pip-compile",
            requirements_file,
            "--output-file",
            str(compiled_requirements),
            "--verbose",
        ],
        check=True,
    )

    # Install with platform targeting
    print(f"Installing dependencies for platform {suggested_platform}...")

    result = subprocess.run(
        [
            "pip",
            "install",
            "-r",
            str(compiled_requirements),
            "--target",
            dependency_path,
            "--platform",
            suggested_platform,
            "--python-version",
            prod_python_version,
            "--only-binary=:all:",
            "--no-deps",
        ],
        check=True,
    )

    compiled_requirements.unlink()

    return result


def install_dependencies_to_path(
    dependency_path: str, requirements_file: str, is_prod_install: bool
) -> subprocess.CompletedProcess:
    """
    Install dependencies to the given path with pip using --target flag.
    Remove all files in the given path before installation.

    Returns:
        tuple: (CompletedProcess result, platform tag used or None for local)
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    if is_prod_install:
        # Production install - determines platform automatically
        return install_dependencies_to_path_prod(dependency_path, requirements_file)
    else:
        # Local development - simple installation
        result = subprocess.run(
            ["pip", "install", "-r", requirements_file, "--target", dependency_path],
            check=True,
        )
        return result


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
        print("Installing dependencies for production...")
        _ = install_dependencies_to_path(str(lib_dir), str(requirements_file), True)
        print(
            f"Prod dependencies installed to {lib_dir} with platform tag {suggested_platform}"
        )
    else:
        install_dependencies_to_path(str(lib_dir), str(requirements_file), False)
        print(f"Local development dependencies installed to {lib_dir}")

    clean_up_depedency_path(str(lib_dir), print_warnings=not is_prod_install)


if __name__ == "__main__":
    main()
