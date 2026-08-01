# MCP Tool Reference

All tools are namespaced under `browser.` and return structured JSON. Unless
noted, every response includes `success`, `session_id`, `page_id`, and
timing/metadata fields. On failure, `success` is `false` and the error message
is returned in the `error` field.

Every tool accepts an optional `timeout_ms` override (except where noted);
otherwise the configured global timeout for that operation class applies.

## Navigation

### `browser.goto`

Navigate a page to a URL and wait until the requested load state.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `session_id` | string | — | Session identifier. |
| `page_id` | string | — | Page identifier. |
| `url` | string | — | Destination URL (http/https/file, subject to policy). |
| `navigation_strategy` | string | `normal` | `fast` → DOM content loaded, `normal` → load event, `complete` → network idle. |
| `timeout_ms` | int? | — | Navigation timeout override. |

Policy (allowed/blocked domains, schemes, redirects) is enforced before and
during the navigation. Redirect counts are validated against
`allow_redirects`/`max_redirects`.

### `browser.reload`

Reload the current page. Same parameters as `browser.goto` (minus `url`).

### `browser.back`

Go back one entry in the page history.

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `session_id` | string | Session identifier. |
| `page_id` | string | Page identifier. |
| `timeout_ms` | int? | Timeout override. |

### `browser.forward`

Go forward one entry in the page history. Same parameters as `browser.back`.

## Waiting

### `browser.wait_timeout`

Sleep for a fixed number of milliseconds (debug/flow-control helper).

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `session_id` | string | Session identifier. |
| `page_id` | string | Page identifier. |
| `milliseconds` | int | Milliseconds to sleep. |

### `browser.wait_navigation`

Wait until the page reaches a load state.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `session_id` | string | — | Session identifier. |
| `page_id` | string | — | Page identifier. |
| `state` | string | `load` | One of `load`, `domcontentloaded`, `networkidle`. |
| `timeout_ms` | int? | — | Timeout override. |

### `browser.wait_popup`

Wait for a popup (new tab/window) opened by the page, and register it.

### `browser.wait_download`

Wait for a download to start on the page. Returns the suggested filename and
path in the configured downloads directory.

### `browser.wait_url`

Wait until the page URL matches a glob pattern (e.g. `**/simple.html`).

| Parameter | Type | Description |
| --------- | ---- | ----------- |
| `session_id` | string | Session identifier. |
| `page_id` | string | Page identifier. |
| `pattern` | string | Playwright URL glob pattern. |
| `timeout_ms` | int? | Timeout override. |

## Scrolling

| Tool | Parameters | Description |
| ---- | ---------- | ----------- |
| `browser.scroll_to` | `session_id`, `page_id`, `x`, `y`, `frame_id?` | Scroll the viewport to absolute `(x, y)`. |
| `browser.scroll_by` | `session_id`, `page_id`, `delta_x`, `delta_y`, `frame_id?` | Scroll the viewport by a relative offset. |
| `browser.scroll_element` | `session_id`, `page_id`, `selector`, `frame_id?`, `align` (`center`/`start`/`end`), `timeout_ms?` | Scroll an element into view. |

## Interactions

Interactions resolve `selector` through the `LocatorResolver`; they can target
an iframe by passing its `frame_id` (see `browser.list_frames`).

### `browser.click`

Click the element matching a selector.

| Parameter | Type | Default | Description |
| --------- | ---- | ------- | ----------- |
| `session_id` | string | — | Session identifier. |
| `page_id` | string | — | Page identifier. |
| `selector` | string | — | Playwright CSS selector. |
| `frame_id` | string? | — | Optional frame to target. |
| `button` | string | `left` | `left`, `right`, or `middle`. |
| `click_count` | int | `1` | Number of clicks to dispatch. |
| `delay_ms` | int? | — | Delay between clicks (for multi-click). |
| `timeout_ms` | int? | — | Timeout override. |

### `browser.hover`

Hover the element matching a selector (`session_id`, `page_id`, `selector`,
`frame_id?`, `timeout_ms?`).

### `browser.double_click`

Double-click the element matching a selector (`session_id`, `page_id`,
`selector`, `frame_id?`, `delay_ms?`, `timeout_ms?`).

### `browser.right_click`

Right-click the element matching a selector (`session_id`, `page_id`,
`selector`, `frame_id?`, `timeout_ms?`).

## Frames & Windows

### `browser.list_frames`

List the frames (iframes) present in a page. Returns an array of frame records:
`frame_id`, `page_id`, `parent_frame_id`, `name`, `url`, `is_main`.

### `browser.list_windows`

List the tabs/windows (pages) in the same context as a page.

### `browser.close_popup`

Close a tracked popup by its popup/page id (`session_id`, `popup_id`).

### `browser.activate_window`

Bring a page (tab/window) to the front of its context (`session_id`,
`page_id`).

## Response Example

```json
{
  "success": true,
  "session_id": "session_ab12cd34ef56",
  "browser_id": "browser_90ab12cd34ef",
  "context_id": "context_78ef90ab12cd",
  "page_id": "page_1234abcd5678",
  "url": "https://example.com",
  "title": "Example Domain",
  "status": 200,
  "navigation_time_ms": 320,
  "redirect_count": 0
}
```
