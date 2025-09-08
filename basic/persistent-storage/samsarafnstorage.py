import base64
import json
import os
import boto3
import botocore.exceptions


class Storage:
    """
    A multi-purpose object storage.
    Can be used to store files, images, etc.
    """

    def __init__(self, credentials: dict[str, str]):
        self.client = boto3.client("s3", **credentials)
        self.bucket = os.environ["SamsaraFunctionStorageName"]

    def put(self, Key: str, Body: bytes, **kwargs):
        """
        Insert or overwrite an object.
        Kwargs are passed to the underlying boto3.client('s3').put_object().
        Returns the original boto3 response.
        """
        return self.client.put_object(
            Bucket=self.bucket,
            Key=Key,
            Body=Body,
            **kwargs,
        )

    def put_base64(self, Key: str, Base64: str, **kwargs):
        """
        Insert or overwrite an object from a base64 encoded string.
        Object will be stored as bytes, not as a string.
        Kwargs are passed to the underlying `boto3.client('s3').put_object()`.
        Returns the original boto3 response.
        """
        return self.put(Key, Body=base64.b64decode(Base64), **kwargs)

    def get(self, Key: str, **kwargs):
        """
        Get an object with it's metadata.
        Kwargs are passed to the underlying `boto3.client('s3').get_object()`.
        Returns the original boto3 response.
        """
        return self.client.get_object(
            Bucket=self.bucket,
            Key=Key,
            **kwargs,
        )

    def get_body(self, Key: str, **kwargs) -> bytes:
        """
        Get an object's body.
        Returns bytes.
        Kwargs are passed to the underlying `boto3.client('s3').get_object()`.
        """
        return self.get(Key, **kwargs)["Body"].read()

    def get_body_base64(self, Key: str, **kwargs) -> str:
        """
        Get an object's body as a base64 encoded string.
        Expects the object to be stored as bytes.
        Kwargs are passed to the underlying `boto3.client('s3').get_object()`.
        """
        body = self.get_body(Key, **kwargs)
        return base64.b64encode(body).decode("utf-8")

    def delete(self, Key: str, **kwargs):
        """
        Delete an object.
        Kwargs are passed to the underlying `boto3.client('s3').delete_object()`.
        Returns the original boto3 response.
        """
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
        """
        List objects in the bucket with bucket and object metadata.
        Kwargs are passed to the underlying `boto3.client('s3').list_objects_v2()`.
        Returns the original boto3 response.
        """
        return self.client.list_objects_v2(
            Bucket=self.bucket,
            Prefix=Prefix,
            **kwargs,
        )

    def list_contents(
        self,
        Prefix: str = "",
        **kwargs,
    ):
        """
        List objects in the bucket with metadata.
        Kwargs are passed to the underlying `boto3.client('s3').list_objects_v2()`.
        Returns the `Contents` field of the original boto3 response.
        """
        return self.list_objects(
            Prefix=Prefix,
            **kwargs,
        ).get("Contents", [])

    def list_keys(
        self,
        Prefix: str = "",
        **kwargs,
    ) -> list[str]:
        """
        List object keys.
        Kwargs are passed to the underlying `boto3.client('s3').list_objects_v2()`.
        """
        return [
            obj.get("Key")
            for obj in self.list_contents(
                Prefix=Prefix,
                **kwargs,
            )
            if obj.get("Key")
        ]


class Database:
    """
    A key-value database that writes on each invocation.
    Can be used for cross-Function communication and synchronization.
    """

    def __init__(self, storage: Storage, namespace: str):
        self.storage = storage
        self.namespace = namespace

        self.namespace = self.namespace.strip(" /")

    def __key(self, key: str) -> str:
        return f"{self.namespace}/{key}"

    def keys(self) -> list[str]:
        return list(
            map(
                lambda key: key.removeprefix(self.namespace + "/"),
                self.storage.list_keys(Prefix=self.namespace),
            )
        )

    def get(self, key: str) -> str | None:
        try:
            return self.storage.get_body(Key=self.__key(key)).decode("utf-8")
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise e

    def get_dict(self, key: str) -> dict[str, str] | None:
        """
        Get a value from the database and parse it as a dictionary.
        Returns `None` if the key is not found.
        Raises `json.JSONDecodeError` if the value is not a valid JSON string.
        """
        value = self.get(key)
        if value is None:
            return None

        return json.loads(value)

    def put(self, key: str, value: str):
        return self.storage.put(Key=self.__key(key), Body=value.encode("utf-8"))

    def put_dict(self, key: str, value: dict[str, any]):
        return self.put(key, json.dumps(value))

    def delete(self, key: str):
        return self.storage.delete(Key=self.__key(key))


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


_databases: dict[str, Database] = {}


def get_database(namespace: str | None = None) -> Database:
    """
    Get a database instance.
    If `namespace` is `None`, the function name will be used.
    Namespace is used to prefix the storage keys used by the database.
    """
    if namespace is None:
        namespace = os.environ["SamsaraFunctionName"]

    global _databases
    if namespace in _databases:
        return _databases[namespace]

    _databases[namespace] = Database(get_storage(), namespace)
    return _databases[namespace]
