import os
import boto3
import json


_credentials: None | dict[str, str] = None


def get_credentials(force_refresh=False) -> dict[str, str]:
    global _credentials
    if _credentials is not None and not force_refresh:
        return _credentials

    sts = boto3.client("sts")
    res = sts.assume_role(
        RoleArn=os.environ["SamsaraFunctionExecRoleArn"],
        RoleSessionName=os.environ["SamsaraFunctionName"],
    )
    _credentials = {
        "aws_access_key_id": res["Credentials"]["AccessKeyId"],
        "aws_secret_access_key": res["Credentials"]["SecretAccessKey"],
        "aws_session_token": res["Credentials"]["SessionToken"],
    }
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
