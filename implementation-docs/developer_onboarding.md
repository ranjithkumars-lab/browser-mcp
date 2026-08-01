# Developer Onboarding: Browser MCP (Phases 1-8)

Welcome to the **Browser MCP** project! 

You are joining the project at an exciting time. We have completed Phases 1 through 8, establishing an enterprise-grade **Browser Platform** equipped with a Plugin Framework, **Form Automation (Phase 4)**, **Web Scraping (Phase 5)**, **Authentication Engine (Phase 6)**, **Download/Upload Engine (Phase 7)**, and **Browser Events Engine (Phase 8)**.

This document will walk you through the architectural evolution from Phase 1 to Phase 8.

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

## 3. The Plugin Framework & Form Automation (Phase 4)

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

### Architecture Highlights
1. **Provider Abstraction (`EventProvider`)**: Insulates event dispatch (`InMemoryEventProvider`, with `RedisEventProvider` reserved).
2. **Event Router (`EventRouter`)**: Managed subscriber registry supporting topic pattern matching (`page.*`, `transfer.#`, `*`), priority queueing, and dispatch.
3. **Middleware Pipeline (`EventMiddleware`)**: Supports `LoggingMiddleware`, `MetricsMiddleware`, `AuditMiddleware`, and `SamplingMiddleware`.
4. **Causality & Tracing**: Includes `correlation_id`, `parent_event_id`, and `trace_id` metadata.
5. **In-Memory Ring Buffer (`EventHistoryStore`)**: Retains historical events for log inspection and stream tailing (`browser.events.replay`).
6. **Real-time Streaming (`EventStreamAdapter`)**: Formats event serializations for WebSocket and SSE live streams.
7. **MCP Tools**: `browser.events.listen`, `browser.events.query`, `browser.events.replay`.

---

## 8. Verification Standard

The codebase is fully verified:
- **Pyright**: 0 errors, 0 warnings.
- **Pytest**: 524 passed tests (100% green).






