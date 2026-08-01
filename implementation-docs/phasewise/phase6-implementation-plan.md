# Phase 6 Implementation Plan — Authentication Engine (Revised Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 6: Authentication Engine** of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

The **Authentication Engine** is a **Browser Core service** (located in `src/browser_mcp/auth/`) that provides persistent, enterprise-grade authentication capabilities across browser contexts, sessions, and plugins. 

### Key Architectural Commitments:
1. **Core Service (Not a Plugin)**: Injected via `PluginContext` so all current (Forms, Scraper) and future plugins leverage unified session states.
2. **Provider Abstraction (`AuthProvider`)**: Decouples the Auth Engine from Playwright, mirroring the design of `LocatorProvider` in Phase 3.
3. **Strategy Registry**: Dynamic lookup for authentication strategies (`FormStrategy`, `CookieStrategy`, `HeaderStrategy`).
4. **Modular Storage Engine**: Decoupled into `storage/manager.py`, `encryption.py`, `serializer.py`, and `ttl.py`.
5. **Configurable Encryption & Location**: Configurable path defaulting to `~/.browser_mcp/auth_states/` with AES-256-GCM encryption.
6. **Explicit Error & Event Hierarchy**: Inherits from `BrowserError` and emits Domain Events on `EventBus`.
7. **OAuth Reservation**: OAuth authentication is explicitly deferred to a dedicated sub-phase; clear extension interfaces are provided.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/auth/
├── __init__.py
├── manager.py          # AuthManager facade (orchestration only)
├── provider.py         # AuthProvider interface & PlaywrightAuthProvider implementation
├── registry.py         # AuthStrategyRegistry for dynamic lookup
├── models.py           # Typed domain models (AuthCredentials, AuthState, CookieCollection, etc.)
├── errors.py           # AuthenticationError hierarchy
├── events.py           # Domain event helpers (auth.started, auth.success, etc.)
│
├── storage/            # Modular storage subsystem
│   ├── __init__.py
│   ├── manager.py      # AuthStorageManager (high-level state I/O)
│   ├── serializer.py   # State serialization/deserialization
│   ├── encryption.py   # AES-256-GCM encryption with plaintext fallback mode
│   └── ttl.py          # Expiration & TTL validator
│
├── strategies/         # Authentication strategies
│   ├── __init__.py
│   ├── base.py         # BaseAuthStrategy ABC
│   ├── form.py         # FormAuthStrategy (username/password login)
│   ├── cookie.py       # CookieAuthStrategy (direct cookie injection)
│   └── header.py       # HeaderAuthStrategy (JWT, Bearer, API Keys)
│
└── tools.py            # MCP tool handlers (browser.auth.*)
```

---

## 3. Detailed Component Specification

### 3.1. Error Hierarchy (`src/browser_mcp/auth/errors.py`)
```python
BrowserError
└── AuthenticationError
    ├── LoginFailedError
    ├── InvalidCredentialsError
    ├── SessionExpiredError
    ├── StateLoadError
    ├── StateSaveError
    ├── CookieInjectionError
    ├── HeaderInjectionError
    └── UnsupportedAuthStrategyError
```

### 3.2. EventBus Integration (`src/browser_mcp/auth/events.py`)
Emits domain events via core `EventBus`:
- `auth.started`
- `auth.success`
- `auth.failed`
- `auth.state.saved`
- `auth.state.loaded`
- `auth.headers.updated`
- `auth.expired`

### 3.3. Provider Abstraction (`src/browser_mcp/auth/provider.py`)
- `AuthProvider`: Abstract interface defining `async def inject_cookies()`, `async def inject_headers()`, `async def extract_storage_state()`, and `async def apply_storage_state()`.
- `PlaywrightAuthProvider`: Concrete adapter insulating core auth logic from Playwright driver internals.

### 3.4. Modular Storage Subsystem (`src/browser_mcp/auth/storage/`)
- `AuthStorageManager`: High-level I/O manager.
- `AuthEncryptionEngine`: AES-256-GCM encryption using standard key derivation from `config.auth.encryption_key`, with dev plaintext fallback (`config.auth.allow_plaintext`).
- `StateSerializer`: Playwright storage state format converter.
- `TTLValidator`: Inspects cookie `expires` timestamps and custom state TTLs.

### 3.5. Strategy Registry (`src/browser_mcp/auth/strategies/`)
- `AuthStrategyRegistry`: Registers and resolves strategies by name (`form`, `cookie`, `header`).
- **OAuth Note**: OAuth 2.0 PKCE / OIDC workflows are deferred to Phase 6.1. The registry reserves `"oauth"` as an extension point (`UnsupportedAuthStrategyError` raised until enabled).

### 3.6. MCP Tools (`src/browser_mcp/auth/tools.py`)
Standardized MCP Tool Response Model:
```json
{
  "success": true,
  "session_id": "s1",
  "browser_id": "b1",
  "context_id": "c1",
  "page_id": "p1",
  "auth_state_id": "state_domain_com_user",
  "expires_at": "2026-08-02T15:00:00Z",
  "duration_ms": 142.5,
  "error": null
}
```

Tools exposed:
- `browser.auth.login`
- `browser.auth.save_state`
- `browser.auth.load_state`
- `browser.auth.set_headers`

---

## 4. Documentation Strategy (`docs/auth/`)

The phase includes complete documentation artifacts:
- `docs/auth/overview.md`
- `docs/auth/architecture.md`
- `docs/auth/tools.md`
- `docs/auth/storage.md`
- `docs/auth/security.md`
- `docs/auth/examples.md`

---

## 5. Verification & Definition of Done

### Verification Plan
1. **Unit Tests (`tests/unit/test_auth_*.py`)**:
   - Strategy registration & resolution.
   - AES-256-GCM encryption, key rotation, and plaintext fallback.
   - TTL expiration logic and corrupted JSON state recovery.
2. **Integration Tests (`tests/integration/test_auth_integration.py`)**:
   - `FormAuthStrategy` mock page login flow.
   - Context persistence: Save state in Context A -> load in Context B.
   - Concurrent storage state access and multi-context isolation.
   - PluginContext auth access (verifying forms/scraper plugins use `AuthManager`).
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).

### Definition of Done Checklist
- [ ] `AuthProvider` interface implemented.
- [ ] `AuthStrategyRegistry` implemented.
- [ ] `AuthenticationError` hierarchy added to `errors.py`.
- [ ] `EventBus` domain events emitted.
- [ ] Modular storage engine (`manager.py`, `encryption.py`, `serializer.py`, `ttl.py`) implemented.
- [ ] AES-256-GCM encryption & configurable storage directory integrated.
- [ ] `AuthManager` injected into `PluginContext`.
- [ ] MCP tools return standardized response schemas.
- [ ] Full documentation added under `docs/auth/`.
- [ ] All unit, integration, and persistence tests passing.
- [ ] Local user verification, git commit, and git push completed.
