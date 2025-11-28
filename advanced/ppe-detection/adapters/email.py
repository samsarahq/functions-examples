import json
import requests
from dataclasses import asdict, dataclass
from samsarafnsecrets import get_secrets


@dataclass
class Variables:
    DevNotificationMainContent: str = ""
    DevNotificationTeamName: str = ""
    DevNotificationTeamSignoff: str = ""
    NotificationSubtitle: str = ""
    NotificationTitle: str = ""


def send(
    to_email: str,
    subject: str,
    attachments: list[tuple[str, bytes]],
    variables: Variables,
):
    variables_json = json.dumps(asdict(variables))

    files = map(lambda f: ("attachment", f), attachments)

    res = requests.post(
        "https://api.mailgun.net/v3/sis.samsara.com/messages",
        auth=("api", get_secrets(force_refresh=True)["MAILGUN_KEY"]),
        data={
            "from": "Samsara SIS <no-reply@sis.samsara.com>",
            "to": to_email,
            "subject": subject,
            "template": "sis custom report template",
            "h:X-Mailgun-Variables": variables_json,
        },
        files=files,
    )

    res.raise_for_status()
    return res
