"""Form Automation Examples."""

# Form Automation Examples

## Fill a Login Form

```python
# Using the MCP tools directly:
await session.call_tool("browser.form.fill", {
    "session_id": session_id,
    "page_id": page_id,
    "field": "email",
    "value": "user@example.com"
})
await session.call_tool("browser.form.fill", {
    "session_id": session_id,
    "page_id": page_id,
    "field": "password",
    "value": "secret"
})
await session.call_tool("browser.form.submit", {
    "session_id": session_id,
    "page_id": page_id,
})
```

## Check a Checkbox

```python
await session.call_tool("browser.form.check", {
    "session_id": session_id,
    "page_id": page_id,
    "field": "terms"
})
```

## Select from a Dropdown

```python
await session.call_tool("browser.form.select", {
    "session_id": session_id,
    "page_id": page_id,
    "field": "country",
    "value": "us"
})
```

## Use an Explicit Selector

```python
await session.call_tool("browser.form.fill", {
    "session_id": session_id,
    "page_id": page_id,
    "field": "username",
    "value": "admin",
    "selector": "#login-form > input[type='text']"
})
```