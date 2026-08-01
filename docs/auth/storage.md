# Authentication Storage

## Configuration

Auth state persistence is controlled via `config.auth` in `BrowserSettings`:

```yaml
auth:
  storage_directory: "~/.browser-mcp/auth_states"
  allow_plaintext: false
```

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `storage_directory` | `string` | `~/.browser-mcp/auth_states` | Root directory for persisted auth states. |
| `allow_plaintext` | `bool` | `false` | Allow unencrypted auth state files in development. |

## File Layout

Each browser context gets one file:

```
~/.browser-mcp/auth_states/
├── context_abc123.auth
├── context_def456.auth
└── ...
```

## Encryption

When `allow_plaintext` is `false` (default), states are encrypted with AES-256-GCM.

- **Key derivation**: SHA-256 of the provided key string, or a random 256-bit key if none is provided.
- **Nonce**: 12 random bytes prepended to the ciphertext.
- **Fallback**: If `allow_plaintext` is `true` and no key is configured, data is stored as plain UTF-8 bytes.

## TTL Validation

`TTLValidator` checks:

1. **Cookie expiry** — `is_cookie_valid(cookie)` returns `false` if `expires` is in the past.
2. **Session expiry** — `validate_session(metadata)` raises `SessionExpiredError` if `expires_at` is in the past.

## API

```python
from browser_mcp.auth.storage.manager import AuthStorageManager
from browser_mcp.auth.storage.encryption import AuthEncryptionEngine
from browser_mcp.auth.storage.serializer import StateSerializer

storage = AuthStorageManager(
    directory="~/.browser-mcp/auth_states",
    encryption=AuthEncryptionEngine(key="my-secret-key"),
)

# Save
path = await storage.save("ctx-1", auth_state)

# Load
state = await storage.load("ctx-1")

# Delete
storage.delete("ctx-1")
```
