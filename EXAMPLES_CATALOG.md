# Samsara Functions — Examples Catalog

Example Functions demonstrating common patterns, integrations, and best practices.
Each example can be imported directly into the Samsara Functions editor.

Repository: https://github.com/samsarahq/functions-examples

## Basic Examples

Focused patterns that demonstrate a single Samsara Functions capability.

| Example | Description |
|---------|-------------|
| [access-bundle-content](https://github.com/samsarahq/functions-examples/tree/main/basic/access-bundle-content) | Access files bundled with the Function and print their contents. |
| [additional-python-dependencies](https://github.com/samsarahq/functions-examples/tree/main/basic/additional-python-dependencies) | Demonstrates vendoring extra Python dependencies into the bundle and using them. |
| [correlation-logging](https://github.com/samsarahq/functions-examples/tree/main/basic/correlation-logging) | Structured, correlation-aware logging with optional JSON output and custom levels. |
| [just-secrets](https://github.com/samsarahq/functions-examples/tree/main/basic/just-secrets) | Demonstrates retrieving configured secrets at runtime and logging the count. |
| [persistent-storage](https://github.com/samsarahq/functions-examples/tree/main/basic/persistent-storage) | Use shared persistent storage and a lightweight key/value database across runs. |
| [resolve-samsara-region](https://github.com/samsarahq/functions-examples/tree/main/basic/resolve-samsara-region) | Resolve Samsara API region from AWS region and print derived values. |
| [temporary-runtime-storage](https://github.com/samsarahq/functions-examples/tree/main/basic/temporary-runtime-storage) | Use per-invocation temporary storage for transient files in the runtime. |

## Advanced Examples

Multi-step workflows combining Samsara APIs, external services, and real-world business logic.

| Example | Description |
|---------|-------------|
| [coach-scoring](https://github.com/samsarahq/functions-examples/tree/main/advanced/coach-scoring) | Analyze driver safety score changes and compute coach performance scores, sending a summary via webhook. |
| [compliance-audit](https://github.com/samsarahq/functions-examples/tree/main/advanced/compliance-audit) | Audit fleet safety settings against expected targets and trigger a webhook alert if non-compliant. |
| [idling-clustering](https://github.com/samsarahq/functions-examples/tree/main/advanced/idling-clustering) | Cluster idling events by proximity over recent hours and report top hotspots via webhook. |
| [moving-legacy-scripts-to-functions](https://github.com/samsarahq/functions-examples/tree/main/advanced/moving-legacy-scripts-to-functions) | Shows how to make migration from legacy scripts to Functions as seamless as possible. |
| [painting-preview](https://github.com/samsarahq/functions-examples/tree/main/advanced/painting-preview) | Generate painting mockups from dashcam images on alerts and on schedule using OpenAI. |
| [ppe-detection](https://github.com/samsarahq/functions-examples/tree/main/advanced/ppe-detection) | Detect missing PPE in dashcam images using OpenAI; queue on alerts, analyze on schedule, and email reports. |

## Download

To download the entire repository as a zip archive:

https://github.com/samsarahq/functions-examples/archive/refs/heads/main.zip
