# Phase 12 Implementation Plan — Distributed Worker System

This document outlines the technical implementation plan for **Phase 12: Worker System** (`src/browser_mcp/workers/`) of the Enterprise Browser MCP Platform.
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

In Phase 11, we introduced the `JobManager` with an `InMemoryJobProvider` to handle asynchronous tasks within the FastAPI process. While sufficient for local development, production browser automation is highly resource-intensive and requires isolated execution.

**Phase 12** implements a fully distributed **Worker System** backed by Redis. It decouples job submission (REST API) from job execution (Browser Core), allowing horizontal scaling of browser workers.

> *"Phase 12 transforms the platform into a distributed system. The REST API enqueues jobs into Redis, and independent Worker nodes consume, execute, and report back, ensuring resilience, retries, and high availability."*

### Key Architectural Commitments:
1. **Redis Integration**: Redis serves as the message broker, state store, and lock manager.
2. **Provider Swap**: The Phase 11 `JobExecutionProvider` is upgraded to `RedisJobProvider`.
3. **Dedicated Worker Processes**: Workers are launched independently via the CLI (`browser-mcp worker start`) and maintain their own `AppContext` and browser pools.
4. **Resilience & Safety**: Native support for Dead Letter Queues (DLQ), exponential backoff retries, and graceful cancellation/resumption.
5. **Priority Queues**: Support for critical, default, and low-priority job lanes.
6. **Task Scheduler**: Implementation of a `Scheduler` for recurring or delayed browser jobs (e.g., daily scraping).

---

## 2. Directory & Component Layout

```text
src/browser_mcp/workers/
├── __init__.py
├── engine.py             # WorkerEngine (Core consumer loop)
├── config.py             # config.workers.* (Redis URI, concurrency)
├── errors.py             # Worker-specific exceptions
│
├── broker/               # Queue management
│   ├── __init__.py
│   ├── redis.py          # Redis client and Lua scripting for queue logic
│   ├── queues.py         # Priority queue management
│   └── dlq.py            # Dead Letter Queue handling
│
├── execution/            # Job processing
│   ├── __init__.py
│   ├── executor.py       # JobExecutor (bridges Job payload to AppContext)
│   ├── retry.py          # Exponential backoff and retry policies
│   └── state.py          # Synchronizes job state back to Redis
│
├── scheduler/            # Deferred and recurring jobs
│   ├── __init__.py
│   ├── cron.py           # Cron parser and trigger
│   └── dispatcher.py     # Pushes scheduled jobs to the active queue
│
└── cli.py                # Worker CLI commands
```

*(Note: `src/browser_mcp/api/jobs/provider.py` will also be updated with `RedisJobProvider`)*

---

## 3. Detailed Component Specifications

### 3.1. Message Broker (Redis)
We will use `redis.asyncio` to implement a lightweight, reliable queue.
- **Queues**: `browser_jobs:high`, `browser_jobs:default`, `browser_jobs:low`.
- **DLQ**: `browser_jobs:dlq` (Failed jobs exceeding max retries).
- **Job State**: Stored in Redis Hashes (`job:{job_id}`) for O(1) retrieval by the REST API.

### 3.2. Worker Lifecycle (`WorkerEngine`)
1. **Startup**: Initializes `AppContext`, connects to Redis, and registers capabilities.
2. **Poll Loop**: Uses `BRPOP` (blocking pop) on priority queues.
3. **Execution**: Parses the JSON `JobModel`, invokes the `JobExecutor`, which routes to `PluginManager` or `NavigationEngine`.
4. **Heartbeat**: Periodically updates a `job:{job_id}:heartbeat` key to detect crashed workers (zombie jobs).
5. **Shutdown**: Gracefully finishes active jobs or requeues them before exiting (`SIGTERM`).

### 3.3. Retry & Cancellation
- **Retry**: On transient failures (e.g., `TimeoutError`), the job is placed in a delayed set and retried with exponential backoff.
- **Cancellation**: If the REST API sets the job state to `Cancelled` in Redis, the worker's active `asyncio.Task` is cancelled, and the browser session is forcefully torn down.

### 3.4. Worker Configuration Schema (`config.workers.*`)
- `redis_uri`: Connection string (default `redis://localhost:6379/0`).
- `concurrency`: Number of concurrent jobs per worker process (default `2`).
- `queues`: List of queues to listen to (default `["high", "default", "low"]`).
- `max_retries`: Default retry limit (default `3`).
- `heartbeat_interval`: Interval in seconds (default `30`).

### 3.5. CLI Integration
Integrated into the main CLI:
- `browser-mcp worker start --queues high,default --concurrency 4`
- `browser-mcp worker status` (lists active workers and queue depths)
- `browser-mcp worker schedule --job my_job.json --cron "0 0 * * *"`

---

## 4. Documentation Strategy (`docs/workers/`)

Complete documentation suite under `docs/workers/`:
- `docs/workers/overview.md` (Architecture and Redis dependency).
- `docs/workers/deployment.md` (Scaling workers horizontally).
- `docs/workers/retries-and-dlq.md` (Handling failures).
- `docs/workers/scheduling.md` (Cron jobs and delayed execution).

---

## 5. Open Questions for User Approval

1. **Queue Backend**: This plan proposes using `redis.asyncio` directly to build a highly tailored, dependency-light queue. Alternatively, we could use a framework like `ARQ` (Async Redis Queue) or `Celery`. Building directly on `redis.asyncio` ensures tighter integration with our Job Models and avoids heavy third-party abstractions. Do you agree with the direct Redis implementation?
2. **Worker Isolation**: Should a single worker process handle multiple concurrent browser jobs (`concurrency=4`), or should we enforce 1 process = 1 browser job for maximum memory isolation?

---

## 6. Verification Plan

1. **Unit Tests (`tests/unit/test_workers_*.py`)**:
   - Queue enqueue/dequeue logic with priority handling.
   - Retry logic and DLQ routing upon exceeding `max_retries`.
   - `RedisJobProvider` state synchronization.
2. **Integration Tests (`tests/integration/test_workers_integration.py`)**:
   - End-to-end flow: API `POST /jobs` -> Redis -> Worker execution -> API `GET /jobs` (Status: Completed).
   - Simulating worker crashes and validating zombie job recovery via heartbeats.
   - Job cancellation via Redis pub/sub or state polling.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
