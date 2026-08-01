"""Form Automation Overview."""

# Form Automation

The Form Automation plugin provides deterministic DOM-based form detection
and interaction capabilities for browser automation.

## Features

- **Deterministic form detection** — No AI guessing; uses DOM analysis with
  a strict fallback order.
- **Pre-interaction validation** — Verifies elements are safe to interact with
  before performing any action.
- **Retry policy** — Transient failures are retried with exponential backoff.
- **Namespaced events** — All form actions publish events for observability.
- **Structured results** — Every tool returns a standardised JSON response.

## Tools

| Tool | Description |
|------|-------------|
| `browser.form.fill` | Fill a text input field |
| `browser.form.check` | Check a checkbox or radio |
| `browser.form.uncheck` | Uncheck a checkbox or radio |
| `browser.form.select` | Select an option in a `<select>` |
| `browser.form.submit` | Submit a form |
| `browser.form.fill_many` | Fill multiple fields at once *(reserved)* |

## Detection Fallback Order

1. Explicit CSS selector
2. ARIA attributes
3. Associated `<label>` element
4. `name` attribute
5. `id` attribute
6. `placeholder` attribute

## Validation Pipeline

Before any interaction, the field is validated:

1. **Exists** — Element is present in the DOM.
2. **Visible** — Element is visible on the page.
3. **Enabled** — Element is not disabled.
4. **Editable** — Element accepts text input (for text fields).

## Events

| Event | Published When |
|-------|---------------|
| `form.started` | Any form action begins |
| `form.field.filled` | A field is successfully filled/checked/selected |
| `form.field.failed` | A field action fails |
| `form.validation.failed` | Validation fails |
| `form.submitted` | A form is successfully submitted |