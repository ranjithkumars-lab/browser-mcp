# Tool Reference

The following MCP tools are exposed by the Element Engine.

## `browser.element.find`
Resolves a locator (strategy + value) to a cached `element_id`.
**Inputs**:
- `session_id` (string, required)
- `page_id` (string, required)
- `strategy` (enum: `css`, `xpath`, `aria`, `text`, `playwright`, required)
- `value` (string, required)
- `timeout_ms` (integer, optional)
- `strict` (boolean, default `true`)

## `browser.element.find_all`
Resolves all matching elements for a given locator. Returns an array of `element_id`s.
**Inputs**: Same as `find`, except `strict` is implicitly false.

## `browser.element.text`
Returns the visible inner text of an element.
**Inputs**:
- `session_id` (string, required)
- `page_id` (string, required)
- `element_id` (string, required)

## `browser.element.html`
Returns the HTML of an element.
**Inputs**:
- `session_id` (string, required)
- `page_id` (string, required)
- `element_id` (string, required)
- `outer` (boolean, default `false`) - Return `outerHTML` if true, `innerHTML` if false.

## `browser.element.attribute`
Returns the value of a specific attribute on an element.
**Inputs**:
- `session_id` (string, required)
- `page_id` (string, required)
- `element_id` (string, required)
- `name` (string, required) - Attribute name (e.g. `href`, `data-testid`).

## `browser.element.state`
Checks the boolean states of an element. Returns `exists`, `visible`, `enabled`, `editable`, and `checked`.
**Inputs**:
- `session_id` (string, required)
- `page_id` (string, required)
- `element_id` (string, required)
