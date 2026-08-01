# Phase 11 Implementation Plan — REST API Engine (Refined Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 11: REST API Engine** (`src/browser_mcp/api/`) of the Enterprise Browser MCP Platform.
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

While Phase 10 integrated the Model Context Protocol (MCP) strictly for AI agents, **Phase 11** introduces a traditional **REST API Engine** via FastAPI. This API allows standard web applications and microservices to orchestrate the Browser Core.

> *"Phase 11 provides a REST presentation layer built on top of the Browser Core. It introduces an `ApiEngine` orchestrator and a `JobManager` to handle inherently asynchronous browser operations seamlessly, strictly delegating execution to the `AppContext`."*

### Key Architectural Commitments:
1. **Orchestrator (`ApiEngine`)**: A FastAPI-wrapped orchestrator that delegates strictly to the `AppContext` and internal managers, maintaining the separation of protocol transport and business logic.
2. **Provider Abstraction (`JobExecutionProvider`)**: Implements `InMemoryJobProvider` now, reserving `RedisJobProvider` and `CeleryJobProvider` for Phase 12.
3. **Async Job Pattern (`JobManager`)**: Endpoints return `202 Accepted` with a Job ID, moving away from blocking HTTP connections.
4. **Exposing the Full Core**: Beyond plugins, the REST API exposes Sessions, Navigation, Forms, Downloads, and Uploads.
5. **Event Streaming (`/api/v1/events`)**: Reuses the `EventStreamAdapter` from Phase 8 for SSE log streaming.
6. **Authentication (`ApiKey`)**: Configurable API Key validation for securing the endpoints (disabled in dev, enforced in prod).
7. **Versioned Routing (`/api/v1`)**: Strict API versioning and OpenAPI schema generation.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/api/
├── __init__.py
├── app.py                # FastAPI application factory
├── engine.py             # ApiEngine (Core orchestrator delegating to AppContext)
├── dependencies.py       # FastAPI Depends() providers (AppContext, Auth validation)
├── middleware.py         # Request tracing, logging, and error handling
├── errors.py             # REST-specific HTTP exceptions
│
├── jobs/                 # Job orchestration subsystem
│   ├── __init__.py
│   ├── manager.py        # JobManager facade
│   ├── provider.py       # JobExecutionProvider interface
│   ├── models.py         # Formal Job JSON models
│   ├── store.py          # State persistence
│   └── cleanup.py        # Retention policy enforcer
│
├── gateways/             # Subsystem delegations
│   ├── __init__.py
│   ├── plugins.py        # Maps to PluginManager
│   ├── browser.py        # Maps to NavigationEngine / SessionManager
│   ├── artifacts.py      # Maps to TransferManager
│   └── logs.py           # Maps to BrowserEventManager
│
├── v1/                   # Version 1 API
│   ├── __init__.py
│   ├── router.py         # Main APIRouter aggregator
│   ├── routes/
│   │   ├── jobs.py       # Job polling and lifecycle
│   │   ├── plugins.py    # Plugin execution
│   │   ├── browser.py    # Browser lifecycle, forms, and transfers
│   │   ├── health.py     # Health checks
│   │   ├── metrics.py    # Platform metrics
│   │   └── events.py     # SSE Stream from EventStreamAdapter
│   └── schemas/          # Pydantic schemas (Request/Response)
│
└── config.py             # config.api.* specific configurations
```

---

## 3. Detailed Component Specifications

### 3.1. Formalized Job Model (`src/browser_mcp/api/jobs/models.py`)
Matches the rigorous structures used in earlier phases:
```json
{
  "job_id": "job_54321",
  "type": "plugin_execution",
  "state": "Running",
  "created_at": "2026-08-01T12:00:00Z",
  "started_at": "2026-08-01T12:00:01Z",
  "completed_at": null,
  "duration_ms": 1500,
  "progress": 50,
  "result": null,
  "error": null
}
```
**Job Lifecycle States**: `Queued`, `Pending`, `Running`, `Completed`, `Failed`, `Cancelled`, `Expired`.

### 3.2. Route Organization & Browser Core Exposure

The REST API formally exposes operations handled by the Browser Core managers:

**Browser API (`/api/v1/browser`)**
- `POST /browser/sessions` (Create browser profile/context)
- `DELETE /browser/sessions/{id}` (Teardown session)
- `POST /browser/navigation` (goto, reload, back)
- `POST /browser/forms` (fill, submit)
- `POST /browser/download` & `POST /browser/upload` (Transfer initiation)

**Plugins API (`/api/v1/plugins`)**
- `GET /plugins` (List installed/active)
- `POST /plugins/run` (Triggers job)

**Events API (`/api/v1/events`)**
- `GET /events/stream` (SSE integration via `EventStreamAdapter`).

**System API (`/api/v1/`)**
- `GET /health` & `GET /metrics`

### 3.3. Authentication
Configurable API Key Authentication (`X-API-Key` header) validated via `dependencies.py`:
- **Development**: Disabled by configuration.
- **Production**: Enabled and enforced.

### 3.4. API Configuration Schema (`config.api.*`)
- `host` & `port` (default `0.0.0.0:8080`).
- `cors_origins`: Allowed origin list.
- `request_timeout`: Hard limit on sync endpoints.
- `max_request_size`: Payload limits.
- `enable_docs`, `enable_redoc`: OpenAPI toggles.
- `enable_health`, `enable_metrics`: System route toggles.
- `job_retention_minutes`: Time before `Expired` state cleanup.
- `max_jobs`: Concurrency backpressure limit.
- `default_sync_timeout`: Timeout threshold.

### 3.5. CLI Integration
Integrated directly into the existing `cli.py` root:
- `browser-mcp api serve`
- `browser-mcp api doctor`

---

## 4. Documentation Strategy (`docs/api/`)

Complete documentation suite under `docs/api/`:
- `docs/api/overview.md` (Design and Auth).
- `docs/api/async-jobs.md` (JobManager and 202 Accepted polling).
- `docs/api/browser-core.md` (Exposed browser endpoints).
- `docs/api/streaming.md` (SSE Events mapping).

---

## 5. Verification Plan

1. **Unit Tests (`tests/unit/test_api_*.py`)**:
   - `JobManager` lifecycle transitions (`Queued` → `Expired`) using `InMemoryJobProvider`.
   - `ApiEngine` correct delegation to `AppContext`.
   - API Key dependency rejection for unauthorized requests.
2. **Integration Tests (`tests/integration/test_api_integration.py`)**:
   - Concurrent async job executions simulating scraping/plugins.
   - API cancellation (`DELETE /jobs/{id}`) halting active jobs.
   - `EventHistoryStore` & `EventStreamAdapter` SSE testing via `httpx.AsyncClient`.
   - Artifact download and malformed payload validations.
   - Graceful shutdown without dropping active requests.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
