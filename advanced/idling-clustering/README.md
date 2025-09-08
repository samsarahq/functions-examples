# idling-clustering

| Handler                    |
| -------------------------- |
| idling_clustering.main     |

---

This function analyzes vehicle idling patterns by clustering idling events based on geographic proximity to identify hotspots where multiple vehicles frequently idle. It retrieves idling reports from the past 8 hours, groups nearby locations within a 2-mile radius, and ranks clusters by total idling events. The top 5 clusters are reported via webhook for fleet optimization insights.

### Event Parameters

This function does not require any specific event parameters.

### Secrets

| Secret Name         | Description                                    |
| ------------------- | ---------------------------------------------- |
| SAMSARA_API_TOKEN   | Samsara API token for accessing fleet data    |
| NOTIFY_WEBHOOK      | Webhook URL for sending cluster reports       |