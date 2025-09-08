# compliance-audit

| Handler                  |
| ------------------------ |
| compliance_audit.main    |

---

This function performs automated compliance checks on fleet safety settings by comparing the current safety score target against expected compliance standards. It retrieves safety settings from the Samsara API and sends notifications when the safety score target deviates from the expected threshold of 90, helping maintain regulatory compliance.

### Event Parameters

This function does not require any specific event parameters.

### Secrets

| Secret Name         | Description                                    |
| ------------------- | ---------------------------------------------- |
| SAMSARA_API_TOKEN   | Samsara API token for accessing fleet data    |
| NOTIFY_WEBHOOK      | Webhook URL for sending compliance alerts     |