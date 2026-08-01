# Compatibility

This document defines the supported platforms, environments, and dependencies
for the Enterprise MCP Server Template. It becomes the compatibility contract
for all servers created from the template.

## Python

- **Supported:** 3.13
- **Development target:** 3.13.x (pinned in `.python-version`)

## Operating Systems

- **Supported:** Windows 10/11, macOS, Linux
- **Tested CI:** Ubuntu latest (GitHub Actions)
- All code is OS-independent; paths and processes are handled through the
  standard library.

## Browser Automation

The navigation engine (Phase 2) is built on Playwright for Python.

- **Playwright:** `>=1.62.0` (tested against `1.62.0`). Browser binaries are
  **not** auto-installed; run `playwright install` first. `browser.doctor` /
  health checks surface missing binaries.
- **Browsers:** Chromium (default), Firefox, WebKit — selected via
  `browser.engine`.
- **Supported OS:** Windows 10/11, macOS, Linux (same matrix as Playwright).
- **Minimum Python:** 3.13.
- **URL schemes:** navigation defaults to `http`, `https`, and `file`
  (`navigation.allowed_schemes`).
- **Downloads:** require an HTTP origin (download events do not fire for
  `file://` URLs) and a configured `browser.downloads_dir`.

## MCP SDK

- **Supported:** official Python MCP SDK `>=1.2,<2.0`
- Protocol versions follow the SDK's negotiated versioning.

## Transports

| Transport        | Status  | Default | Notes                               |
| ---------------- | ------- | ------- | ----------------------------------- |
| streamable-http  | Planned | Yes     | Preferred transport                 |
| sse              | Planned | No      | Legacy compatibility                |
| stdio            | Planned | No      | Local development                   |

Transport implementations are added in a later phase behind the
`Transport` interface. Selection is configured through
`server.transports.default`.

## HTTP / API

- REST interface is served by FastAPI + Uvicorn.
- Endpoints: `/health`, `/live`, `/ready`, `/version`, `/docs`, `/openapi.json`.
- OpenAPI is enabled by default.

## Dependency Policy

- Dependency versions are pinned with upper bounds in `pyproject.toml`.
- Only mature, actively maintained libraries are used.
- The template deliberately does **not** depend on browser automation,
  database drivers, or cloud SDKs. Those belong in downstream servers.

## Versioning

This project follows **Semantic Versioning** (SemVer):

- `MAJOR` — breaking changes to public interfaces or configuration.
- `MINOR` — backward-compatible features and new capabilities.
- `PATCH` — backward-compatible bug fixes.

Breaking changes require:

- an explanation in the changelog,
- migration steps,
- a `MAJOR` version bump,
- documentation updates.

## Environment Variables

All environment variables use the `ENTERPRISE_MCP_` prefix. Nested settings use
`__` as a delimiter, for example:

```text
ENTERPRISE_MCP_ENV=production
ENTERPRISE_MCP_SERVER__TRANSPORTS__PORT=9000
```

See `docs/configuration.md` (when added) and `src/enterprise_mcp/config/`
for the full settings model.
