# Developer Onboarding: Browser MCP (Phases 1-9)

Welcome to the **Browser MCP** project! 

You are joining the project at an exciting time. We have completed Phases 1 through 9, establishing an enterprise-grade **Browser Platform** equipped with an Enhanced Plugin Framework, **Form Automation (Phase 4)**, **Web Scraping (Phase 5)**, **Authentication Engine (Phase 6)**, **Download/Upload Engine (Phase 7)**, and **Browser Events Engine (Phase 8)**.

This document will walk you through the architectural evolution from Phase 1 to Phase 9.

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

Phase 9 elevated the minimal plugin system into an enterprise plugin runtime (`src/browser_mcp/plugins/`).

### Architecture Highlights
1. **Plugin Runtime (`PluginRuntime`)**: Dedicated isolated runtime encapsulating lifecycle ownership and context injection (`BrowserManager`, `AuthManager`, `TransferManager`, `BrowserEventManager`, etc.).
2. **Security & Permissions**: Cryptographic signature validation (`SignatureVerifier`), typed permission scopes (`PluginPermission`), and strict sandbox enforcement (`SandboxPolicy`).
3. **Dependency & Schema Engines**: Dependency resolution graph (`DependencyResolver`) and strict JSON Schema validation for inputs/outputs (`PluginSchemaValidator`).
4. **Separated Registries**: `InstalledPluginRegistry` (on-disk manifest index) vs `ActivePluginRegistry` (running plugin runtimes).
5. **Metadata Caching**: Fast in-memory manifest caching (`PluginMetadataStore`).
6. **MCP Tools**: `browser.plugins.list`, `browser.plugins.info`, `browser.plugins.execute`, `browser.plugins.reload`.

---

## 9. Verification Standard

The codebase is fully verified:
- **Pyright**: 0 errors, 0 warnings.
- **Pytest**: 524 passed tests (100% green).






