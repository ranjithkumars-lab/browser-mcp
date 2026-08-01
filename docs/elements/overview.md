# Element Engine Overview

The Element Engine is Phase 3 of the Browser Automation MCP. It provides robust, universal element interaction capabilities using multiple locator strategies (CSS, XPath, ARIA, Text).

## Key Concepts

- **Locator Strategies**: Choose how to find elements using `css`, `xpath`, `aria`, `text`, or raw `playwright` locators.
- **Element ID Caching**: To avoid repeated resolutions, elements are queried once via `find()` to yield an `element_id`. This ID is cached and passed to subsequent actions like `text()` or `click()`.
- **State and Properties**: Quickly extract the state (`exists`, `visible`, `enabled`) or properties (`text`, `html`, `attribute`) of an element.
- **Future-Proof**: The underlying implementation abstracts away the actual browser engine (Playwright), preparing for future extensions.

## Why Element IDs?

Traditional web scraping scripts often resolve the same selector over and over:
```python
if page.locator("#btn").is_visible():
    page.locator("#btn").click()
```
With the Element Engine, we query once:
```json
// Request: browser.element.find {"strategy": "css", "value": "#btn"}
// Response: {"element_id": "element_123"}

// Request: browser.element.state {"element_id": "element_123"}
// Response: {"visible": true}

// Request: browser.element.click {"element_id": "element_123"}
```
This is far more resilient to DOM updates and reduces network overhead when bridging MCP tools to browser actions.
