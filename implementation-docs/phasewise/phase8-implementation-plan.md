# Phase 8 Implementation Plan — Browser Events & Live Monitoring Engine (Refined Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 8: Browser Events & Live Monitoring Engine** (`src/browser_mcp/events/`) of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

The **Browser Events Engine** is a **Browser Core service** that formalizes and extends the internal `EventBus` established in earlier phases into an enterprise-grade, typed event infrastructure. It connects browser actions, element interactions, authentication states, transfer progress, and plugin execution to live monitoring endpoints (WebSockets/SSE) without requiring client polling.

> *"Phase 8 formalizes the existing EventBus introduced in earlier phases into a structured Browser Events Engine while preserving 100% backward compatibility for all existing event publishers."*

### Key Architectural Commitments:
1. **Browser Core Service (`BrowserEventManager`)**: Injected into `PluginContext` alongside `BrowserManager`, `SessionManager`, `ElementEngine`, `AuthManager`, `TransferManager`, `Logger`, `Configuration`, and `Metrics`.
2. **Provider Abstraction (`EventProvider`)**: Decouples the event engine logic from storage/in-memory dispatch (`InMemoryEventProvider`, with `RedisEventProvider` reserved).
3. **Event Router (`EventRouter`)**: Evolved subscriber registry managing topic pattern matching (`page.*`, `transfer.#`, `*`), filters, dispatch queues, and async listener isolation.
4. **Middleware Pipeline (`EventMiddleware`)**: Supports extensible middleware layers (`LoggingMiddleware`, `MetricsMiddleware`, `AuditMiddleware`, `SamplingMiddleware`).
5. **Typed Event Schema & Causality (`BrowserEvent`)**: Includes `correlation_id`, `parent_event_id`, `trace_id`, priority levels (`LOW`, `NORMAL`, `HIGH`, `CRITICAL`), and typed payloads (`NavigationPayload`, `TransferPayload`, `AuthenticationPayload`, `PluginPayload`, `ElementPayload`).
6. **Factory Registry (`EventFactoryRegistry`)**: Centralized factories for event construction, reserving namespaces for `browser.*`, `session.*`, `context.*`, `worker.*`, `api.*`.
7. **In-Memory History & Replay Store (`EventHistoryStore`)**: In-memory ring buffer for log inspection, queries, and stream tailing (`browser.events.replay`).
8. **Real-Time Streaming Adapter (`EventStreamAdapter`)**: Formats event serializations for WebSocket and SSE streaming outputs.
9. **Full Configuration Schema (`config.events.*`)**: Detailed schema covering history size, queue size, subscriber timeouts, worker counts, drop policies, and metrics toggles.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/events/
├── __init__.py
├── manager.py            # BrowserEventManager facade (orchestration)
├── provider.py           # EventProvider interface & InMemoryEventProvider
├── router.py             # EventRouter (topic pattern matching, dispatch, filters)
├── middleware.py         # Middleware pipeline (Logging, Metrics, Audit, Sampling)
├── models.py             # BrowserEvent, EventHeader, EventPriority, Typed Payloads
├── errors.py             # EventEngineError hierarchy
├── store.py              # EventHistoryStore (ring buffer & query interface)
├── streaming.py          # EventStreamAdapter (WebSocket & SSE formatters)
│
├── categories/           # Domain event factory builders
│   ├── __init__.py
│   ├── factory.py        # EventFactoryRegistry (dynamic factory dispatcher)
│   ├── page.py           # PageEventFactory
│   ├── element.py        # ElementEventFactory
│   ├── transfer.py       # TransferEventFactory
│   ├── auth.py           # AuthEventFactory
│   ├── plugin.py         # PluginEventFactory
│   └── reserved.py       # Reserved extension points (browser, session, worker, api)
│
└── tools.py              # MCP Tools (browser.events.listen, query, replay)
```

---

## 3. Detailed Component Specifications

### 3.1. Error Hierarchy (`src/browser_mcp/events/errors.py`)
```python
BrowserError
└── EventEngineError
    ├── InvalidEventPatternError
    ├── SubscriberExecutionError
    ├── EventBufferFullError
    ├── MiddlewareExecutionError
    └── StreamDisconnectedError
```

### 3.2. Configuration Schema (`config.events.*`)
- `max_history_size`: Ring buffer capacity (default `1000`).
- `max_queue_size`: Maximum async dispatch queue size (default `10000`).
- `subscriber_timeout_seconds`: Timeout before slow subscribers are isolated (default `5.0`).
- `worker_count`: Number of async event dispatcher workers (default `4`).
- `drop_policy`: Policy when queue fills up (`drop_oldest`, `reject_new`).
- `enable_metrics`: Enables metrics middleware tracking (`true`).
- `enable_streaming`: Enables WebSocket / SSE serialization output (`true`).

### 3.3. Event Model & Correlation Schema (`src/browser_mcp/events/models.py`)
```json
{
  "event_id": "evt_987654321",
  "correlation_id": "corr_123456",
  "parent_event_id": "evt_111222333",
  "trace_id": "trace_abc123",
  "event_type": "download.progress",
  "category": "transfer",
  "priority": "NORMAL",
  "timestamp": "2026-08-01T17:48:00.000Z",
  "meta": {
    "session_id": "s1",
    "browser_id": "b1",
    "context_id": "c1",
    "page_id": "p1"
  },
  "payload": {
    "transfer_id": "xfers_123",
    "progress_percentage": 65.4,
    "bytes_received": 685760,
    "speed_bps": 1048576
  }
}
```

### 3.4. MCP Tools (`src/browser_mcp/events/tools.py`)
- `browser.events.listen`: Subscribes to real-time event topics matching a pattern.
- `browser.events.query`: Queries historical events from `EventHistoryStore` with filters.
- `browser.events.replay`: Replays event streams from a given event ID or timestamp for UI reconnects.

---

## 4. Documentation Strategy (`docs/events/`)

Complete documentation suite under `docs/events/`:
- `docs/events/overview.md`
- `docs/events/architecture.md`
- `docs/events/lifecycle.md`
- `docs/events/filtering.md`
- `docs/events/streaming.md`
- `docs/events/event-reference.md` (Defines every emitted event schema)

---

## 5. Verification Plan

1. **Unit Tests (`tests/unit/test_events_*.py`)**:
   - `EventRouter`: Wildcard topic matching (`page.*`, `transfer.#`, `*`) and priority queueing.
   - `MiddlewarePipeline`: Verification of logging, audit, and metrics middleware execution.
   - `EventHistoryStore`: Ring buffer overflow, filtering, causality tracing, and `replay` queries.
   - High-burst stress test (10,000 event burst) and slow subscriber isolation.
2. **Integration Tests (`tests/integration/test_events_integration.py`)**:
   - Real-time event emission across `NavigationEngine`, `ElementEngine`, `AuthManager`, `TransferManager`, and Plugins via `PluginContext`.
   - Concurrent event publishing, worker handling, and clean browser shutdown context cancellation.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
