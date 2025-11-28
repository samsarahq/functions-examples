import requests
import json
import os
import samsara

SAMSARA_SAFETY_SETTINGS_API_URL = "https://api.samsara.com/fleet/settings/safety"
EXPECTED_SAFETY_SCORE_TARGET = 90


def main(event, context):
    function = samsara.Function()
    secrets = function.secrets().load()

    SAMSARA_API_HEADERS = {
        "accept": "application/json",
        "authorization": f"Bearer {secrets['SAMSARA_API_TOKEN']}",
    }

    NOTIFY_WEBHOOK = secrets["NOTIFY_WEBHOOK"]

    response = requests.get(
        SAMSARA_SAFETY_SETTINGS_API_URL, headers=SAMSARA_API_HEADERS
    )
    safety_settings = json.loads(response.text)

    if "data" in safety_settings and len(safety_settings["data"]) >= 1:
        target_settings = safety_settings["data"][0]
        if "safetyScoreTarget" in target_settings:
            notification_message = "Safety compliance check: "

            safety_target = target_settings["safetyScoreTarget"]
            if safety_target != EXPECTED_SAFETY_SCORE_TARGET:
                notification_message += f"Safety score target should be {EXPECTED_SAFETY_SCORE_TARGET}, but it's actually {safety_target}.\n\nReview the setting here: https://cloud.samsara.com/o/15030/fleet/config/safety_settings"
                requests.post(NOTIFY_WEBHOOK, json={"message": notification_message})
