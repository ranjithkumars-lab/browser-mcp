# Phase 2: Navigation & Basic Interaction Implementation Plan

This plan details the steps to build Phase 2 of the **Browser Automation MCP**, focusing on the Navigation & Basic Interaction Engine, while strictly adhering to the enterprise architecture and vibe coding rules.

## Goal

Implement the complete navigation layer and basic browser interactions (`goto`, `back`, `forward`, `reload`, `wait_*`, `scroll_*`, `hover`, `click`, `double_click`, `right_click`) along with support for Tabs, Windows, Frames, Iframes, and Popups. These capabilities will be exposed as well-structured MCP tools, forming a robust foundation for the Element Engine in Phase 3.

**Crucial Boundary:** Phase 2 does not implement locator strategies. It only consumes the `LocatorResolver` abstraction.

## Proposed Changes

### 1. Architecture & Folder Structure

We will introduce a dedicated `navigation` package within `src/browser_mcp/browser/` to organize the logic:

```text
src/browser_mcp/browser/navigation/
├── manager.py       # Core NavigationManager (goto, reload)
├── history.py       # History management (back, forward)
├── frames.py        # Frame and Iframe context switching
├── windows.py       # Tabs and Popups management
├── interactions.py  # User interactions (click, hover, scroll)
├── state.py         # StateManager (hierarchy tracking)
└── policy.py        # Navigation policies (domains, redirects)
```

### 2. State Management & Page Lifecycle

- **StateManager**: We will introduce a central `StateManager` in `state.py` to track the full hierarchy (`Session` -> `Browser` -> `Context` -> `Page` -> `Frame`). **StateManager is the single source of truth.** No manager should ever own or cache state directly.
- **Page Lifecycle Events**: We will document and track the lifecycle explicitly: `PageCreated` -> `PageActivated` -> `PageNavigated` -> `PageClosed`.

### 3. Navigation Policies

We will implement enterprise-grade policies in `policy.py` to control browsing boundaries. This includes implementing:
- `allowed_domains`, `blocked_domains`
- `allow_redirects`, `max_redirects`
- `allowed_schemes`

And we will reserve the interface for:
- `blocked_extensions`
- `allowed_ports`
- `max_navigation_depth`

### 4. Minimal Internal Locator Abstraction

To prevent deep coupling and prepare for Phase 3, interaction methods (e.g., `click`) will **not** call Playwright's `Page.click(selector)` directly.
Instead, we will introduce a `LocatorResolver` abstraction:

```text
InteractionManager -> LocatorResolver -> Playwright Locator -> click()
```

This isolates the interaction logic from the element-finding logic.

### 5. Browser Events & Metrics

- **EventBus**: We will proactively emit events using dotted naming conventions:
  - `navigation.started`
  - `navigation.completed`
  - `navigation.failed`
  - `popup.opened`
  - `frame.changed`
- **Browser Pool Metrics**: Expose runtime metrics useful for logs and health endpoints:
  - Active Browsers
  - Active Contexts
  - Active Pages
  - Active Frames
  - Open Popups

### 6. MCP Tools & Parameters

We will expose the following well-structured tools over the MCP transport:

- **Navigation**: `browser.goto`, `browser.back`, `browser.forward`, `browser.reload`
  - *Parameter Change*: Use a vendor-neutral `navigation_strategy` (`normal`, `fast`, `complete`).
- **Waiting Tools (Split API)**: `browser.wait_timeout`, `browser.wait_navigation`, `browser.wait_popup`, `browser.wait_download`, `browser.wait_url`, and reserving `browser.wait_element`.
- **Scrolling Tools**: `browser.scroll_to`, `browser.scroll_by`, `browser.scroll_element`
- **Interactions**: `browser.click`, `browser.hover`, `browser.double_click`, `browser.right_click`

### 7. Rich Structured Responses

All tool responses will return structured JSON, universally including full ID tracking and navigation metadata.

Example response:
```json
{
  "success": true,
  "session_id": "sess_123",
  "browser_id": "br_456",
  "context_id": "ctx_789",
  "page_id": "pg_012",
  "url": "https://example.com",
  "title": "Example Domain",
  "status": 200,
  "navigation_time_ms": 320,
  "duration_ms": 325,
  "redirect_count": 0,
  "timestamp": "2026-08-01T12:00:00Z"
}
```

### 8. Timeouts & Error Hierarchy

- **Global Timeouts**: Implement globally configurable timeouts instead of passing them everywhere: `default_timeout`, `navigation_timeout`, `interaction_timeout`.
- **Error Hierarchy**: Implement a clean exception hierarchy:
  ```
  BrowserError
  └── NavigationError
      ├── TimeoutError
      ├── FrameError
      ├── PopupError
      └── InteractionError
  ```

### 9. Code Quality & Testing (Local Fixtures)

- **Testing**: We will **not** test against live external websites (e.g., Google). Instead, we will create local HTML fixtures:
  ```text
  tests/
  └── fixtures/
      └── html/
          ├── simple.html
          ├── iframe.html
          ├── popup.html
          ├── redirect.html
          ├── forms.html
          └── downloads.html
  ```
- **Coverage & Linting**: Maintain >90% test coverage, passing all `ruff` linting and strict `pyright` type checks.

### 10. Documentation & Compatibility

We will replace the single-file documentation with a well-structured directory:
```text
docs/navigation/
├── overview.md
├── architecture.md
├── tools.md
├── lifecycle.md
└── examples.md
```

**Compatibility Documentation**:
We will document the supported configurations for enterprise deployments:
- Supported Playwright version
- Supported browsers (Chromium, Firefox, WebKit)
- Supported operating systems
- Minimum Python version

## Definition of Done

- [ ] Feature implemented
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Ruff passes
- [ ] Pyright passes
- [ ] Documentation updated
- [ ] Examples updated
- [ ] Local verification completed
- [ ] Git committed
- [ ] Git pushed
- [ ] Phase tagged (v0.2.0 or equivalent)
