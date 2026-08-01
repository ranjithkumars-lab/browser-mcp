# Phase 9 Implementation Plan — Enhanced Plugin Framework & Execution Engine (Refined Enterprise Architecture)

This document details the refined technical implementation plan for **Phase 9: Enhanced Plugin Framework & Execution Engine** (`src/browser_mcp/plugins/`) of the Enterprise Browser MCP Platform. 
In accordance with our **Vibe Coding Rules**, no code will be written until this implementation plan is approved.

---

## 1. Executive Summary & Design Principles

While Phase 4 introduced a minimal plugin framework, **Phase 9** elevates it to a complete enterprise plugin ecosystem with a dedicated execution runtime, dependency management, sandboxing, and schema validation.

> *"Phase 9 extends the minimal plugin framework introduced in Phase 4 into an enterprise plugin runtime while maintaining 100% backward compatibility with existing plugins and manifests."*

### Key Architectural Commitments:
1. **Dedicated Plugin Runtime (`PluginRuntime`)**: Encapsulates lifecycle ownership, context injection, resource limits, and execution cancellation (`PluginRuntime → PluginExecutor`).
2. **Granular Lifecycle State Machine**: Distinguishes `Discovered`, `Installed`, `Validated`, `Loaded`, `Activated`, `Deactivated`, `Unloaded`, `Uninstalled`, `Error`.
3. **Dependency Resolution Engine (`DependencyResolver`)**: Manages plugin dependency graphs, version compatibility, cycle detection, and startup ordering.
4. **Provider Abstraction (`PluginProvider`)**: Insulates plugin sources (`FilePluginProvider`, with `MarketplacePluginProvider` reserved).
5. **Separated Registries**:
   - `InstalledPluginRegistry`: Manages on-disk installed plugin manifests and metadata.
   - `ActivePluginRegistry`: Manages active, loaded plugin runtime instances.
6. **Manifest & API Versioning (`plugin.yaml`)**: Includes `manifest_version: 2`, `api_version: "1"`, `version`, `author`, `category`, `permissions`, `inputs`, `outputs`, `dependencies`, and `signature`.
7. **Typed Permissions & Sandbox Policy**: Typed permission scopes (`PluginPermission(resource, action, scope)`), filesystem limits, network policies, and subprocess restrictions.
8. **Signature Verification (`SignatureVerifier`)**: Validates cryptographic plugin signatures before loading (`PluginTrustValidator`).
9. **Metadata Store & Cache (`PluginMetadataStore`)**: Fast in-memory manifest caching to prevent disk re-parsing.
10. **Full Configuration Schema (`config.plugins.*`)**: Schema covering `plugin_directory`, `auto_discover`, `auto_reload`, `marketplace_enabled`, `verify_signatures`, `max_execution_time`, `max_memory`.

---

## 2. Directory & Component Layout

```text
src/browser_mcp/plugins/
├── __init__.py
├── manager.py            # PluginLifecycleManager facade (orchestration)
├── runtime.py            # PluginRuntime (lifecycle ownership, context binding, cancellation)
├── executor.py           # PluginExecutor (isolated entrypoint invocation)
├── provider.py           # PluginProvider interface & FilePluginProvider
├── registry.py           # InstalledPluginRegistry & ActivePluginRegistry
├── dependency.py         # DependencyResolver (dependency graph & cycle detection)
├── metadata.py           # PluginMetadataStore (manifest cache & checksum index)
├── trust.py              # SignatureVerifier / PluginTrustValidator
├── models.py             # PluginManifest, PluginPermission, PluginState, PluginInput/Output
├── errors.py             # PluginError hierarchy
├── events.py             # Domain event helpers (plugin.discovered, plugin.activated, etc.)
│
├── permissions/          # Security subsystem
│   ├── __init__.py
│   ├── validator.py      # PluginPermissionValidator
│   ├── scope.py          # Typed PluginPermission (resource, action, scope)
│   └── policy.py         # SandboxPolicy (filesystem, network, subprocess limits)
│
├── schemas/              # Validation subsystem
│   ├── __init__.py
│   ├── validator.py      # PluginSchemaValidator (JSON Schema enforcement)
│   └── parser.py         # Manifest Pydantic parser (v1 & v2 backward compatibility)
│
└── tools.py              # MCP tools (browser.plugins.list, info, execute, reload)
```

