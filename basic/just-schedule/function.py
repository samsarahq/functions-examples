from samsarafnsecrets import get_secrets, apply_to_env
import os
import urllib.request
import json


def main(_, __):
    """
    Scheduled function that fetches vehicle count from the Samsara API.
    Demonstrates how to use secrets and make API calls on a schedule.
    """
    secrets = get_secrets()
    apply_to_env(secrets)

    api_key = os.environ.get("SAMSARA_API_KEY")
    if not api_key:
        print({"error": "SAMSARA_API_KEY not configured"})
        return

    try:
        request = urllib.request.Request(
            "https://api.samsara.com/fleet/vehicles",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib.request.urlopen(request) as response:
            data = json.loads(response.read().decode())
            vehicle_count = len(data.get("data", []))

        print({
            "status": "success",
            "vehicleCount": vehicle_count,
        })
    except urllib.error.HTTPError as e:
        print({
            "status": "error",
            "code": e.code,
            "message": str(e),
        })
    except Exception as e:
        print({
            "status": "error",
            "message": str(e),
        })
