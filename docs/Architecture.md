# Architecture

## Overview

The Enterprise MCP Server Template is a **scaffolding-first** foundation for
building MCP servers. It provides infrastructure and abstractions with zero
business logic. Downstream servers fork this template and add their own tools,
plugins, and domain capabilities.

The template is **transport-independent**: business logic never imports a
transport, protocol SDK, or HTTP framework directly. It interacts with small,
stable interfaces owned by this project.

## Layer Diagram

```text
                    +---------------------------+
                    |   AI Assistant / Clients   |
                    +-------------+-------------+
                                  |
        +-------------------------+-------------------------+
        |                  Transport Layer                  |
        |    streamable-http (default)  |  sse  |  stdio    |
        +-------------------------+-------------------------+
                                  |
                    +-------------v-------------+
                    |        MCP Server         |
                    |  protocol + tool registry  |
                    +-------------+-------------+
                                  |
                    +-------------v-------------+
                    |    Tool Registry          |
                    |  metadata / validation     |
                    +-------------+-------------+
                                  |
              +-------------------+-------------------+
              |                                       |
    +---------v---------+                     +-------v--------+
    |   Domain Tools    |                     |  Extensions    |
    |  (in downstream   |                     |  plugins /      |
    |    repositories)  |                     |  middleware     |
    +---------+---------+                     +-------^--------+
              |                                       |
              +----------------+----------------------+
                               |
                 +-------------v-------------+
                 |  Foundation (DI, lifecycle)|
                 +-------------+-------------+
                               |
     +--------------+----------+-----------+---------------+
     |              |          |           |               |
     v              v          v           v               v
  Config        Logging    Event Bus    Metrics        Tracing
```

## Module Responsibilities

| Module           | Responsibility                                                      |
| ---------------- | ------------------------------------------------------------------- |
| `foundation`     | DI container, lifecycle hooks, application bootstrap context         |
| `config`         | Settings models and the hierarchical loader                          |
| `observability`  | structlog setup, metrics/tracing provider abstractions               |
| `security`       | Auth, RBAC, secrets, audit scaffolds                                 |
| `transport`      | `Transport` interface, registry, factory; stubs for each transport  |
| `mcp`            | Protocol + server abstractions over the tool registry                |
| `tools`          | `@tool` decorator, metadata, registry, loader, validator             |
| `extensions`     | Extension/plugin/middleware/hook/provider extension points           |
| `workers`        | Executor, queue, retry, scheduler, DLQ interfaces                    |
| `persistence`    | Repository, entity, database interfaces                              |
| `interfaces`     | FastAPI REST app with health/version endpoints                       |
| `events`         | Async event bus with subscriber isolation                            |
| `cli`            | Typer commands: `serve`, `version`, `doctor`, `config`, `plugins`    |
| `ai`             | Reserved for memory/prompts/agents                                   |

## Key Flows

### Startup

1. `load_settings()` merges YAML defaults, environment YAML, env vars, overrides.
2. `AppContext` is constructed: container, lifecycle manager, event bus, tool
   registry are wired and core services registered.
3. Logging is configured from `LoggingSettings`.
4. `context.start()` runs all lifecycle startup hooks.
5. The REST app is served by Uvicorn; lifespan calls `context.start()`/`stop()`.

### Tool Execution

1. A `@tool`-decorated callable is registered in `ToolRegistry`.
2. Metadata (name, description, parameters) is derived from the signature.
3. On invocation, `ToolRegistry.call()` validates arguments and runs the
   callable (sync or async).

### Events

1. `DomainEvent` instances are published to `EventBus`.
2. Subscribers (sync or async) receive the event.
3. Subscriber failures are logged and isolated; other subscribers still run.

## Extensibility

Downstream servers add capabilities in these ways:

1. **Register tools** via `@tool` and `context.tools.register(...)`.
2. **Subscribe to events** via `context.events.subscribe(...)`.
3. **Add extensions** by subclassing `Extension` and registering it.
4. **Add transports** by implementing `Transport` and registering it.
5. **Add middleware/hooks** through the extension points.

All of these are designed so the template itself stays generic and the
downstream repository stays specific.
