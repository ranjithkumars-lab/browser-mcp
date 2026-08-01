# Distributed Worker System — Overview

Phase 12 adds an asynchronous worker layer for browser work that should not
hold an MCP or REST request open. Workers consume queued tool jobs, execute
them through the existing application context, and report failures through a
dead-letter queue (DLQ).

## Scope

- Priority queues: high, default, and low.
- Job ownership leases and abandoned-job detection.
- Cooperative cancellation through CancellationToken.
- Worker lifecycle management and isolated tool execution.
- Scheduled job definitions and in-memory schedule storage.

The current RedisBrokerProvider presents the broker contract and has an
in-memory-compatible implementation. A networked Redis adapter and durable
scheduler dispatch are reserved extension points.

## Key Principles

- **AppContext remains the execution boundary.** Workers call registered tools;
  they do not duplicate browser, plugin, or transfer business logic.
- **A claimed job has an owner and lease.** Ownership metadata supports future
  broker recovery after a worker failure.
- **Failure is explicit.** Failed payloads are sent to the DLQ rather than
  silently discarded.

## Contents

- [Architecture](architecture.md) — components, responsibilities, and flow.
- [Configuration](configuration.md) — settings and queue priorities.
- [Lifecycle](lifecycle.md) — worker/job states, leases, and cancellation.
- [Operations](operations.md) — running, observing, retrying, and DLQ handling.
