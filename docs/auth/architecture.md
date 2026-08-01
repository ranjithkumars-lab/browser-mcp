# Authentication Architecture

## Layered Design

```
+-------------------+     +------------------+     +-----------------+
|   MCP Tools       | --> |   AuthManager    | --> |   Strategies    |
| (browser.auth.*)  |     |   (Facade)       |     | (form/cookie/   |
+-------------------+     +------------------+     |  header)        |
                                                +-----------------+
                                                       |
                                                       v
                                                +------------------+
                                                |   AuthProvider   |
                                                | (Playwright)     |
                                                +------------------+

+-------------------+     +------------------+     +-----------------+
|   AuthStorage     | <-- |   AuthManager    | --> |   AuthEvents    |
|   (file + crypto) |     |   (Facade)       |     | (EventBus)      |
+-------------------+     +------------------+     +-----------------+
```

## Components

### 1. Domain Models (`auth/models.py`)

- `AuthCredentials` — login payload (username, password, URL, headers, cookies, metadata).
- `AuthHeaders` — structured HTTP header injection map.
- `CookieCollection` — Playwright-style cookie list.
- `AuthMetadata` — immutable audit metadata (strategy, timestamps, expiry).
- `AuthSession` — active session state (authenticated flag + metadata).
- `AuthState` — serialisable snapshot containing an `AuthSession`.

### 2. Errors (`browser_mcp.errors`)

New error hierarchy under `AuthenticationError`:

- `AuthError` — base for auth subsystem failures.
- `LoginFailedError` — login attempt failed.
- `SessionExpiredError` — auth session TTL exceeded.
- `StateLoadError` / `StateSaveError` — persistence failures.
- `UnsupportedAuthStrategyError` — strategy not registered.

### 3. Events (`auth/events.py`)

Thin `DomainEvent` subclasses with namespaced names (`auth.*`). Emitted asynchronously
via the enterprise `EventBus`.

### 4. Provider (`auth/provider.py`)

`AuthProvider` isolates the auth subsystem from the underlying browser library.
`PlaywrightAuthProvider` wraps `BrowserContext`:

- `inject_cookies(context, cookies)`
- `inject_headers(context, headers)`
- `extract_storage_state(context)`
- `apply_storage_state(context, state)`

### 5. Storage Subsystem (`auth/storage/`)

| Module | Responsibility |
|--------|---------------|
| `serializer.py` | JSON serialise/deserialise Playwright `storage_state`. |
| `encryption.py` | AES-256-GCM encryption with `allow_plaintext` fallback. |
| `ttl.py` | Validate cookie `expires` and session `expires_at`. |
| `manager.py` | High-level file I/O using `config.auth.storage_directory`. |

### 6. Strategies (`auth/strategies/`)

- `BaseAuthStrategy` — abstract `execute(context, credentials)`.
- `AuthStrategyRegistry` — dynamic lookup; `"oauth"` reserved as unsupported.
- `FormAuthStrategy` — navigates to URL, fills form, waits for network idle.
- `CookieAuthStrategy` — injects name/value dict as Playwright cookies.
- `HeaderAuthStrategy` — calls `set_extra_http_headers`.

### 7. Manager (`auth/manager.py`)

`AuthManager` is the single entry point for auth operations:

1. `login(context, credentials)` — looks up strategy, emits events, persists state.
2. `save_state(context_id, session_id, state)` — persists state to disk.
3. `load_state(context_id)` — loads and validates state (TTL check).
4. `set_headers(context, headers, ...)` — injects headers and emits event.

### 8. PluginContext Integration

`PluginContext` now exposes `auth_manager` so plugins (Forms, Scraper) can
perform authenticated operations.

### 9. MCP Tools (`auth/tools.py`)

`AuthToolkit` registers four tools under the `browser.auth` namespace:

- `browser.auth.login`
- `browser.auth.save_state`
- `browser.auth.load_state`
- `browser.auth.set_headers`
