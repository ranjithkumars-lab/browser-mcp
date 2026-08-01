# Phase 0 Walkthrough

This document walks through what Phase 0 of the Enterprise MCP Server
Template delivered, how the pieces fit together, and how to run and verify
the result. It is the "how it works" companion to
[Architecture](../../docs/Architecture.md) (design) and
[Design Principles](../../docs/Design-Principles.md) (why we build this way).

---

## 1. What Phase 0 is

Phase 0 builds the **scaffolding and infrastructure** of an enterprise MCP
server with **zero business logic**. Everything a real MCP server needs —
configuration, dependency injection, lifecycle, logging, events, the tool
framework, transport abstraction, health endpoints, and a CLI — is
implemented and tested. Anything that is browser/domain-specific is
deliberately **not** here.

Everything that belongs to a later phase is present only as an **interface or
scaffold** (see [Section 8](#8-scaffolds-for-later-phases)).

### Deliverables

- `uv` project, Python 3.13, `src` layout, single package `enterprise_mcp`
  (distribution name `enterprise-mcp-server`).
- Hierarchical configuration with Pydantic v2 + YAML.
- DI container, lifecycle manager, application bootstrap context.
- structlog structured logging.
- Async event bus with subscriber isolation.
- Tool framework: `@tool` decorator, metadata, registry, validator, loader.
- Transport abstraction with registry/factory (implementations stubbed).
- MCP protocol/server abstractions.
- FastAPI REST interface: `/health`, `/live`, `/ready`, `/version`.
- Scaffolds: extensions, workers, persistence, security, AI.
- Typer CLI: `serve`, `version`, `doctor`, `config`, `plugins`.
- Dev tooling: Ruff, Pyright, pytest, pre-commit, Makefile.
- Ops: Dockerfile, docker-compose, Kubernetes manifests, GitHub Actions.
- Docs: architecture, design principles, compatibility, ADRs, this walkthrough.

---

## 2. Repository layout

```text
src/enterprise_mcp/
├── foundation/     # DI container, lifecycle, app bootstrap context
├── config/         # models, loader, defaults, settings/*.yaml
├── observability/  # logging (implemented), metrics + tracing (scaffolds)
├── events/         # async event bus
├── tools/          # @tool decorator, metadata, registry, validator, loader
├── transport/      # base interface, registry, factory (+ http/sse/stdio stubs)
├── mcp/            # protocol + server abstractions
├── interfaces/     # REST (FastAPI), WebSocket + internal (scaffolds)
├── extensions/     # plugins, middleware, hooks, providers (scaffolds)
├── workers/        # executors, schedulers, queues, retry (scaffolds)
├── persistence/    # repositories, models, database (scaffolds)
├── security/       # auth, RBAC, secrets, audit (scaffolds)
├── ai/             # reserved (empty)
├── resources/      # templates, static, sample-data
├── utils/          # error hierarchy and shared helpers
└── cli/            # Typer CLI: serve, version, doctor, config, plugins

tests/
├── unit/           # 51 passing tests
├── integration/    # reserved
├── e2e/            # reserved
├── fixtures/       # reserved
└── data/           # sample YAML for config tests

examples/
├── basic/          # minimal server exposing one tool
├── advanced/       # fuller example wiring plugins/events
└── production/     # deployment-oriented example

deployments/
├── docker/         # multi-stage Dockerfile
└── kubernetes/     # ConfigMap, Deployment, Service manifests

.github/workflows/  # ci.yml, release.yml
docs/               # MkDocs site source
scripts/            # bootstrap, dev, release, version helpers
```

---

## 3. The runtime flow in five steps

1. **Configuration** — `load_settings()` merges bundled defaults →
   environment YAML (`settings/{development,production,test}.yaml`) →
   environment variables (`ENTERPRISE_MCP_...`) → explicit overrides.
   The result is a validated `Settings` model
   (`src/enterprise_mcp/config/loader.py`).

2. **Composition root** — `AppContext` binds `settings`, a `Container`
   (DI), a `LifecycleManager`, an `EventBus`, and a `ToolRegistry`
   (`src/enterprise_mcp/foundation/app.py`).

3. **Startup** — `AppContext.start()` runs the lifecycle's registered
   startup hooks. The FastAPI lifespan calls `start()`/`stop()` around the
   serving window (`src/enterprise_mcp/interfaces/rest/app.py`).

4. **Traffic** — requests enter through a transport. The transport
   abstraction (`src/enterprise_mcp/transport/base.py`) means business logic
   never depends on streamable-http vs SSE vs stdio. Tool calls are
   dispatched through the `ToolRegistry`.

5. **Observability** — structlog emits JSON logs with request context; health
   endpoints report process/readiness status.

The full call path for a normal launch:

```text
enterprise-mcp serve
  → load_settings(...)
  → AppContext(settings)                 # container + lifecycle + events + tools
  → uvicorn.run("...rest.app:create_app", factory=True)
  → create_app() builds FastAPI app      # /health /live /ready /version
  → lifespan → context.start()           # runs startup hooks
  → serving...
  → shutdown → context.stop()            # runs shutdown hooks
```

---

## 4. Module deep-dive

### 4.1 Configuration (`config/`)

The loader supports the standard, hierarchical resolution:

```text
bundled defaults  →  <env>.yaml  →  ENTERPRISE_MCP_* env vars  →  CLI overrides
```

- `config/models.py` — Pydantic `Settings` model (server, transports,
  observability, security).
- `config/loader.py` — `load_settings()` performs a deep YAML merge then
  applies environment-variable and explicit overrides.
- `config/settings/default.yaml` — the defaults:

```yaml
server:
  name: enterprise-mcp-server
  environment: development
  transports:
    default: streamable-http
    host: 0.0.0.0
    port: 8000
```

Try `uv run enterprise-mcp config --json` to see the effective configuration.

### 4.2 Foundation (`foundation/`)

- `container.py` — `Container` registers singletons/transients via factory
  callables; `acreate()` auto-wires dependencies from type hints (async
  aware).
- `lifecycle.py` — `LifecycleManager` runs `STARTUP`/`SHUTDOWN` hooks in
  registration order.
- `app.py` — `AppContext` is the composition root described in
  [Section 3](#3-the-runtime-flow-in-five-steps).

### 4.3 Events (`events/`)

`EventBus` is async-first pub/sub. Subscribers run in isolation so one
failing handler does not break the others. A subscriber that raises is logged
(under the `event_name` key) and the remaining subscribers still run.

```python
await bus.publish("tool.invoked", {"name": "hello"})
```

### 4.4 Tools (`tools/`)

The dual-usage `@tool` decorator works bare or parameterized:

```python
@tool(description="Say hello to someone.")
async def hello(name: str) -> str:
    return f"hello, {name}!"
```

- `decorators.py` — the decorator plus generated `ToolMetadata`.
- `metadata.py` — `ToolMetadata`, parameter/return schemas.
- `registry.py` — `ToolRegistry` for `register`/`list`/`call`.
- `validator.py` — runtime input validation.
- `loader.py` — auto-discovery of tool modules.

A server registers its tools on the registry:

```python
context.tools.register(hello)
```

### 4.5 Transport (`transport/`)

`Transport` is the base interface (`start`, `stop`, `handle`, `is_running`).
The `Registry` and `Factory` resolve a named transport. In Phase 0 the
concrete transports (`http.py`, `sse.py`, `stdio.py`) are **stubs** that
raise `NotImplementedError` for `handle`; they are implemented in Phase 1
behind the same interface.

### 4.6 MCP (`mcp/`)

`protocol.py` and `server.py` provide the protocol/server abstractions that
Phase 1's streamable-http implementation will plug into.

### 4.7 REST interface (`interfaces/rest/`)

`create_app(context=None)` is a FastAPI application factory usable with
`uvicorn --factory`. When called with no arguments it builds a default
context, which is how the CLI and Docker launch it.

| Endpoint     | Response                                   | Purpose                        |
| ------------ | ------------------------------------------ | ------------------------------ |
| `/health`    | `{"status": "ok", "service": ...}`         | Liveness / basic health        |
| `/live`      | `{"status": "alive"}`                      | Process liveness               |
| `/ready`     | `{"status": "ready"}` (503 if unready)     | Core services readiness        |
| `/version`   | version metadata                           | Version reporting              |

Interactive API docs are served at `/docs`.

### 4.8 CLI (`cli/`)

Typer app exposed as the `enterprise-mcp` console script:

```bash
uv run enterprise-mcp serve             # run the server
uv run enterprise-mcp version           # print version info
uv run enterprise-mcp doctor            # environment diagnostics
uv run enterprise-mcp config --json     # show effective configuration
uv run enterprise-mcp plugins           # list extensions (scaffold)
```

---

## 5. Running it

Prerequisites: [uv](https://docs.astral.sh/uv/) with Python 3.13.

```bash
uv sync --all-extras       # create the environment + install everything
uv run enterprise-mcp doctor
uv run enterprise-mcp serve              # http://localhost:8000
```

In a second terminal:

```bash
curl http://localhost:8000/health        # {"status":"ok",...}
curl http://localhost:8000/ready         # {"status":"ready"}
curl http://localhost:8000/version
curl http://localhost:8000/docs          # interactive API docs
```

### Example server

```bash
uv run python examples/basic/basic_server.py
# registered tools: ['hello']
# enterprise-mcp-server v0.1.0 ready
```

---

## 6. Verification

```bash
uv run pytest            # 51 passed
uv run ruff check .      # all checks passed
uv run pyright           # 0 errors (strict mode)
uv run pre-commit run --all-files
```

The Makefile wraps these:

```bash
make lint typecheck test test-coverage doctor config
```

Phase 0 exit criteria:

- [x] `uv sync --all-extras` resolves cleanly.
- [x] `ruff check .` clean.
- [x] `pyright` 0 errors in strict mode.
- [x] `pytest` green (51 tests at Phase 0 close).
- [x] Server boots; `/health`, `/live`, `/ready`, `/version` respond.
- [x] Example server registers and lists its tools.
- [x] No browser/third-party backend imports in `src/enterprise_mcp`.

---

## 7. Windows notes

- **uv trampolines are not portable**: console-script launchers (e.g.
  `pyright.exe`) embed the absolute path to the venv's `python.exe`. If the
  project directory is **moved**, run `uv sync --all-groups --all-extras`
  (or delete `.venv` first) so the launchers are regenerated with the new
  path. Otherwise you get errors like `Failed to canonicalize script path`.
- **`ruff format --check`** can crash on Windows when diffs are needed
  (a Ruff bug in the diff renderer). Use `ruff format .` directly; CI runs
  on Linux where `--check` is safe.
- **`make`** is Unix-oriented; on Windows run `uv run <tool>` directly.
- **pytest `tmp_path`**: `tests/conftest.py` redirects pytest's basetemp
  into the OS temp dir to avoid long-path/scanning issues.

---

## 8. Scaffolds for later phases

These packages exist with interfaces and `NotImplementedError` stubs only:

| Package        | Later-phase responsibility                          |
| -------------- | --------------------------------------------------- |
| `transport/*`  | Streamable HTTP (Phase 1), SSE, stdio backends      |
| `observability`| Prometheus metrics, OpenTelemetry tracing backends  |
| `security/`    | Auth providers, RBAC, secrets vault, audit storage  |
| `workers/`     | Executors, schedulers, queues, retry backends       |
| `persistence/` | Repositories, models, migrations, DB drivers        |
| `extensions/`  | Plugin loading, middleware, hooks, providers        |
| `ai/`          | Memory, prompts, agents                             |

The extension points exist **now**; the backends are added in later phases
behind them. This keeps the Phase 0 surface small, testable, and free of
third-party operational dependencies.

---

## 9. Ops and CI

- **Docker** (`deployments/docker/Dockerfile`): multi-stage build with the
  official `uv` base image, non-root user, and a health check.
- **docker-compose**: `.dev` and `.prod` overrides.
- **Kubernetes** (`deployments/kubernetes/manifests.yaml`): ConfigMap,
  Deployment, Service with readiness/liveness probes.
- **GitHub Actions**: `ci.yml` (lint + typecheck + test on every push/PR)
  and `release.yml` (tag `v*` → version-match check, PyPI publish, GHCR
  image push).

> Note: Docker is not installed in the author's local (Windows) environment,
> so the image build itself has not been executed end-to-end; CI exercises
> it on Linux.

---

## 10. Extending into Phase 1

Phase 1 builds the first real backend on top of Phase 0:

1. Implement the streamable-http transport using the official Python MCP SDK,
   wired through `transport/registry.py` and the `Transport` interface.
2. Mount the MCP server in the FastAPI app next to the health endpoints.
3. Add the metrics (Prometheus) and tracing (OpenTelemetry) backends.
4. Optionally rename `enterprise_mcp` → `browser_mcp` once the browser
   server features start being added.

The **Template First Principle** still governs: generic capabilities are
added here in this repository; browser-specific capabilities live in the
downstream server code that consumes this foundation.

---

## 11. Related documents

- [Architecture](../../docs/Architecture.md) — system design.
- [Design Principles](../../docs/Design-Principles.md) — guiding principles.
- [Compatibility](../../docs/Compatibility.md) — supported Python/OS/transport matrix.
- [Development Rules](../../docs/Development-Rules.md) — contribution and workflow rules.
- [Folder Structure](../../docs/Folder-Structure.md) — directory responsibilities.
- [Production Checklist](../../docs/Production-Checklist.md) — go-live checklist.
- [ADRs](../../docs/adr/index.md) — architecture decision records.
