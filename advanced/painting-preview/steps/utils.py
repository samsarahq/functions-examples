import datetime


def timestamp_to_datetime(timestamp_ms: int) -> datetime.datetime:
    """Convert a timestamp in milliseconds to a datetime object in UTC timezone"""
    return datetime.datetime.fromtimestamp(
        timestamp_ms / 1000, tz=datetime.timezone.utc
    )


def base_name_no_ext(key: str) -> str:
    return key.split("/")[-1].split(".")[0]
