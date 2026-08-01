# Phase 3: Locator & Element Engine Implementation Plan

## 1. Phase Goal
Develop a Universal Locator Engine that supports querying page elements via multiple strategies (CSS, XPath, ARIA, Text) and provides mechanisms to extract element properties and state (`text()`, `html()`, `attribute()`, `exists()`, `visible()`, `enabled()`). This engine will seamlessly integrate with and enhance the `LocatorResolver` from Phase 2, while introducing an `element_id` abstraction to optimize repeated interactions.

## 2. Scope
- Implementing locator strategies (CSS, XPath, ARIA, Playwright, Text).
- Exposing element property extraction and state checking methods.
- Refactoring `LocatorResolver` to utilize these strategies cleanly.
- Introducing a `LocatorProvider` interface to decouple `ElementEngine` from Playwright.
- Introducing an `element_id` cache/abstraction.
- *Out of Scope*: Form automation (Phase 4), advanced Web Scraping (Phase 5).
- *Strict Rule*: This plan does not introduce functionality that belongs to future phases unless it is required as a non-functional abstraction (e.g., interfaces, extension points). Any such abstraction is clearly identified as preparatory and does not implement future-phase behavior.

## 3. Architecture Overview
The Element Engine acts as a robust middle layer between the MCP interface and the underlying browser automation engine. 
To adhere to the Open/Closed Principle and decouple our framework from Playwright:
```text
ElementEngine -> LocatorProvider (Interface) -> PlaywrightLocatorProvider -> Playwright
```
This ensures that the core engine coordinates resolution and state tracking, while the provider executes the actual browser commands, keeping the door open for Selenium or CDP in the future.

Furthermore, `find()` calls will resolve to an `element_id`, which is temporarily cached. Subsequent actions like `text()` or `click()` (from Phase 2) will consume this `element_id` rather than re-evaluating the locator.

## 4. New Components
- `ElementEngine`: Core facade coordinating finding and querying elements.
- `LocatorProvider`: Interface isolating the underlying browser engine (Playwright).
- `LocatorRegistry`: Registers and resolves different locator strategies (css, xpath, aria, etc.).
- `ElementProperties`: Extractors for `text`, `html`, and `attributes`.
- `ElementState`: Validators for `exists`, `visible`, `enabled`, `editable`, `checked`.

## 5. Folder Structure Changes
```text
src/browser_mcp/browser/elements/
├── __init__.py
├── engine.py           # Core ElementEngine API facade
├── provider.py         # LocatorProvider interface (Playwright decoupling)
├── properties.py       # Element property extraction
├── state.py            # Element state checks
├── resolver.py         # Upgraded LocatorResolver from Phase 2
└── locators/           # Strategy Implementations
    ├── __init__.py
    ├── registry.py     # Strategy coordinator
    ├── css.py
    ├── xpath.py
    ├── aria.py
    ├── text.py
    └── playwright.py
```

## 6. Internal Design
- **Locator Model**: A structured, future-proofed Pydantic model:
  ```json
  {
    "strategy": "xpath",
    "value": "//div",
    "timeout": 5000,
    "strict": true
  }
  ```
- **Element ID Abstraction**: The `ElementEngine` will map `element_id` to a resolved Playwright handle/locator. This avoids repeated resolution during chained interactions.
- **Preparatory Abstraction**: `ElementState` will return `editable` and `checked` status as placeholders to align perfectly with Phase 4 (Form Automation).

## 7. MCP Tool Design
Exposed tools will output structured JSON with full ID hierarchy (`session_id`, `browser_id`, `context_id`, `page_id`), `element_id`, and `duration_ms`.
- `browser.element.find` (params: `page_id`, `strategy`, `value`, `timeout`, `strict` -> returns `element_id`)
- `browser.element.find_all` (params: `page_id`, `strategy`, `value`)
- `browser.element.state` (params: `page_id`, `element_id` -> returns `exists`, `visible`, `enabled`, `editable`, `checked`)
- `browser.element.text` (params: `page_id`, `element_id`)
- `browser.element.html` (params: `page_id`, `element_id`, `outer: bool`)
- `browser.element.attribute` (params: `page_id`, `element_id`, `attribute_name`)

## 8. Configuration Changes
No new configuration parameters are strictly required. Global timeouts from Phase 2 (`interaction_timeout`) will be used as the default if `timeout` is not provided in the Locator Model.

## 9. Logging & Observability
- All queries and state checks will be logged at the `DEBUG` level.
- Integrate with Phase 2's EventBus utilizing dotted naming conventions:
  - `element.resolved`
  - `element.found`
  - `element.not_found`
  - `element.state_changed`

## 10. Error Handling
Extend the established Error Hierarchy:
```text
BrowserError
└── ElementError
    ├── ElementNotFoundError
    ├── InvalidLocatorStrategyError
    ├── ElementStateError (e.g., querying text of a hidden element)
    └── StaleElementReferenceError
```

## 11. Testing Strategy
- **Local HTML Fixtures**: We will massively expand local fixtures for robust testing coverage:
  ```text
  tests/fixtures/html/
  ├── elements.html
  ├── shadow-dom.html
  ├── nested-frames.html
  ├── aria.html
  └── dynamic.html
  ```
- **Unit Tests**: Test the `LocatorRegistry` and individual strategies.
- **Integration Tests**: Verify end-to-end MCP tool calls for finding elements and extracting properties.

## 12. Documentation Updates & Shadow DOM Policy
- **Shadow DOM Policy**: 
  - Open Shadow DOM: Fully supported.
  - Closed Shadow DOM: Not supported unless browser engine capabilities change natively.

```text
docs/elements/
├── overview.md
├── architecture.md
├── locators.md
├── examples.md
└── tool-reference.md
```

## 13. Risks
- **Stale Element References**: Caching `element_id` introduces the risk of stale references after heavy DOM mutations.
- **Race Conditions**: Rapidly changing dynamic pages may cause sporadic `ElementNotFoundError`.
*Mitigation*: We will leverage Playwright's auto-waiting within the provider layer where appropriate, and document the risks of holding `element_id`s for long periods.

## 14. Verification Plan
1. Stand up the MCP server locally.
2. Serve the `tests/fixtures/html/` fixtures via a local static server.
3. Use a real MCP client to call `browser.element.find` to retrieve an `element_id`.
4. Pass the retrieved `element_id` to `browser.element.text` and verify correct extraction.
5. Validate that Phase 2's `InteractionManager` correctly consumes the new `LocatorResolver` and `element_id`.

## 15. Definition of Done
- [ ] Feature implemented
- [ ] Unit tests pass (>90% coverage)
- [ ] Integration tests pass
- [ ] Ruff passes
- [ ] Pyright passes
- [ ] Documentation updated
- [ ] Examples updated
- [ ] Local verification completed
- [ ] MCP tools verified from a real MCP client
- [ ] Git committed
- [ ] Git pushed
- [ ] Phase tagged (v0.3.0)