---

## 3. Detailed Component Specifications

### 3.1. Error Hierarchy (`src/browser_mcp/plugins/errors.py`)
```python
BrowserError
└── PluginError
    ├── PluginNotFoundError
    ├── PluginManifestError
    ├── PluginDependencyError
    │   └── CircularDependencyError
    ├── PluginPermissionDeniedError
    ├── PluginSignatureError
    ├── PluginSchemaValidationError
    ├── PluginLifecycleError
    └── PluginExecutionError
```

### 3.2. Configuration Schema (`config.plugins.*`)
- `plugin_directory`: Root directory for plugins (default `~/.browser_mcp/plugins/`).
- `auto_discover`: Automatically scan and discover plugins on startup (`true`).
- `auto_reload`: Hot-reload plugin manifests on file change (`true`).
- `marketplace_enabled`: Toggles marketplace provider integration (`false`).
- `verify_signatures`: Enforces signature verification during validation (`false` in dev).
- `allow_unsigned`: Allows unsigned local development plugins (`true` in dev).
- `max_execution_time_seconds`: Hard execution timeout per plugin call (default `30.0`).
- `max_memory_mb`: Memory usage limit per plugin runtime (default `256`).

### 3.3. Enhanced Manifest Specification (`plugin.yaml`)
```yaml
manifest_version: 2
api_version: "1"
name: pdf_extractor
version: 1.0.0
author: "Browser MCP Platform Team"
category: "extraction"
description: "Extracts text and tabular structures from PDF documents."
dependencies:
  - "browser.scraper >= 1.0.0"
permissions:
  - resource: "transfer"
    action: "read"
    scope: "artifacts"
  - resource: "element"
    action: "interact"
    scope: "dom"
inputs:
  type: object
  properties:
    pdf_url:
      type: string
  required: ["pdf_url"]
outputs:
  type: object
  properties:
    text:
      type: string
signature: "sig_sha256_987654321"
```

### 3.4. Lifecycle Domain Events (`src/browser_mcp/plugins/events.py`)
- `plugin.discovered`
- `plugin.installed`
- `plugin.validated`
- `plugin.loaded`
- `plugin.activated`
- `plugin.deactivated`
- `plugin.unloaded`
- `plugin.executed`
- `plugin.failed`
- `plugin.permission.denied`
- `plugin.schema.invalid`

### 3.5. MCP Tools (`src/browser_mcp/plugins/tools.py`)
- `browser.plugins.list`: Lists installed & active plugins with health and permission metrics.
- `browser.plugins.info`: Retrieves manifest, schema, and dependency details for a plugin.
- `browser.plugins.execute`: Safely executes a target plugin through `PluginRuntime` with input validation.
- `browser.plugins.reload`: Dynamic runtime reload without restarting the MCP server.

---

## 4. Documentation Strategy (`docs/plugins/`)

Complete documentation suite under `docs/plugins/`:
- `docs/plugins/overview.md`
- `docs/plugins/architecture.md`
- `docs/plugins/manifest-spec.md`
- `docs/plugins/permissions.md`
- `docs/plugins/sandboxing.md`
- `docs/plugins/development-guide.md`
- `docs/plugins/tools.md`

---

## 5. Verification Plan

1. **Unit Tests (`tests/unit/test_plugin_framework_*.py`)**:
   - `DependencyResolver`: Graph ordering, version resolution, and `CircularDependencyError` detection.
   - `PluginPermissionValidator`: Security scope verification and sandbox policy enforcement.
   - `PluginSchemaValidator`: Strict JSON Schema input/output validation.
   - `SignatureVerifier`: Cryptographic signature check & rejection of tampered packages.
   - `PluginMetadataStore`: Manifest caching & checksum indexing.
2. **Integration Tests (`tests/integration/test_plugin_framework_integration.py`)**:
   - End-to-end execution of Form Automation, Web Scraper, and PDF Extractor plugins via `PluginRuntime`.
   - Sandbox isolation test (preventing unauthorized cross-plugin imports or environment leaks).
   - Dynamic plugin loading, activation, hot-reloading, and clean unloading.
3. **Static Analysis**:
   - `uv run pyright` (Target: 0 errors).
   - `uv run pytest` (Target: 100% green pass).
