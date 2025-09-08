import shutil
import subprocess
import sys
import json
import urllib.request
import urllib.error
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

prod_python_version = "3.12"


def load_supported_tags(tags_file: str = "supported-prod-tags.json") -> List[str]:
    """Load supported platform tags from JSON file."""
    tags_path = Path(__file__).parent / tags_file
    try:
        with open(tags_path, "r") as f:
            tags = json.load(f)
        print(f"Loaded {len(tags)} supported platform tags")
        return tags
    except FileNotFoundError:
        print(f"Error: Could not find {tags_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {tags_path}: {e}")
        sys.exit(1)


def resolve_all_dependencies(requirements_file: str) -> List[str]:
    """Resolve all dependencies including transitive ones using pip."""
    print("Resolving all dependencies (including transitive)...")

    # Create a temporary directory for the resolution
    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            # Use pip-tools to resolve dependencies if available, otherwise use pip
            try:
                # Try pip-compile first (from pip-tools)
                resolved_file = os.path.join(temp_dir, "resolved.txt")
                cmd = [
                    "pip-compile",
                    "--quiet",
                    "--output-file",
                    resolved_file,
                    requirements_file,
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

                with open(resolved_file, "r") as f:
                    lines = f.readlines()

            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback to pip install --dry-run if pip-compile is not available
                print("pip-compile not found, using pip install --dry-run...")
                cmd = [
                    "pip",
                    "install",
                    "--dry-run",
                    "--quiet",
                    "--report",
                    os.path.join(temp_dir, "report.json"),
                    "-r",
                    requirements_file,
                ]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Parse the JSON report
                with open(os.path.join(temp_dir, "report.json"), "r") as f:
                    report = json.load(f)

                lines = []
                for item in report.get("install", []):
                    metadata = item.get("metadata", {})
                    name = metadata.get("name", "")
                    version = metadata.get("version", "")
                    if name and version:
                        lines.append(f"{name}=={version}\n")

            # Parse the resolved dependencies
            packages = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    # Extract package name (handle both == and other operators)
                    if "==" in line:
                        package_name = line.split("==")[0].strip()
                    elif ">=" in line:
                        package_name = line.split(">=")[0].strip()
                    elif "<=" in line:
                        package_name = line.split("<=")[0].strip()
                    elif ">" in line:
                        package_name = line.split(">")[0].strip()
                    elif "<" in line:
                        package_name = line.split("<")[0].strip()
                    else:
                        package_name = line.strip()

                    if package_name:
                        packages.append(package_name)

            print(f"Resolved {len(packages)} total dependencies (including transitive)")
            return packages

        except subprocess.CalledProcessError as e:
            print(f"Error resolving dependencies: {e}")
            print(f"Command output: {e.stdout}")
            print(f"Command error: {e.stderr}")
            # Fallback to just the direct dependencies
            print("Falling back to direct dependencies only...")
            packages = []
            with open(requirements_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        packages.append(line)
            return packages


def parse_package_spec(package_spec: str) -> Tuple[str, Optional[str]]:
    """Parse package specification into name and version constraint."""
    if ">=" in package_spec:
        name, version = package_spec.split(">=", 1)
        return name.strip(), f">={version.strip()}"
    elif "==" in package_spec:
        name, version = package_spec.split("==", 1)
        return name.strip(), f"=={version.strip()}"
    elif ">" in package_spec:
        name, version = package_spec.split(">", 1)
        return name.strip(), f">{version.strip()}"
    else:
        return package_spec.strip(), None


def get_package_info(package_name: str) -> Optional[Dict[str, Any]]:
    """Fetch package information from PyPI JSON API."""
    url = f"https://pypi.org/pypi/{package_name}/json"
    try:
        print(f"Fetching package info for {package_name}...")
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"Package '{package_name}' not found on PyPI")
        else:
            print(f"HTTP error {e.code} while fetching {package_name}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error fetching package info for {package_name}: {e}")
        return None


def extract_platform_tags_from_filename(filename: str) -> List[str]:
    """Extract platform tags from wheel filename."""
    # Wheel filename format: {name}-{version}-{python tag}-{abi tag}-{platform tag}.whl
    if not filename.endswith(".whl"):
        return []

    parts = filename[:-4].split("-")  # Remove .whl extension
    if len(parts) < 5:
        return []

    # For packages with underscores or complex names, we need to find where the version ends
    # and the python tag begins. We'll work backwards from the end.
    python_tag = parts[-3]
    abi_tag = parts[-2]
    platform_part = parts[-1]

    # Handle complex platform tags that might have dots (like manylinux_2_17_x86_64.manylinux2014_x86_64)
    # Split by dots and create tags for each part
    platform_variants = platform_part.split(".")

    tags = []
    for platform in platform_variants:
        full_tag = f"{python_tag}-{abi_tag}-{platform}"
        tags.append(full_tag)

    # Also add the full complex tag as-is
    if len(platform_variants) > 1:
        full_complex_tag = f"{python_tag}-{abi_tag}-{platform_part}"
        tags.append(full_complex_tag)

    return tags


def check_compatibility(package_spec: str, supported_tags: List[str]) -> Dict[str, Any]:
    """
    Check if a package has compatible wheels for any supported platform tags.

    Args:
        package_spec: Package specification (e.g., "pydantic>=2.0.0")
        supported_tags: List of supported platform tags

    Returns:
        Dictionary with compatibility results
    """
    package_name, _ = parse_package_spec(package_spec)

    package_info = get_package_info(package_name)
    if not package_info:
        return {
            "package": package_spec,
            "compatible": False,
            "error": "Package not found or could not fetch info",
            "compatible_tags": [],
            "versions_checked": [],
        }

    compatible_tags = []
    versions_checked = []

    # Check only the latest version
    latest_version = package_info.get("info", {}).get("version")
    if not latest_version:
        return {
            "package": package_spec,
            "compatible": False,
            "error": "Could not determine latest version",
            "compatible_tags": [],
            "versions_checked": [],
        }
    releases = package_info.get("releases", {})
    versions_to_check = [latest_version] if latest_version in releases else []

    print(f"Checking {len(versions_to_check)} version(s) for {package_name}...")

    for version in versions_to_check:
        versions_checked.append(version)
        files = releases.get(version, [])

        print(f"  Version {version}: {len(files)} files")

        for file_info in files:
            filename = file_info.get("filename", "")
            if not filename.endswith(".whl"):
                continue

            file_tags = extract_platform_tags_from_filename(filename)

            for tag in file_tags:
                if tag in supported_tags:
                    compatible_tags.append(
                        {"version": version, "tag": tag, "filename": filename}
                    )
                    print(f"    ✓ Compatible: {filename} (tag: {tag})")

    return {
        "package": package_spec,
        "compatible": len(compatible_tags) > 0,
        "compatible_tags": compatible_tags,
        "versions_checked": versions_checked,
        "total_supported_tags": len(supported_tags),
    }


def find_best_platform_tag(
    compatible_tags: List[Dict[str, Any]], supported_tags: List[str]
) -> Optional[str]:
    """Find the best platform tag to use for pip install."""
    if not compatible_tags:
        return None

    # Prefer more specific tags over generic ones
    tag_priority = {
        "manylinux2014": 100,
        "manylinux_2_17": 90,
        "manylinux_2_28": 80,
        "manylinux1": 70,
        "linux": 60,
        "any": 10,
    }

    best_tag = None
    best_score = -1

    for combo in compatible_tags:
        tag = combo["tag"]
        score = 0

        # Score based on tag content
        for keyword, points in tag_priority.items():
            if keyword in tag:
                score += points
                break

        # Prefer tags that appear earlier in supported_tags (higher priority)
        try:
            tag_index = supported_tags.index(tag)
            score += (len(supported_tags) - tag_index) / len(supported_tags) * 50
        except ValueError:
            pass

        if score > best_score:
            best_score = score
            best_tag = tag

    return best_tag


def determine_best_platform_tag(requirements_file: str) -> str:
    """
    Determine the best platform tag for production by analyzing all dependencies.
    Returns the most restrictive platform tag needed by any dependency.
    """
    print("Analyzing dependencies to determine best platform tag...")

    # Load supported tags
    supported_tags = load_supported_tags("supported-prod-tags.json")

    # Resolve all dependencies
    packages = resolve_all_dependencies(requirements_file)

    # Check compatibility for all packages
    platform_specific_tags = []
    for package in packages:
        result = check_compatibility(package, supported_tags)
        if result["compatible"] and result["compatible_tags"]:
            best_tag = find_best_platform_tag(result["compatible_tags"], supported_tags)
            if best_tag and best_tag != "py3-none-any":
                # Extract just the platform part (e.g., "manylinux2014_x86_64" from "cp312-cp312-manylinux2014_x86_64")
                parts = best_tag.split("-")
                if len(parts) >= 3:
                    platform_part = parts[-1]
                    platform_specific_tags.append(platform_part)

    # If we found platform-specific tags, use the most restrictive one
    if platform_specific_tags:
        # Prefer manylinux2014 over other variants as it's more compatible
        for tag in platform_specific_tags:
            if "manylinux2014_x86_64" in tag:
                print(f"Selected platform tag: {tag}")
                return tag

        # Otherwise, use the first platform-specific tag found
        selected_tag = platform_specific_tags[0]
        print(f"Selected platform tag: {selected_tag}")
        return selected_tag

    return "py3-none-any"


def install_pip_tools():
    """Install pip-tools if not already installed."""
    try:
        subprocess.run(["pip-compile", "--version"], check=True, capture_output=True)
        print("pip-tools already installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Installing pip-tools...")
        subprocess.run(["pip", "install", "pip-tools"], check=True)


def install_dependencies_to_path_prod(
    dependency_path: str, requirements_file: str, platform: str, python_version: str
) -> subprocess.CompletedProcess:
    """
    Install dependencies using pip-tools for production with platform targeting.
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    # Install pip-tools first
    install_pip_tools()

    # Generate compiled requirements
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
    print(
        f"Installing dependencies for platform {platform} (Python {python_version})..."
    )
    result = subprocess.run(
        [
            "pip",
            "install",
            "-r",
            str(compiled_requirements),
            "--target",
            dependency_path,
            "--platform",
            platform,
            "--python-version",
            python_version,
            "--only-binary=:all:",
            "--no-deps",  # Don't install dependencies of dependencies since we already resolved them
        ],
        check=True,
    )

    # Clean up compiled requirements
    compiled_requirements.unlink()

    return result


def install_dependencies_to_path(
    dependency_path: str, requirements_file: str, platform: str | None = None
) -> subprocess.CompletedProcess:
    """
    Install dependencies to the given path with pip using --target flag.
    Remove all files in the given path before installation.
    """
    dep_path = Path(dependency_path)
    if dep_path.exists():
        shutil.rmtree(dep_path)

    if platform:
        return install_dependencies_to_path_prod(
            dependency_path, requirements_file, platform, prod_python_version
        )
    else:
        # Local development - simple installation
        return subprocess.run(
            ["pip", "install", "-r", requirements_file, "--target", dependency_path],
            check=True,
        )


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
        # Dynamically determine the best platform tag
        prod_platform = determine_best_platform_tag(str(requirements_file))
        print(f"Installing dependencies for production (platform: {prod_platform})...")
        install_dependencies_to_path(
            str(lib_dir), str(requirements_file), prod_platform
        )
        print(
            f"Prod dependencies installed to {lib_dir} with platform tag {prod_platform}"
        )
    else:
        install_dependencies_to_path(str(lib_dir), str(requirements_file))
        print("Local development dependencies installed to {lib_dir}")

    clean_up_depedency_path(str(lib_dir), print_warnings=not is_prod_install)


if __name__ == "__main__":
    main()
