# Navigation & Interactions — Overview

Phase 2 adds the **Navigation & Basic Interaction Engine** to the Browser
Automation MCP. It lets agents drive real browser pages through structured,
policy-enforced MCP tools: navigation, waiting, scrolling, interactions,
frames/iframes, tabs/windows, and popups.

## Scope

Included in this phase:

- Navigation: `goto`, `reload`, `back`, `forward`.
- Waiting: `wait_timeout`, `wait_navigation`, `wait_popup`, `wait_download`,
  `wait_url`.
- Scrolling: `scroll_to`, `scroll_by`, `scroll_element`.
- Interactions: `click`, `hover`, `double_click`, `right_click`.
- Frames & windows: `list_frames`, `list_windows`, `close_popup`,
  `activate_window`.
- Navigation policies: allowed/blocked domains, allowed schemes,
  redirect control, reserved extension/port/depth rules.
- Global timeout model: default, navigation, interaction, and wait timeouts.

Explicitly **out of scope** (deferred to Phase 3, the Element Engine):

- Locator strategies and element queries. Phase 2 only consumes the
  `LocatorResolver` abstraction to resolve a selector to a Playwright
  `Locator`; it does not implement selector discovery.
- `wait_element` is reserved but not implemented.

## Key Principles

- **StateManager is the single source of truth.** No manager caches page,
  frame, popup, or window state on its own.
- **Policy first.** Every `goto` is validated against the navigation policy
  before the browser is touched.
- **Structured responses.** Every tool returns JSON with session/page id
  tracking and navigation metadata — never free-form text.
- **Events.** Lifecycle and outcome events (`navigation.*`, `frame.changed`,
  `popup.opened`) are published on the EventBus for observability.

## Contents

- [Architecture](architecture.md) — module layout, responsibilities, event and
  error models.
- [Tools](tools.md) — the complete MCP tool reference.
- [Lifecycle](lifecycle.md) — session → browser → context → page → frame
  hierarchy and page lifecycle.
- [Examples](examples.md) — end-to-end agent call sequences.
