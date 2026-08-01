# Developer Onboarding: Browser MCP (Phases 1-10)

Welcome to the **Browser MCP** project! 

You are joining the project at an exciting time. We have completed Phases 1 through 10, establishing an enterprise-grade **Browser Platform** equipped with an Enhanced Plugin Framework, **Form Automation (Phase 4)**, **Web Scraping (Phase 5)**, **Authentication Engine (Phase 6)**, **Download/Upload Engine (Phase 7)**, **Browser Events Engine (Phase 8)**, and the **MCP Server Integration (Phase 10)**.

This document will walk you through the architectural evolution from Phase 1 to Phase 10.

---

## 1. Core Architecture (Phases 1 & 2)

At the lowest level, the MCP server translates AI agent requests into Playwright browser actions. We intentionally hid Playwright behind abstract layers to ensure we could swap it out (e.g., for Selenium) without rewriting the engine.

**Key Components in `src/browser_mcp/browser/`:**
- `app.py`: Main MCP server entry point & DI container.
- `manager.py`: `BrowserManager` lifecycle manager.
- `session.py`: `SessionManager` context isolation.
- `navigation/`: High-level navigation actions (`goto`, `back`, `reload`, `wait`).

---

## 2. The Element Engine (Phase 3)

The **Element Engine** (`src/browser_mcp/browser/elements/`) resolves DOM elements, caches locators, and supplies string-based handle references (`element_id`) to AI tools.

---

## 3. The Minimal Plugin Framework & Form Automation (Phase 4)

Phase 4 introduced a **Minimal Plugin Framework** (`src/browser_mcp/plugins/`) and deployed **Form Automation** using verb-oriented tools (`browser.form.fill`, `browser.form.submit`, `browser.form.check`).

---

## 4. The Web Scraping Plugin (Phase 5)

Phase 5 introduced structured scraping (`src/browser_mcp/plugins/scraper/`) with a 4-stage pipeline: `Collector → Normalizer → Formatter → Response`.

---

## 5. The Authentication Engine (Phase 6)

Phase 6 introduced the **Core Authentication Engine** (`src/browser_mcp/auth/`). It provides persistent login, `AuthProvider` abstraction, `AuthStrategyRegistry`, and AES-256-GCM encrypted state storage.

---

## 6. The Download / Upload Engine (Phase 7)

Phase 7 introduced the **Download / Upload Engine** (`src/browser_mcp/transfer/`), providing async file transfer management, strategy registries (`DownloadStrategyRegistry`, `UploadStrategyRegistry`), and `TransferStateManager`.

---

## 7. The Browser Events & Live Monitoring Engine (Phase 8)

Phase 8 introduced the **Browser Events Engine** (`src/browser_mcp/events/`), formalizing and extending the platform's core `EventBus` into a domain-aware event infrastructure.

---

## 8. The Enhanced Plugin Framework & Execution Engine (Phase 9)

Phase 9 elevated the minimal plugin system into an enterprise plugin runtime (`src/browser_mcp/plugins/`), including isolated `PluginRuntime`, `SandboxPolicy`, `SignatureVerifier`, and strict JSON Schema validation.

---

## 9. The MCP Server Integration (Phase 10)

Phase 10 establishes the official **MCP Server** (`src/browser_mcp/server/`) to expose the Browser Core to external AI agents using the standard Model Context Protocol.

### Architecture Highlights
1. **Server Orchestrator (`BrowserMCPServer`)**: The primary server orchestrating tools, events, and sessions.
2. **Transport Abstraction (`TransportProvider`)**: Abstracted network layer supporting:
   - `StreamableHttpTransport` (Primary remote transport).
   - `StdioTransport` (Local sub-process clients).
   - `SseTransport` (Legacy compatibility).
3. **Registry & Capabilities**: `ToolRegistry` managing scoped endpoints, and `CapabilityRegistry` handling protocol handshaking (Tools, Notifications, Resources).
4. **Notification Routing (`NotificationManager`)**: Bridges internal `BrowserEventManager` to MCP clients with active filtering and batching.
5. **Deterministic Error Translation**: Enforces mapping from internal `BrowserError` subclasses to standard JSON-RPC MCP errors.

---

## 10. Verification Standard

The codebase is fully verified:
- **Pyright**: 0 errors, 0 warnings.
- **Pytest**: 100% green pass.






