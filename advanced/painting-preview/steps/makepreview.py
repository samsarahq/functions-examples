import os
import sys
import requests

from steps.samsarafnstorage import get_storage
from steps.samsarafnsecrets import get_secrets
from steps.utils import base_name_no_ext


# Disable SSL warnings when using verify=False
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def handle(_):
    storage = get_storage()

    retrieved_media_keys = storage.list_keys(
        Prefix=f"{os.environ['SamsaraFunctionName']}/retrieved/",
    )

    print(f"Processing {len(retrieved_media_keys)} images", retrieved_media_keys)

    for original_image_key in retrieved_media_keys:
        original_image_bytes = storage.get_body(Key=original_image_key)
        retrieval_id = base_name_no_ext(original_image_key)

        response = requests.post(
            "https://api.openai.com/v1/images/edits",
            headers={"Authorization": f"Bearer {get_secrets()['OPENAI_API_KEY']}"},
            files={
                "image[]": ("image.jpg", original_image_bytes, "image/jpeg"),
                "model": (None, "gpt-image-1"),
                "prompt": (
                    None,
                    "Generate an image of this building with a new paint job with a modern popular color to send the home owner inspiration and a quote to paint the exterior of their home. Remove the surrounding vehicle details captured from the dashcam.",
                ),
            },
            verify=False,
        )

        if not response.ok:
            print(
                "Error: OpenAI API request failed",
                response.status_code,
                response.text,
                file=sys.stderr,
            )
            continue

        image_base64 = unpack_openai_response_image_base64(response)
        if not image_base64:
            continue

        storage.put(
            Key=f"{os.environ['SamsaraFunctionName']}/finished/{retrieval_id}-original.jpg",
            Body=original_image_bytes,
        )
        storage.put_base64(
            Key=f"{os.environ['SamsaraFunctionName']}/finished/{retrieval_id}-edited.png",
            Base64=image_base64,
        )

        storage.delete(Key=original_image_key)
        print(f"Successfully processed {retrieval_id}")


def unpack_openai_response_image_base64(response: requests.Response) -> str:
    response_data = response.json()
    if not response_data.get("data") or len(response_data["data"]) == 0:
        print(
            "Error: No image data found in the response",
            response.status_code,
            response_data,
            file=sys.stderr,
        )
        return None

    if usage := response_data.get("usage"):
        print(
            "OpenAI usage:",
            usage,
        )

    return response_data["data"][0]["b64_json"]
