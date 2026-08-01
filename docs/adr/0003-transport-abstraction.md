# ADR 0003: Transport Abstraction

- **Status:** Accepted
- **Date:** 2026-08-01

## Context

MCP supports multiple transports: Streamable HTTP, SSE, and stdio. Business
logic should not depend on how requests arrive.

## Decision

Define a single `Transport` interface (`start()`, `stop()`, `handle()`).
Provide registry and factory plumbing in Phase 0. Streamable HTTP is the
default transport; SSE is kept for legacy compatibility and stdio for local
development. All transports sit behind the same abstraction.

## Consequences

- Business logic is transport-independent.
- New transports can be added by implementing the interface and registering it.
- Transport implementations are deferred to later phases; the extension point
  is fixed now.
