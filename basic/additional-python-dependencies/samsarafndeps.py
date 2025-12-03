import sys
from pathlib import Path


def setup_additional_dependency_path(relative_path: str) -> None:
    """
    Add the relative_path directory to the Python path.
    This allows imports from the relative_path directory to work in the Function runtime.
    The relative_path should be relative to the placement of the samsarafn.py file.
    This is safe to use even if the relative_path does not exist.
    """
    file_dir = Path(__file__).parent.resolve()
    abs_path_dir = file_dir / relative_path

    if str(abs_path_dir) not in sys.path:
        sys.path.append(str(abs_path_dir))


# Automatically invoke, to apply on import
# This works better with linters
setup_additional_dependency_path("lib")
