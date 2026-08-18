import datetime
import json
import os

import boto3

_credentials: None | dict[str, str] = None
_credentials_expiration: datetime.datetime | None = None
_CREDENTIAL_REFRESH_MARGIN = datetime.timedelta(minutes=20)


def _normalize_expiration(
    value: str | datetime.datetime,
) -> datetime.datetime:
    """Return an expiration timestamp as a timezone-aware UTC datetime."""
    if isinstance(value, str):
        value = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if value.tzinfo is None:
        value = value.replace(tzinfo=datetime.timezone.utc)
    return value.astimezone(datetime.timezone.utc)


def get_credentials(force_refresh: bool = False) -> dict[str, str]:
    global _credentials, _credentials_expiration
    refresh_deadline = (
        datetime.datetime.now(datetime.timezone.utc) + _CREDENTIAL_REFRESH_MARGIN
    )
    cache_is_valid = (
        _credentials is not None
        and _credentials_expiration is not None
        and refresh_deadline < _credentials_expiration
    )
    if cache_is_valid and not force_refresh:
        return _credentials

    sts = boto3.client("sts")
    res = sts.assume_role(
        RoleArn=os.environ["SamsaraFunctionExecRoleArn"],
        RoleSessionName=os.environ["SamsaraFunctionName"],
    )
    credentials = res["Credentials"]
    _credentials = {
        "aws_access_key_id": credentials["AccessKeyId"],
        "aws_secret_access_key": credentials["SecretAccessKey"],
        "aws_session_token": credentials["SessionToken"],
    }
    _credentials_expiration = _normalize_expiration(credentials["Expiration"])
    return _credentials


_secrets: None | dict[str, str] = None


def get_secrets(credentials: None | dict[str, str] = None) -> dict[str, str]:
    global _secrets
    if _secrets is not None:
        return _secrets

    if credentials is None:
        credentials = get_credentials()

    ssm = boto3.client("ssm", **credentials)

    res = ssm.get_parameter(
        Name=os.environ["SamsaraFunctionSecretsPath"], WithDecryption=True
    )

    secrets = {}
    value = res["Parameter"]["Value"]
    if value != "null":
        secrets = json.loads(value)

    _secrets = secrets
    return _secrets
