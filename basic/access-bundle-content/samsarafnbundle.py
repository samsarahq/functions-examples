import os
from pathlib import Path


def bundle_path() -> Path:
    return Path(os.environ["SamsaraFunctionCodePath"])
