# Developer Onboarding: Browser MCP (Phases 1-5)

Welcome to the **Browser MCP** project! 

You are joining the project at an exciting time. We have completed Phases 1 through 5, establishing an enterprise-grade **Browser Platform** equipped with a Plugin Framework and plugins for **Form Automation (Phase 4)** and **Web Scraping (Phase 5)**.

This document will walk you through the architectural evolution from Phase 1 to Phase 5.

---

## 1. Core Architecture (Phases 1 & 2)

At the lowest level, the MCP server translates AI agent requests into Playwright browser actions. We intentionally hid Playwright behind abstract layers to ensure we could swap it out (e.g., for Selenium) without rewriting the engine.

**Key Components in `src/browser_mcp/browser/`:**
- `app.py`: The main MCP server entry point and Dependency Injection container.
- `manager.py` (`BrowserManager`): Handles browser instance lifecycle (launching Chromium).
- `session.py` (`SessionManager`): Manages isolated browser contexts (incognito windows, storage state).
- `page.py`: Wrapper for managing tabs.
- `navigation/`: The Navigation Engine (Phase 2), providing high-level tools like `goto`, `back`, `reload`, and `wait`.

---

## 2. The Element Engine (Phase 3)

In Phase 3, we built the **Element Engine** (`src/browser_mcp/browser/elements/`). 
AI agents cannot easily pass complex Playwright DOM references back and forth through the MCP protocol. Therefore, we needed a way to resolve DOM elements, cache them, and hand a simple string (`element_id`) back to the AI.

**How it works:**
1. The AI calls a tool like `browser.element.find` with a strategy (`css`, `xpath`, `aria`, `text`) and a value (e.g., `#submit-btn`).
2. The `ElementEngine` instructs the `LocatorProvider` to resolve the element in the DOM.
3. The engine caches this locator and generates an `element_id` (e.g., `elem_123`).
4. The AI receives `elem_123` and can pass it to subsequent tools (like `browser.element.text` or plugins) to interact with that exact element safely.

---

## 3. The Plugin Framework & Form Automation (Phase 4)

Phase 4 introduced a **Minimal Plugin Framework** and deployed our first plugin: **Form Automation**.

**The Framework (`src/browser_mcp/plugins/`):**
- **`manifest.py`**: Parses `plugin.yaml` files defining a plugin's name, version, tools, and permissions.
- **`loader.py` & `registry.py`**: Discovers plugins, parses their manifests, and registers them dynamically.
- **`context.py`**: The `PluginContext` injects core services (like `BrowserManager`, `ElementEngine`, and `Logger`) into plugins securely.
- **Rule of Isolation**: Plugins are forbidden from importing other plugins directly. They communicate via the core `EventBus` or shared models.

**The Form Automation Plugin (`src/browser_mcp/plugins/forms/`):**
- Uses **verb-oriented tools** (`browser.form.fill`, `browser.form.submit`, `browser.form.check`).
- **`detector.py`**: Deterministically resolves fields using strict priority.
- **`validator.py`**: Validates element safety (`exists`, `visible`, `editable`) before taking action.
- **`actions.py`**: Executes form inputs safely leveraging `RetryPolicy`.

---

## 4. The Web Scraping Plugin (Phase 5)

Phase 5 introduced structured web scraping capabilities housed in `src/browser_mcp/plugins/scraper/`.

### Pipeline Architecture
The scraper processes structured web data through a 4-stage pipeline:
`Collector → Normalizer → Formatter → Response`

1. **Collectors (`src/browser_mcp/plugins/scraper/collectors/`)**: Extract raw structured elements from web pages (`TextCollector`, `TableCollector`, `ImagesCollector`, `MetadataCollector`, `JsonLdCollector`, `LinksCollector`, `ProductCollector`).
2. **Normalizers (`src/browser_mcp/plugins/scraper/normalizers/`)**: Transform raw collected structures into strongly-typed domain models (e.g., `ProductNormalizer`).
3. **Formatters (`src/browser_mcp/plugins/scraper/formatters/`)**: Convert data into output formats (`json`, `csv`, `markdown`, `html`).
4. **MCP Tools**: Exposed via tools `browser.scraper.text`, `browser.scraper.table`, `browser.scraper.images`, `browser.scraper.metadata`, `browser.scraper.jsonld`, `browser.scraper.links`, `browser.scraper.product`.

---

## 5. Verification Standard

The codebase is fully verified:
- **Pyright**: 0 errors, 0 warnings.
- **Pytest**: 480 passed tests (100% green).



