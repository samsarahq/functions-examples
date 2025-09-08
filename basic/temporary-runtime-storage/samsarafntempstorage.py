import os
from pathlib import Path


def temp_storage_path() -> Path:
    return Path(os.environ["SamsaraFunctionTempStoragePath"])
