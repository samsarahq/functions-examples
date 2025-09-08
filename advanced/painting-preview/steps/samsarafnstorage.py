import base64
import json
import os
import boto3


class Storage:
    """
    A multi-purpose object storage.
    Can be used to store files, images, etc.
    """

    def __init__(self, credentials: dict[str, str]):
        self.client = boto3.client("s3", **credentials)
        self.bucket = os.environ["SamsaraFunctionStorageName"]

    def put(self, Key: str, Body: bytes, **kwargs):
        return self.client.put_object(
            Bucket=self.bucket,
            Key=Key,
            Body=Body,
            **kwargs,
        )

    def put_base64(self, Key: str, Base64: str, **kwargs):
        return self.put(Key, Body=base64.b64decode(Base64), **kwargs)

    def get(self, Key: str, **kwargs):
        return self.client.get_object(
            Bucket=self.bucket,
            Key=Key,
            **kwargs,
        )

    def get_body(self, Key: str, **kwargs) -> bytes:
        return self.get(Key, **kwargs)["Body"].read()

    def get_body_base64(self, Key: str, **kwargs) -> str:
        body = self.get_body(Key, **kwargs)
        return base64.b64encode(body).decode("utf-8")

    def delete(self, Key: str, **kwargs):
        return self.client.delete_object(
            Bucket=self.bucket,
            Key=Key,
            **kwargs,
        )

    def list_objects(
        self,
        Prefix: str = "",
        **kwargs,
    ):
        return self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=Prefix,
            **kwargs,
        )

    def list_contents(
        self,
        Prefix: str = "",
        **kwargs,
    ) -> list[str]:
        return self.list_objects(
            Prefix=Prefix,
            **kwargs,
        ).get("Contents", [])

    def list_keys(
        self,
        Prefix: str = "",
        **kwargs,
    ) -> list[str]:
        return [
            obj.get("Key")
            for obj in self.list_contents(
                Prefix=Prefix,
                **kwargs,
            )
            if obj.get("Key")
        ]


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


_storage: None | Storage = None


def get_storage() -> Storage:
    global _storage
    if _storage is not None:
        return _storage

    _storage = Storage(get_credentials())
    return _storage


class Database:
    """
    A key-value database that writes on each invocation.
    Can be used for cross-Function communication and synchronization.
    """

    def __init__(self, storage: Storage, namespace: str):
        self.storage = storage
        self.namespace = namespace

    def __key(self, id: str) -> str:
        return f"{self.namespace}/{id}"

    def get(self, id: str) -> str:
        return self.storage.get_body(Key=self.__key(id)).decode("utf-8")

    def delete(self, id: str):
        self.storage.delete(Key=self.__key(id))

    def get_dict(self, id: str) -> dict[str, str]:
        return json.loads(self.get(id))

    def put(self, id: str, value: str):
        self.storage.put(Key=self.__key(id), Body=value.encode("utf-8"))

    def put_dict(self, id: str, value: dict[str, str]):
        self.storage.put(Key=self.__key(id), Body=json.dumps(value).encode("utf-8"))


_databases: dict[str, Database] = {}


def get_database(namespace: str) -> Database:
    global _databases
    if namespace in _databases:
        return _databases[namespace]

    _databases[namespace] = Database(get_storage(), namespace)
    return _databases[namespace]
