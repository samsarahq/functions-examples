# ppe-detection

| Handler         |
| --------------- |
| function.main   |

---

This function detects missing Personal Protective Equipment (PPE) in dashcam images captured around alert times. When triggered by an alert, it queues a road‑facing image retrieval for the vehicle. On a schedule, it downloads available images, analyzes them with an OpenAI vision model for PPE compliance, and emails a report with the image attached for any non‑compliant detections.

### Event Parameters

| Parameter Name               | Description                                      | Required   |
| ---------------------------- | ------------------------------------------------ | ---------- |
| SamsaraFunctionTriggerSource | Trigger source: "alert" or "schedule"            | Yes        |
| assetId                      | Vehicle asset ID (for alert triggers)            | For alerts |
| alertIncidentTime            | Alert timestamp in milliseconds (for alert triggers) | For alerts |
| ToEmail                      | Destination email address (for scheduled runs)   | For schedules |

### Secrets

| Secret Name  | Description                                       |
| ------------ | ------------------------------------------------- |
| SAMSARA_KEY  | Samsara API key for camera media retrieval (SDK) |
| OPENAI_KEY   | OpenAI API key for image analysis                |
| MAILGUN_KEY  | Mailgun API key for sending notification emails  |

### Disclaimers

1. Before bundling this example, vendor the required additonal dependencies:
    ```python
    python run-before-bundle/install_deps_to_lib.py prod
    ```
2. Make sure to replace the email adapter with one that will work with your email notification provider.