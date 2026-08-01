# Worker Architecture

## Component layout

    workers/
    ├── broker/       BrokerProvider and priority/DLQ implementations
    ├── execution/    ownership leases, cancellation, and executor
    ├── scheduler/    scheduled definitions and persistence primitives
    ├── engine.py     per-worker state machine
    └── manager.py    lifecycle façade

## Execution flow

    Producer → priority queue → WorkerEngine → WorkerExecutor → AppContext.tools
                               │                    │
                               └── nack ───────────→ DLQ

A producer enqueues a JSON-compatible payload with tool_name and arguments.
WorkerEngine selects the highest non-empty queue. WorkerExecutor invokes the
registered AppContext tool. Successful work is acknowledged; failures are
negatively acknowledged and routed to the DLQ.

BrokerProvider is the durable-queue seam. Production implementations can
replace the in-memory-compatible provider with Redis, Celery, or another broker
without changing engines or executors.
