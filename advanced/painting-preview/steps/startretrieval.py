import json
import os
import datetime

import requests

from steps.samsarafnsecrets import get_secrets
from steps.samsarafnstorage import get_storage
from steps.utils import timestamp_to_datetime


def handle(event):
    alert_at = int(
        event.get(
            "alertIncidentTime",
            # shifting by function invocation time overhead (-10s)
            str(int(datetime.datetime.now().timestamp() - 10) * 1000),
        )
    )
    is_eu_region = bool(event.get("IsEuRegion", "false"))

    # shifting by camera button reaction time (+12s)
    capture_at = timestamp_to_datetime(alert_at) + datetime.timedelta(seconds=12)
    asset_id = event["assetId"]

    response = create_media_retrieval(capture_at, asset_id, is_eu_region)
    media_retrieval_id = response["data"]["retrievalId"]

    storage = get_storage()
    storage.put(
        Key=f"{os.environ['SamsaraFunctionName']}/pending/{media_retrieval_id}.json",
        Body=json.dumps(response).encode("utf-8"),
    )
    print(f"Enqueued retrieval for media {media_retrieval_id}")


def create_media_retrieval(capture_at, asset_id, is_eu_region=False):
    url = f"https://api.{'eu.' if is_eu_region else ''}samsara.com/cameras/media/retrieval"

    payload = {
        "startTime": capture_at.isoformat(),
        "endTime": capture_at.isoformat(),
        "inputs": ["dashcamRoadFacing"],
        "mediaType": "image",
        "vehicleId": asset_id,
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {get_secrets()['SAMSARA_API_KEY']}",
    }

    response = requests.post(url, json=payload, headers=headers)

    if not response.ok:
        raise Exception(
            f"Failed to create media retrieval: {response.status_code}, {response.text}"
        )

    return response.json()
