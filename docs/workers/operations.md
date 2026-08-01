# Worker Operations

## CLI

The worker CLI provides the initial lifecycle commands.

    browser-mcp worker start
    browser-mcp worker status

The Phase 12 command surface reserves stop, drain, retry, and purge-dlq.
Operational hosts can implement them through WorkerManager and their selected
broker.

## Dead-letter queue

A payload is placed in the DLQ after execution fails. Inspect its job payload,
error context, attempt count when supported by the broker, and source tool
before retrying. Retry only after correcting deterministic failures such as
invalid input or missing permissions.

## Monitoring

Track active worker count and worker state, queue depth by priority,
claimed/abandoned jobs, success and failure counts, and DLQ size and age.
Never log secret-bearing tool arguments, browser storage state, or uploaded
file contents in worker diagnostics.
