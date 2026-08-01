# ADR 0002: Locked Technology Stack

- **Status:** Accepted
- **Date:** 2026-08-01

## Context

A stable technology stack across all MCP servers reduces cognitive load and
makes maintenance predictable.

## Decision

Lock the initial stack and avoid changing it without a compelling reason:

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

## Consequences

- Consistent downstream servers and onboarding.
- Backend implementations (metrics, tracing, storage) land behind stable
  abstractions without changing the stack.
- Version upgrades are controlled and documented.
