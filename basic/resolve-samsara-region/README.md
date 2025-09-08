# resolve-samsara-region

| Handler       |
| ------------- |
| function.main |

---

This function resolves the correct Samsara API region (US, EU, or CA) based on the `AWS_DEFAULT_REGION` environment and prints:
- the resolved region code
- the corresponding base API URL
- a sample selection value derived from the region

Use it to route API calls to the appropriate Samsara regional endpoint.

### Event Parameters

This function does not require any event parameters.

### Secrets

This function does not require any secrets.
