# coach-scoring

| Handler               |
| --------------------- |
| coach_scoring.main    |

---

This function analyzes driver safety score changes and assigns performance scores to their coaches based on improvement or decline patterns. It retrieves driver-coach assignments, compares current vs previous safety scores, and calculates coach performance scores using configurable thresholds. The results are sent to a notification webhook for reporting purposes.

### Event Parameters

This function does not require any specific event parameters.

### Secrets

| Secret Name         | Description                                    |
| ------------------- | ---------------------------------------------- |
| SAMSARA_API_TOKEN   | Samsara API token for accessing fleet data    |
| NOTIFY_WEBHOOK      | Webhook URL for sending score notifications   |