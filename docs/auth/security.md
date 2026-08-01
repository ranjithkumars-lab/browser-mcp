# Authentication Security

## Threat Model

The auth engine protects browser session credentials and persistent auth state from
unauthorized access and tampering.

## Controls

### 1. Encryption at Rest

All auth state files are encrypted with AES-256-GCM by default.

- **Confidentiality**: Ciphertext cannot be read without the encryption key.
- **Integrity**: GCM authentication tag detects tampering.
- **Key management**: Keys are derived from a configurable secret or generated randomly.

### 2. TTL Enforcement

Auth states are validated against expiry timestamps on load:

- `AuthMetadata.expires_at` — session-level TTL.
- Cookie `expires` attribute — per-cookie TTL.

Expired states raise `SessionExpiredError` and must be re-authenticated.

### 3. Plaintext Fallback (Development Only)

`config.auth.allow_plaintext` disables encryption. This is intended for local
development only and should never be enabled in production.

### 4. Event Isolation

Auth events are published on the enterprise `EventBus`. Failing subscribers are
isolated and logged, preventing auth failures from cascading.

### 5. Strategy Sandboxing

`"oauth"` is reserved as an unsupported strategy. Future OAuth implementations
must opt-in explicitly via `AuthStrategyRegistry.register()`.

## Recommendations

- Store the encryption key in a secrets manager or environment variable.
- Rotate keys periodically.
- Set short TTLs for high-security contexts.
- Monitor `auth.failed` and `auth.expired` events for anomalies.
