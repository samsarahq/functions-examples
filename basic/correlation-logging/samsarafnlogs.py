import json
import sys

_corr_id = "<not set up>"
_is_json_out = False
_log_level = "INFO"

_level_order = ["DEBUG", "INFO", "WARN", "ERROR", "CRITICAL"]


def setup_logger_once(params: dict[str, any], is_json_out=None, log_level=None):
    """
    Setup the Samsara Function logging package once in handler function using Event Parameters.

    Args:
        `params`: Samsara Function parameters
        `is_json_out`: Whether to log in JSON format. Defaults to None, if so reads from `SamsaraFunctionLoggerIsJsonOut` parameter.
        `log_level`: The log level to use. Defaults to None, if so reads from `SamsaraFunctionLoggerLevel` parameter.
    """
    global _corr_id
    _corr_id = params["SamsaraFunctionCorrelationId"]

    global _is_json_out
    _is_json_out = (
        is_json_out
        if is_json_out is not None
        else params.get("SamsaraFunctionLoggerIsJsonOut", "False").lower() == "true"
    )

    global _log_level
    _log_level = (
        log_level
        if log_level is not None
        else params.get("SamsaraFunctionLoggerLevel", "INFO")
    )


def log(*args, **kwargs):
    """
    Log a message. Outputs a one line string or JSON object depending on the setup configuration.

    Example:
    ```python
    log("Hello, world!", level="DEBUG")
    ```
    ```txt
    7f2f3fbd-c27c-40c2-8630-16860231e51e | DEBUG | Hello, world!
    ```
    ```json
    {"correlation_id": "7f2f3fbd-c27c-40c2-8630-16860231e51e", "level": "DEBUG", "message": "Hello, world!"}
    ```
    """
    level = "INFO"
    if "level" in kwargs:
        level = str(kwargs.pop("level")).upper()

    file = sys.stdout if level in ["INFO", "DEBUG"] else sys.stderr

    try:
        log_prio = _level_order.index(level)
        set_prio = _level_order.index(_log_level)
        should_log = log_prio >= set_prio
        if not should_log:
            return
    except ValueError:
        # invalid log level, just print regardless
        pass

    if _is_json_out:
        payload = {
            "correlation_id": _corr_id,
            "level": level,
        }

        message = [*args, *kwargs]
        if len(args) == 1 and len(kwargs) == 0:
            message = args[0]

        payload["message"] = message

        print(json.dumps(payload), file=file)
        return

    prefix = f"{_corr_id} | "
    if level != "INFO":
        prefix = f"{_corr_id} | {level} | "

    print(prefix, *args, **kwargs, file=file)
