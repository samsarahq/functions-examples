import requests
import samsara
from datetime import datetime
from samsara.core import ApiError
from samsarafnsecrets import get_secrets
from samsarafnregion import get_region

client = samsara.Samsara(
    token=get_secrets(force_refresh=True)["SAMSARA_KEY"],
    base_url=get_region().to_api_url(),
)


def start_road_facing_image_retrieval(
    vehicle_id: str,
    moment: datetime,
):
    """Starts a road-facing image retrieval for the given vehicle and moment."""
    try:
        return client.media.post_media_retrieval(
            vehicle_id=vehicle_id,
            start_time=moment.isoformat(),
            end_time=moment.isoformat(),
            media_type="image",
            inputs=["dashcamRoadFacing"],
        ).data.retrieval_id

    except ApiError as e:
        if "not recording at" in e.body.get("message", ""):
            return None

        raise e


def get_available_retrieval_image(retrieval_id: str):
    """Returns the bytes of the available road-facing image retrieval, or None if image is not available."""
    response = client.media.get_media_retrieval(retrieval_id=retrieval_id)

    url = None

    for media in response.data.media:
        if media.input == "dashcamRoadFacing":
            if media.status == "available":
                url = media.url_info.url
                break

    if url is None:
        return None

    response = requests.get(url)
    response.raise_for_status()
    return response.content
