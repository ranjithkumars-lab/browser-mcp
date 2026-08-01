# Authentication Tools

## `browser.auth.login`

Authenticate against a browser context using the configured strategy.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | `string` | Yes | — | Browser session identifier. |
| `context_id` | `string` | Yes | — | Browser context identifier. |
| `strategy` | `string` | No | `"form"` | Auth strategy: `form`, `cookie`, or `header`. |
| `username` | `string` | No | — | Login username or email. |
| `password` | `string` | No | — | Login password. |
| `url` | `string` | No | `""` | Target URL for the login page. |
| `headers` | `object` | No | `{}` | Extra HTTP headers. |
| `cookies` | `object` | No | `{}` | Extra cookies (name → value). |
| `metadata` | `object` | No | `{}` | Strategy-specific extra data. |

### Returns

```json
{
  "success": true,
  "session": {
    "session": {
      "session_id": "ses-1",
      "context_id": "ctx-1",
      "authenticated": true,
      "metadata": { ... }
    },
    "state_id": "...",
    "created_at": "...",
    "updated_at": "..."
  },
  "duration_ms": 42.5
}
```

---

## `browser.auth.save_state`

Persist the current auth state for a context to disk.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | `string` | Yes | — | Browser session identifier. |
| `context_id` | `string` | Yes | — | Browser context identifier. |

### Returns

```json
{
  "success": true,
  "path": "/home/user/.browser-mcp/auth_states/ctx-1.auth"
}
```

---

## `browser.auth.load_state`

Load a previously persisted auth state for a context.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `context_id` | `string` | Yes | — | Browser context identifier. |

### Returns

```json
{
  "success": true,
  "state": { ... }
}
```

---

## `browser.auth.set_headers`

Inject dynamic HTTP headers into a browser context.

### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `session_id` | `string` | Yes | — | Browser session identifier. |
| `context_id` | `string` | Yes | — | Browser context identifier. |
| `headers` | `object` | Yes | — | Header name → value mapping. |

### Returns

```json
{
  "success": true,
  "headers_injected": ["Authorization"]
}
```
