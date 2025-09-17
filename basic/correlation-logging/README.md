# correlation-logging

| Handler |
| ---- |
| function.main |

---

Demonstrates structured, correlation-aware logging for Samsara Functions. On each invocation, the function initializes logging with the automatically provided correlation ID, then emits logs in two formats based on configuration: either raw text or JSON output. 

Output is written to standard output for levels below INFO, standard error above WARN, and can be correlated with production logs using the correlation ID retrieved at Function start.

### Event Parameters

| Parameter Name | Description | Required |
| ---- | --- | ---- |
| SamsaraFunctionLoggerIsJsonOut | When "true", emits logs as JSON objects. Defaults to `false`. | No |
| SamsaraFunctionLoggerLevel | Minimum log level to emit (DEBUG, INFO, WARN, ERROR, CRITICAL). Defaults to `INFO`. | No |

### Secrets

This function does not require any secrets.


