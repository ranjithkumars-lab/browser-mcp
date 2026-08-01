# Authentication Engine

## Overview

The Authentication Engine (`browser_mcp.auth`) provides a pluggable, strategy-based
system for authenticating browser sessions. It supports form-based logins, direct
cookie injection, and dynamic HTTP header injection (JWT, Bearer, API Keys).

### Goals

- Decouple authentication logic from browser automation internals.
- Persist auth state across context and server restarts.
- Emit structured domain events for observability.
- Provide a clean extension point for future strategies (OAuth, SSO, etc.).

### Key Concepts

| Concept | Description |
|---------|-------------|
| `AuthStrategy` | Pluggable execution unit (form, cookie, header). |
| `AuthProvider` | Browser-driver abstraction (Playwright, CDP, Selenium). |
| `AuthStorageManager` | File-backed state persistence with optional AES-256-GCM encryption. |
| `AuthManager` | Facade orchestrating strategies, storage, and provider calls. |

### Events

The engine publishes the following events on the enterprise `EventBus`:

- `auth.started`
- `auth.success`
- `auth.failed`
- `auth.state.saved`
- `auth.state.loaded`
- `auth.headers.updated`
- `auth.expired`
