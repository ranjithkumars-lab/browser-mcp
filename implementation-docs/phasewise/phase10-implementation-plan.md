# Phase 10 Implementation Plan — MCP Server Integration (Refined Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 10: MCP Server Integration** (`src/browser_mcp/server/`) of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

Through Phases 1-9, we built an enterprise-grade Browser Core engine. **Phase 10** establishes the MCP Server integration layer, strictly separating browser automation logic from external protocol transport.

> *"Phase 10 bridges our Browser Core with external AI agents, formalizing standard MCP capabilities, resources, prompts, and unified JSON Schema tool boundaries over pluggable transports."*

### Key Architectural Commitments:
1. **Server Orchestrator (`BrowserMCPServer`)**: The primary MCP application orchestrator interfacing with the internal `AppContext`.
2. **Provider Abstraction (`TransportProvider`)**: Decouples protocol parsing from network layers (`start`, `stop`, `send`, `receive`, `close`).
3. **Transport Implementations**:
   - `StreamableHttpTransport` (Primary remote transport).
   - `StdioTransport` (Local subprocess transport).
   - `SseTransport` (Legacy compatibility).
4. **Tool Registry & Abstraction (`ToolRegistry`)**: Delegates tool definitions into subsystem-specific files (`tools/browser.py`, `tools/auth.py`, `tools/plugins.py`, etc.).
5. **Capability Discovery (`CapabilityRegistry`)**: Advertises and negotiates server capabilities (Tools, Notifications, Resources, Prompts) via protocol handshakes.
6. **Notification Orchestration (`NotificationManager`)**: Bridges `BrowserEventManager` to MCP Clients via filtering, batching, and throttling to prevent transport saturation.
7. **Session Context Management**: Formally maps `MCP Connection → SessionContext → Browser Session(s)`, allowing multi-client and multi-session capabilities.
8. **Deterministic Error Translation**: Enforces formal mapping from all `BrowserError` subclasses to standardized MCP JSON-RPC error codes.
9. **Full Configuration Schema (`config.server.*`)**: Rich configuration controlling timeouts, buffers, limits, and protocol versions.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/server/
├── __init__.py
├── mcp.py                # BrowserMCPServer (core MCP server instance)
├── registry.py           # Core MCP Registry & DI bridging
├── notifications.py      # NotificationManager (filtering, throttling, serialization)
├── capabilities.py       # CapabilityRegistry (tools, resources, prompts negotiation)
├── errors.py             # Error translation table (BrowserError -> MCP Error)
│
├── transports/           # Communication layer abstraction
│   ├── __init__.py
│   ├── provider.py       # TransportProvider interface
│   ├── stdio.py          # Stdio streaming transport
│   ├── streamable_http.py# Streamable HTTP (Primary remote transport)
│   └── sse.py            # Server-Sent Events (Legacy compatibility transport)
│
├── tools/                # Subsystem-specific tool boundaries
│   ├── __init__.py
│   ├── registry.py       # ToolRegistry facade
│   ├── browser.py        # Core Navigation & Lifecycle tools
│   ├── auth.py           # Authentication Engine tools
│   ├── transfer.py       # Download/Upload Engine tools
│   ├── plugins.py        # Enhanced Plugin Framework tools
│   └── scraping.py       # Web Scraper tools
│
└── cli.py                # Rich CLI (serve, doctor, transports, version, plugins, config)
```

---

## 3. Detailed Component Specifications

### 3.1. Error Translation Table (`src/browser_mcp/server/errors.py`)
Provides deterministic mapping to standard JSON-RPC codes:
- `NavigationError` → `InvalidRequest` (-32600)
- `ElementNotFoundError` → `InvalidParams` (-32602)
- `PluginPermissionDeniedError` → `PermissionDenied` (-32000)
- `PluginSchemaValidationError` → `InvalidParams` (-32602)
- `AuthenticationError` → `AuthenticationFailed` (-32001)
- `TransferError` → `InternalError` (-32603)

### 3.2. Configuration Schema (`config.server.*`)
- `default_transport`: `stdio`, `streamable_http`, or `sse` (default `stdio`).
- `protocol_version`: MCP protocol specification version (default `2025-06`).
- `host` & `port`: HTTP bindings (default `127.0.0.1:8000`).
- `request_timeout`: Hard timeout for incoming MCP requests.
- `max_connections`: Concurrent MCP client limits.
- `stream_buffer_size`: Size of HTTP transport buffer.
- `enable_notifications`, `enable_resources`, `enable_prompts`: Capability toggles.

### 3.3. Session Ownership & Connection Context
- Clients establish an `MCP Connection`.
- `BrowserMCPServer` maps this to a `SessionContext`.
- `SessionContext` manages 1 or more `Browser Sessions` via the Browser Core `SessionManager`.

### 3.4. Future Protocol Features
- **Resources**: `browser.logs`, `browser.metrics`, `browser.events.history`, and `browser.artifacts` are reserved via `capabilities.py`.
- **Prompts**: Prompt templating and registries are reserved for future conversational wrappers.

---

## 4. Documentation Strategy (`docs/server/`)

Complete documentation suite under `docs/server/`:
- `docs/server/overview.md`
- `docs/server/transports.md` (Streamable HTTP, Stdio, SSE).
- `docs/server/capabilities.md` (Negotiation and capability registry).
- `docs/server/tools-reference.md`
- `docs/server/error-handling.md`
- `docs/server/cli-usage.md`

---

## 5. Verification Plan

1. **Unit Tests (`tests/unit/test_server_*.py`)**:
   - `TransportProvider` lifecycle (`start`, `stop`, `send`, `receive`).
   - `NotificationManager` event batching, filtering, and payload serialization.
   - Deterministic error code mapping.
   - Subsystem tool registration via `ToolRegistry`.
2. **Integration Tests (`tests/integration/test_server_integration.py`)**:
   - Multiple simultaneous MCP clients handling and protocol negotiation.
   - Reconnect handling and session context restoration.
   - Streamable HTTP connection resilience.
   - Simulated client request executing a `browser.execute_plugin` flow and receiving `BrowserEvent` notifications.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
