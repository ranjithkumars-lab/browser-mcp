# Phase 1: Browser Automation MCP Foundation

This plan details the steps to build the **Browser Automation MCP**, which is a new repository generated from the `enterprise-mcp-server-template`. The generic template remains untouched and reusable.

## Goal

Establish the Browser Automation MCP Foundation by integrating a robust Core Browser Engine (Playwright) into the template infrastructure, alongside a fully functional Streamable HTTP MCP transport.

## Proposed Changes

### 1. Repository Instantiation

- **Instantiate**: Create the `browser-automation-mcp` (in this case, `BROWSER-MCP`) from the `enterprise-mcp-server-template`.
- **Naming**: The internal package will be `browser_mcp`.

### 2. Browser Engine Architecture

We will implement an independent and hierarchical browser engine in `src/browser_mcp/browser/`:

- `manager.py`: `BrowserManager`
- `factory.py`
- `context.py`: `ContextManager`
- `page.py`: `PageManager`
- `profile.py`: `ProfileManager`
- `session.py`: `SessionManager`

### 3. Browser Pool & State

- **Hierarchy**: Implement a strict resource hierarchy: `Pool` -> `Browser` -> `Context` -> `Page`.
- **Profiles**: Add profile management supporting `temporary/`, `persistent/`, and `incognito/` profiles.
- **State Identifiers**: Every level will have unique IDs (e.g., `session_id`, `browser_id`, `context_id`, `page_id`).

### 4. Configuration & Errors

- **Browser Configuration**: Add specific configuration options (Engine, Headless, SlowMo, Viewport, Locale, Timezone, Downloads, UserAgent) via configuration files/env vars.
- **Error Hierarchy**: Define specific exceptions (`BrowserError`, `PageError`, `ContextError`, `NavigationError`, `SessionError`) for clean error handling.

### 5. Transport & MCP Tools

- **Transport Priority**: Implement Streamable HTTP (primary), then SSE, then stdio. The transport will not know anything about Playwright.
- **Structured Tools**: Expose hierarchical tools that return structured JSON (e.g., `{"success": true, "session_id": "..."}`) rather than plain strings:
  - `browser.create_session`
  - `browser.close_session`
  - `browser.create_context`
  - `browser.close_context`
  - `browser.new_page`
  - `browser.close_page`

### 6. Health & Diagnostics

- **Enhanced `/health`**: Extend the `/health` endpoint to report browser pool statistics (e.g., active browsers, contexts, pages).
- **Playwright Installation**: We will _not_ auto-install browsers at startup. We will add `playwright` as a dependency, run `playwright install` during environment setup/Docker build, and return clear runtime errors if binaries are missing.

### 7. Documentation

- Create a `docs/ROADMAP.md` mirroring the planned phases.
- Add docs for: Browser architecture, Session/Context/Page lifecycles, Tool reference, Client usage examples, and Troubleshooting.

## Phase Exit Criteria

- Implementation completed.
- Full test suite passed (Unit -> Integration -> Transport -> Browser -> MCP Tool -> End-to-End).
- Documentation updated.
- Verify the server works with at least one MCP client over Streamable HTTP.
- Verify the Docker image builds successfully.
- User validation, commit, and push to GitHub.
