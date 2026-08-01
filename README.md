# Enterprise MCP Server Template

A production-ready, transport-independent foundation for building enterprise
Model Context Protocol (MCP) servers in Python.

This template contains **zero business logic**. It provides the infrastructure,
abstractions, and tooling that every MCP server needs, so downstream projects
can focus on their domain capabilities.

> **Template First Principle**
> All new MCP servers must be created from this template. Generic capabilities
> are added to the template; server-specific capabilities remain in the
> individual repository. The template evolves independently, and downstream
> projects adopt new template versions through controlled upgrades.

---

## Features

- **Transport-independent core** — Streamable HTTP (default), SSE, and stdio
  behind a single `Transport` abstraction. Business logic never depends on a
  concrete transport.
- **Configuration** — hierarchical loading: bundled defaults → environment
  YAML → environment variables → CLI overrides (Pydantic v2 + YAML).
- **Dependency injection** — small, testable async-capable DI container.
- **Structured logging** — `structlog` with JSON and console renderers.
- **Event bus** — async-first publish/subscribe with subscriber isolation.
- **Tool framework** — `@tool` decorator, metadata models, registry, and input
  validation.
- **Extendable scaffolds** — plugins, middleware, hooks, providers, workers,
  persistence, security, and AI packages with defined extension points.
- **Plugin framework** — minimal plugin architecture with manifest-based discovery,
  lifecycle hooks, and a unified `PluginContext`.
- **Form Automation plugin** — deterministic DOM-based form detection, pre-interaction
  validation, and structured form tools (`fill`, `check`, `uncheck`, `select`, `submit`).
- **Observable** — `/health`, `/live`, `/ready`, `/version` endpoints.
- **Developer tooling** — `uv`, Ruff, Pyright, pytest, pre-commit, Makefile.
- **Operations** — Docker, docker-compose, Kubernetes manifests, GitHub Actions.

## Technology Stack

| Concern         | Choice                        |
| --------------- | ----------------------------- |
| Python          | 3.13                          |
| Package manager | `uv`                          |
| Web framework   | FastAPI                       |
| MCP SDK         | Official Python MCP SDK       |
| Validation      | Pydantic v2                   |
| Config          | pydantic-settings + YAML      |
| Logging         | structlog                     |
| CLI             | Typer                         |
| HTTP server     | Uvicorn                       |
| Testing         | pytest                        |
| Async           | asyncio                       |
| Lint            | Ruff                          |
| Type checking   | Pyright                       |
| Hooks           | pre-commit                    |
| Docs            | MkDocs Material               |
| Containers      | Docker                        |
| Plugins         | Built-in framework            |
| Form Automation | Deterministic DOM + Retry     |

## Quick Start

Prerequisites: [uv](https://docs.astral.sh/uv/) with Python 3.13.

```bash
uv sync --all-extras
make doctor        # verify the environment
make test          # run the test suite
make run           # start the server (http://localhost:8000)
```

Check the server is healthy:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/ready
curl http://localhost:8000/version
```

### CLI

```bash
uv run enterprise-mcp serve            # run the server
uv run enterprise-mcp version          # print version info
uv run enterprise-mcp doctor           # environment diagnostics
uv run enterprise-mcp config --json    # show effective configuration
uv run enterprise-mcp plugins          # list extensions (scaffold)
```

## Repository Layout

```text
src/enterprise_mcp/
├── foundation/     # DI container, app lifecycle, startup/shutdown
├── config/         # loaders, defaults, settings/*.yaml
├── observability/  # logging, metrics, tracing
├── security/       # auth, RBAC, secrets, audit
├── transport/      # base interface, HTTP, SSE, stdio
├── mcp/            # protocol and server abstractions
├── tools/          # decorators, metadata, loader, validator, registry
├── extensions/     # plugins, middleware, hooks, providers
├── workers/        # executors, schedulers, queues, retry
├── persistence/    # repositories, models, migrations, database
├── interfaces/     # REST, WebSocket, internal API
├── events/         # event bus
├── resources/      # templates, static, sample-data
├── utils/          # shared utilities
├── ai/             # memory, prompts, agents (reserved)
└── cli/            # Typer-based CLI
```

## Documentation

- [Architecture](docs/Architecture.md)
- [Design Principles](docs/Design-Principles.md)
- [Compatibility](docs/Compatibility.md)
- [Development Rules](docs/Development-Rules.md)
- [Folder Structure](docs/Folder-Structure.md)
- [Production Checklist](docs/Production-Checklist.md)
- [ADR index](docs/adr/)
- [Element Engine](docs/elements/overview.md)

## License

MIT — see [LICENSE](LICENSE).
