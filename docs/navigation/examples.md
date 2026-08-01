# Examples

Agent-facing call sequences. Tools live under the `browser.` namespace.

## Create a Session and Navigate

```json
{"tool": "browser.create_session", "input": {"url": "https://example.com"}}
```

```json
{"tool": "browser.goto", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "url": "https://example.com/docs", "navigation_strategy": "complete"}}
```

Response:

```json
{
  "success": true,
  "session_id": "session_ab12cd34ef56",
  "page_id": "page_1234abcd5678",
  "url": "https://example.com/docs",
  "title": "Example Docs",
  "status": 200,
  "navigation_time_ms": 320,
  "redirect_count": 0
}
```

## Back / Forward / Reload

```json
{"tool": "browser.back", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
{"tool": "browser.forward", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
{"tool": "browser.reload", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "navigation_strategy": "fast"}}
```

## Interact with a Page

```json
{"tool": "browser.click", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#submit"}}
```

```json
{"tool": "browser.hover", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#nav-menu"}}
{"tool": "browser.double_click", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#row-3"}}
{"tool": "browser.right_click", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#cell"}}
```

## Scroll

```json
{"tool": "browser.scroll_to", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "x": 0, "y": 2000}}
{"tool": "browser.scroll_by", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "delta_x": 0, "delta_y": 500}}
{"tool": "browser.scroll_element", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#footer", "align": "start"}}
```

## Wait for Conditions

```json
{"tool": "browser.wait_navigation", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "state": "networkidle"}}
{"tool": "browser.wait_url", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "pattern": "**/results/**"}}
```

## Work with Iframes

List the frames, then target a click inside one:

```json
{"tool": "browser.list_frames", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
```

```json
{
  "success": true,
  "page_id": "page_1234abcd5678",
  "frames": [
    {"frame_id": "frame_abc", "page_id": "page_1234abcd5678", "parent_frame_id": null, "name": "", "url": "https://example.com", "is_main": true},
    {"frame_id": "frame_def", "page_id": "page_1234abcd5678", "parent_frame_id": "frame_abc", "name": "widget", "url": "https://widgets.example.com", "is_main": false}
  ]
}
```

```json
{"tool": "browser.click", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678", "selector": "#confirm", "frame_id": "frame_def"}}
```

## Popups

```json
{"tool": "browser.wait_popup", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
```

```json
{"tool": "browser.list_windows", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
{"tool": "browser.activate_window", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_5678abcd1234"}}
{"tool": "browser.close_popup", "input": {"session_id": "session_ab12cd34ef56", "popup_id": "page_5678abcd1234"}}
```

## Downloads

Downloads require an HTTP origin and a configured downloads directory.

```json
{"tool": "browser.wait_download", "input": {"session_id": "session_ab12cd34ef56", "page_id": "page_1234abcd5678"}}
```

```json
{
  "success": true,
  "suggested_filename": "report.csv",
  "path": "C:\\Users\\me\\.browser-mcp\\downloads\\report.csv"
}
```

## Error Handling

Failures return `success: false` with a readable message; the session and page
remain valid and reusable:

```json
{
  "success": false,
  "session_id": "session_ab12cd34ef56",
  "page_id": "page_1234abcd5678",
  "error": "domain 'blocked.example' is blocked by navigation policy"
}
```

## End-to-End Flow

1. `browser.create_session` → session + page ids.
2. `browser.goto` the landing page.
3. `browser.click` to open a form / trigger a popup.
4. `browser.wait_popup` and `browser.activate_window` to switch.
5. `browser.list_frames` + frame-targeted `browser.click` for iframes.
6. `browser.wait_url` / `browser.wait_navigation` for async transitions.
7. `browser.close_popup`, then `browser.close_session` to tear down.
