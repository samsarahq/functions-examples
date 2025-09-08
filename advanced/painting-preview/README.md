# painting-preview

| Handler         |
| --------------- |
| entrypoint.main |

---

This function creates AI-generated painting previews for buildings captured by vehicle dashcams during alerts. It is meant to showcase what is possible with Functions from a creativity standpoint.

When triggered by an alert, it initiates media retrieval from the dashcam at the incident location. On a scheduled basis, it downloads available images and uses OpenAI's image editing API to generate professional painting mockups with modern colors, removing vehicle details.

### Event Parameters

| Parameter Name               | Description                                      | Required   |
| ---------------------------- | ------------------------------------------------ | ---------- |
| SamsaraFunctionTriggerSource | Trigger source: "alert" or "schedule"            | Yes        |
| assetId                      | Vehicle asset ID (required for alert triggers)   | For alerts |
| alertIncidentTime            | Timestamp of the alert incident in milliseconds  | For alerts |
| IsEuRegion                   | Boolean flag for whether to use EU API endpoints | No         |

### Secrets

| Secret Name     | Description                                |
| --------------- | ------------------------------------------ |
| SAMSARA_API_KEY | Samsara API key for camera media retrieval |
| OPENAI_API_KEY  | OpenAI API key for image editing services  |
