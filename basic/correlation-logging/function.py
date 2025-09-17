from samsarafnlogs import setup_logger_once, log

counter = 0


def main(params, _):
    setup_logger_once(params)

    log("Whoops!", level="error")

    # default logging
    do_work()

    # json logging
    params_with_json_setting = {
        **params,
        "SamsaraFunctionLoggerIsJsonOut": "true",
    }
    setup_logger_once(params_with_json_setting)
    do_work()

    # custom log level
    params_with_custom_level = {
        **params,
        "SamsaraFunctionLoggerLevel": "DEBUG",
    }
    setup_logger_once(params_with_custom_level)
    do_work()


def do_work():
    global counter
    counter += 1

    log(f"Hello, {counter}!")
    log({"message": "Shh!", "counter": counter}, level="debug")
