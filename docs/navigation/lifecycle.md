# Lifecycle & State

## Resource Hierarchy

Every live entity is tracked by `StateManager` as the single source of truth:

```text
Session
  └── Browser
        └── Context
              └── Page
                    └── Frame (main + child iframes)
                          └── Popup (a Page opened by another Page)
```

Identifiers are opaque, prefixed strings (`session_*`, `browser_*`,
`context_*`, `page_*`, `frame_*`, `popup_*`) generated at creation. They are
stable for the lifetime of the object and are the only tokens tools use.

## Page Lifecycle

A page moves through these states:

```text
PageCreated ──► PageActivated ──► PageNavigated ──► PageClosed
```

- **PageCreated** — `PageManager` registers a new page in the pool and records
  its `PageState` (`status: open`).
- **PageActivated** — the page becomes the active target for interaction tools.
  Popups are activated automatically when detected via `wait_popup`.
- **PageNavigated** — `NavigationManager.goto`/`reload` and
  `HistoryManager.back`/`forward` update the recorded `url` on the page state.
- **PageClosed** — the page is removed from the pool and its state is marked
  `closed`.

## Frames

Frames are discovered lazily and reconciled on every `list_frames` /
interaction call:

- Each Playwright frame is identified by a stable **driver guid**
  (`frame.guid`, with a private `_guid` fallback) so ids survive wrapper
  recreation.
- Attach/detach transitions emit `frame.changed` events (`action: attached` /
  `action: detached`).
- Interactions target frames by `frame_id`; the main frame is used when
  `frame_id` is omitted.

## Popups & Windows

- A popup is a page opened by another page (window.open, target=_blank,
  downloads, etc.).
- `wait_popup` listens for the popup event, registers the new page in the
  pool, and records a `PopupState` (`status: open`).
- Popups appear in `browser.list_windows` and can be closed with
  `browser.close_popup` or activated with `browser.activate_window`.
- `close_popup` unregisters the page from the pool and marks the popup
  `closed`.

## Events

Lifecycle transitions publish on the EventBus:

| Event | Meaning |
| ----- | ------- |
| `navigation.started` | A `goto`/`reload` began (strategy + timeout included). |
| `navigation.completed` | Navigation finished; page URL updated. |
| `navigation.failed` | Navigation raised an error. |
| `frame.changed` | A frame attached or detached. |
| `popup.opened` | A popup was detected and registered. |

## Metrics

Pool metrics (active browsers, contexts, pages, frames, popups) are derivable
from `StateManager` and surfaced in logs and health payloads.
