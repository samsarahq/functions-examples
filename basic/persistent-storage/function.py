from samsarafnstorage import get_storage, get_database


def storage_example():
    print("\nStorage example:")
    storage = get_storage()

    list_objects_response = storage.list_objects()
    print(f"{list_objects_response=}")

    list_contents_response = storage.list_contents()
    print(f"{list_contents_response=}")

    list_keys_response = storage.list_keys()
    print(f"{list_keys_response=}")

    if len(list_contents_response) > 0:
        object = list_contents_response[-1]
        get_response = storage.get(Key=object["Key"])
        print(f"{get_response=}")

    put_response = storage.put(
        Key=f"test-{len(list_contents_response)}.csv", Body=b"col1,col2\nvalue1,value2"
    )
    print(f"{put_response=}")

    put_base64_response = storage.put_base64(
        Key=f"test-base64-{len(list_contents_response)}",
        Base64="SGVsbG8h",
    )
    print(f"{put_base64_response=}")

    get_body_base64_response = storage.get_body_base64(
        Key=f"test-base64-{len(list_contents_response)}",
    )
    print(f"{get_body_base64_response=}")

    if len(list_contents_response) > 0:
        object = list_contents_response[0]
        delete_response = storage.delete(Key=object["Key"])
        print(f"{delete_response=}")


def database_example():
    print("\nDatabase example:")
    database = get_database("my-feature")

    database.put("unique-id", "123")
    print(f"{database.get('unique-id')=}")

    database.put_dict(
        "other-unique-id",
        {
            "name": "object",
            "tags": ["descriptive"],
        },
    )
    print(f"{database.get_dict('other-unique-id')=}")

    print(f"{database.keys()=}")

    database.delete("unique-id")
    print(f"{database.get('unique-id')=}")


def main(_, __):
    storage_example()
    database_example()
