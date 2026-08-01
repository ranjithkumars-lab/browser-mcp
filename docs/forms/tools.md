"""Form Automation Tools Reference."""

# Form Automation Tools

## `browser.form.fill`

Fill a text input field with a value.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session identifier. |
| `page_id` | string | Yes | The page identifier. |
| `field` | string | Yes | The field name, id, or placeholder. |
| `value` | string | Yes | The value to fill. |
| `selector` | string | No | An explicit CSS selector. |

**Returns:**

```json
{
  "success": true,
  "session_id": "...",
  "browser_id": "...",
  "context_id": "...",
  "page_id": "...",
  "duration_ms": 142,
  "message": "Field filled successfully"
}
```

## `browser.form.check`

Check a checkbox or radio button.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session identifier. |
| `page_id` | string | Yes | The page identifier. |
| `field` | string | Yes | The field name, id, or placeholder. |
| `selector` | string | No | An explicit CSS selector. |

## `browser.form.uncheck`

Uncheck a checkbox or radio button.

**Parameters:** Same as `browser.form.check`.

## `browser.form.select`

Select an option in a `<select>` element.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session identifier. |
| `page_id` | string | Yes | The page identifier. |
| `field` | string | Yes | The field name, id, or placeholder. |
| `value` | string | Yes | The option value to select. |
| `selector` | string | No | An explicit CSS selector. |

## `browser.form.submit`

Submit a form.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | string | Yes | The session identifier. |
| `page_id` | string | Yes | The page identifier. |
| `field` | string | No | A submit button selector. |
| `selector` | string | No | An explicit CSS selector. |