import sys
from pathlib import Path


def setup_additional_dependency_path(relative_path: str) -> None:
    """
    Add the relative_path directory to the Python path.
    This allows imports from the relative_path directory to work in the Function runtime.
    The relative_path should be relative to the placement of the samsarafn.py file.
    """
    file_dir = Path(__file__).parent.resolve()
    relative_path_dir = file_dir / relative_path

    if str(relative_path_dir) not in sys.path:
        sys.path.append(str(relative_path_dir))
