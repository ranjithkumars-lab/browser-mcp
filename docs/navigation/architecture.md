# Architecture

The navigation engine lives in `src/browser_mcp/browser/navigation/` and is
exposed to MCP clients through `src/browser_mcp/tools/navigation.py`.

## Module Layout

```text
src/browser_mcp/browser/navigation/
├── __init__.py        # public package surface
├── _common.py         # shared payloads, event helpers, redirect counting
├── frames.py          # FrameManager: iframe discovery + resolution
├── history.py         # HistoryManager: back / forward
├── interactions.py    # InteractionManager + LocatorResolver
├── manager.py         # NavigationManager: goto / reload
├── policy.py          # NavigationPolicy: domain/scheme/redirect rules
├── state.py           # StateManager: single source of truth
├── timeouts.py        # global timeout resolution
├── waiting.py         # WaitingManager: wait_timeout/navigation/popup/download/url
└── windows.py         # WindowManager: tabs, popups, activation
```

## Layer Diagram

```text
MCP transport
      │
      ▼
NavigationToolkit (tools/navigation.py)  20 tools, JSON in/out
      │
      ├──► NavigationManager ──► NavigationPolicy ──► StateManager
      ├──► HistoryManager  ────────► StateManager
      ├──► FrameManager    ────────► StateManager
      ├──► WindowManager   ────────► StateManager + BrowserPool + PageManager
      ├──► InteractionManager ─► LocatorResolver ─► FrameManager ─► Playwright Locator
      └──► WaitingManager  ────────► WindowManager + PageManager
                                  │
                                  ▼
                          StateManager (hierarchy truth)
```

## Responsibilities

| Manager | Responsibility |
| ------- | -------------- |
| `StateManager` | Track the full `Session → Browser → Context → Page → Frame` hierarchy, frame-guid bindings, popup registry, and id-based lookups. The only layer that owns state. |
| `NavigationPolicy` | Validate URLs (scheme, allowed/blocked domains, allowed ports), enforce redirect limits, and resolve the vendor-neutral `navigation_strategy`. |
| `NavigationManager` | Execute `goto`/`reload`, apply policy, measure timings, record the current URL, and emit `navigation.*` events. |
| `HistoryManager` | Execute `back`/`forward` against the browser's own history. |
| `FrameManager` | Discover frames via Playwright, reconcile them against StateManager, and resolve `frame_id` → live `Frame` objects. |
| `WindowManager` | List tabs/windows, detect and register popups, adopt them into the pool, activate, and close popups. |
| `InteractionManager` | Click, double/right-click, hover, scroll operations. Resolves selectors through `LocatorResolver` only. |
| `WaitingManager` | `wait_timeout`, `wait_navigation`, `wait_popup`, `wait_download`, `wait_url`. |

## LocatorResolver Boundary

Interaction methods **never** call Playwright `Page.click(selector)` directly.
They go through `LocatorResolver`, which targets a frame by `frame_id` (or the
main frame) and returns a Playwright `Locator`. This isolates interaction logic
from element-finding and gives Phase 3 a single seam for locator strategies.

```text
InteractionManager → LocatorResolver → Playwright Locator → click()
```

## Timeouts

Global, configurable timeouts in `src/browser_mcp/config/models.py`
(`TimeoutConfig`), all in milliseconds:

- `default_timeout_ms` — fallback when a caller omits a timeout.
- `navigation_timeout_ms` — `goto`/`reload`/`back`/`forward`.
- `interaction_timeout_ms` — clicks, hovers, scrolls.
- `wait_timeout_ms` — `wait_*` operations that do not override it.

Every tool may override the applicable default with its `timeout_ms` parameter.

## Events

Published on the EventBus using dotted names:

- `navigation.started` — a navigation attempt began.
- `navigation.completed` — navigation finished successfully.
- `navigation.failed` — navigation raised an error.
- `frame.changed` — a frame attached or detached.
- `popup.opened` — a new popup was detected and registered.

## Error Hierarchy

All errors derive from `BrowserError` in `src/browser_mcp/errors.py`:

```text
BrowserError
├── BrowserNotReadyError
├── BrowserNotFoundError
├── BrowserPoolLimitError
├── ContextError
│   └── ContextNotFoundError
├── PageError
│   └── NavigationError
│       ├── NavigationTimeoutError
│       ├── FrameError
│       ├── PopupError
│       ├── InteractionError
│       ├── PolicyViolationError
│       └── DownloadError
├── ProfileError
└── SessionError
    └── SessionNotFoundError
```

Timeouts are enforced both by Playwright's own timeout support and by local
`asyncio.wait_for` guards (popups and downloads), so callers always receive a
deterministic `timeout_ms` contract.

## Metrics

Browser-pool metrics exposed to logs/health: active browsers, active contexts,
active pages, active frames, and open popups.
