import json
import os
import requests

from steps.samsarafnsecrets import get_secrets
from steps.samsarafnstorage import get_storage
from steps.utils import base_name_no_ext


def get_pending_media_retrieval_ids(storage):
    return list(
        map(
            base_name_no_ext,
            storage.list_keys(Prefix=f"{os.environ['SamsaraFunctionName']}/pending/"),
        )
    )


def handle(event):
    is_eu_region = bool(event.get("IsEuRegion", "false"))

    storage = get_storage()

    pending_media_retrieval_ids = get_pending_media_retrieval_ids(storage)
    print(
        f"Polling for {len(pending_media_retrieval_ids)} media retrievals",
        pending_media_retrieval_ids,
    )

    for retrieval_id in pending_media_retrieval_ids:
        response = get_media_retrieval(retrieval_id, is_eu_region)

        retrieval_status = response["data"]["media"][0]["status"]
        print(f"Retrieval {retrieval_id} status: {retrieval_status}")

        if retrieval_status == "available":
            image_url = response["data"]["media"][0]["urlInfo"]["url"]

            response = requests.get(image_url)
            storage.put(
                Key=f"{os.environ['SamsaraFunctionName']}/retrieved/{retrieval_id}.jpg",
                Body=response.content,
            )
            storage.delete(
                Key=f"{os.environ['SamsaraFunctionName']}/pending/{retrieval_id}.json",
            )
            print(f"Downloaded and dequeued {retrieval_id}")
            return

        storage.put(
            Key=f"{os.environ['SamsaraFunctionName']}/pending/{retrieval_id}.json",
            Body=json.dumps(response).encode("utf-8"),
        )


def get_media_retrieval(retrieval_id, is_eu_region=False):
    url = f"https://api.{'eu.' if is_eu_region else ''}samsara.com/cameras/media/retrieval?retrievalId={retrieval_id}"

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {get_secrets()['SAMSARA_API_KEY']}",
    }

    response = requests.get(url, headers=headers)

    if not response.ok:
        raise Exception(
            f"Failed to get media retrieval: {response.status_code}, {response.text}"
        )

    return response.json()
