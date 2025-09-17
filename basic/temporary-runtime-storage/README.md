# temporary-runtime-storage

| Handler       |
| ------------- |
| function.main |

---

If you need to store files that are:

- available for download in the Samsara Dashboard
- are shared between multiple Functions
- are needed in subsequent runs of the same Function

Use the `persistent-storage` template.

As a form of filesystem cache, there is a directory that can be written to, with the path set in the `SamsaraFunctionTempStoragePath` environment variable.

> **IMPORTANT:** While the simulator does allow for writing arbitrary files, writing to any other directory in production will end up with an exception about read only file system.

For example, if you have a Function named `my-func` that uses temporary storage, when testing locally with the simulator, any files written to the temporary directory can be inspected after execution in `.samsara-functions/functions/my-func/temp`. This directory is automatically cleared before each Function invocation.

It can be useful in scenarios where e.g. a library uses file paths instead of accepting bytes as parameters.

### Event Parameters

This function does not require any event parameters.

### Secrets

This function does not require any secrets.
