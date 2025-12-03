# Add these two lines to load Functions shims
import samsarafndeps  # noqa pyright: ignore[reportUnusedImport] autoload vendored packages
from samsarafnsecrets import get_secrets, apply_to_env

# Part of the legacy dependencies, with architecture targeting that need special vendoring
from pydantic import BaseModel
import os


class User(BaseModel):
    id: int
    name: str


# Do this to propagate the secrets to the Python process environment
apply_to_env(get_secrets())


# Write a short adapter to map Function params to the legacy API
def function_entrypoint(_params, _context):
    legacy_args = {"id": _params.get("id") or 1, "name": "Alice"}
    do_the_thing(legacy_args)


# Keep legacy code as is! Unless you're relying on file operations.
# In that case you need to adapt the code to use the Function storage, 
# or write only the the ephemeral volume, with the path to it readable 
# from the `SamsaraFunctionTempStoragePath` environment variable.
# See `basic/temporary-runtime-storage` for more details on that.
def do_the_thing(args):
    print("Doing the thing")
    user = User(**args)
    api_submit(user.model_dump())


def api_submit(payload: dict):
    print(f"Submitting payload {payload} through the API...")
    # simulate credential accessing through the environment
    _ = os.environ["SAMSARA_API_KEY"]


# end of legacy code
