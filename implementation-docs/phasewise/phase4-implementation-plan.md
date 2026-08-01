# Phase 4: Plugin Framework & Form Automation

## 1. Phase Goal
Develop a **Minimal Plugin Framework** to support extending the server cleanly, and implement the **Enterprise Form Automation engine** as the platform's first plugin. This fulfills the roadmap's requirement for a plugin architecture while delivering robust form interactions (`fill`, `check`, `select`, `submit`) backed by the Element Engine.

## 2. Architecture: Plugin Framework
Before building the form logic, we will introduce a minimal, production-quality plugin framework.

### Proposed Structure
```text
src/browser_mcp/
├── foundation/
│   └── retry.py        # Shared RetryPolicy for forms, scraper, auth, etc.
├── plugins/
│   ├── base.py         # Plugin protocol (initialize, register_tools, health, shutdown)
│   ├── context.py      # PluginContext
│   ├── loader.py       # Discovers and instantiates plugins (yaml or json)
│   ├── manifest.py     # Parses plugin manifests
│   ├── permissions.py  # Minimal permissions placeholder
│   ├── registry.py     # Active plugin registry
│   └── forms/          # Form Automation Plugin
│       ├── __init__.py
│       ├── manifest.yaml
│       ├── detector.py # Deterministic DOM form detection
│       ├── validator.py# Pre-interaction validation
│       ├── actions.py  # Fill, check, select, submit logic
│       └── tools.py    # MCP tool registrations
```

### Architectural Rule: Plugin Isolation
> **Rule**: Plugins must not import other plugins directly. Shared functionality must come from browser core, element engine, plugin context, or shared utilities to avoid hidden dependencies.

### Plugin Lifecycle & Discovery
The `loader.py` handles the discovery process sequentially:
`loader` → `manifest` → `instantiate` → `initialize()` → `register_tools()` → `ready`

### Plugin Context
Every plugin receives a unified context containing:
`BrowserManager, SessionManager, ElementEngine, Logger, Configuration, EventBus, Metrics, StateManager`. 
Plugins never instantiate or import these directly.

### Manifest Definition (`plugin.yaml` or `plugin.json`)
```yaml
name: "browser.form"
version: "0.1.0"
description: "Enterprise form automation and interaction."
permissions:
  - "browser.page"
  - "browser.element"
category: "automation"
tools:
  - "browser.form.fill"
```

## 3. Form Automation Design

### Tool Naming (Verb-Oriented) & Output
The plugin will expose natural, verb-oriented MCP tools:
- `browser.form.fill`
- `browser.form.check`
- `browser.form.uncheck`
- `browser.form.select`
- `browser.form.submit`
- `browser.form.fill_many` *(Status: Reserved - Not implemented until Phase 6)*

Every plugin tool will return a standardized base response:
```json
{
  "success": true,
  "session_id": "...",
  "browser_id": "...",
  "context_id": "...",
  "page_id": "...",
  "duration_ms": 142,
  "message": "Field filled successfully"
}
```

### Deterministic Form Detection
Detection strictly relies on DOM analysis (No AI guessing). The fallback order:
1. Explicit selector
2. ARIA attributes
3. Associated `<label>`
4. `name` attribute
5. `id` attribute
6. `placeholder` attribute

### Standardized Validation
Form actions conceptually separate:
1. **Resolution**: Locating the element via Phase 3.
2. **Validation**: Verifying it is safe to act (`exists`, `attached`, `visible`, `enabled`, `editable`).
3. **Action**: Performing the interaction.

### Events
The form actions publish tightly namespaced events:
- `form.started`
- `form.field.filled`
- `form.field.failed`
- `form.validation.failed`
- `form.submitted`

### Error Hierarchy
Extend domain errors in `errors.py`:
```text
BrowserError
└── FormError
    ├── ValidationError
    ├── FieldNotFoundError
    ├── FieldNotEditableError
    └── SubmitError
```

## 4. Documentation & Testing
### Test Fixtures
`simple-form.html`, `login.html`, `registration.html`, `multi-step.html`, `upload.html`, `search-form.html`.

### Documentation
- `docs/plugins/creating-plugin.md`
- `docs/plugins/plugin-lifecycle.md`
- `docs/plugins/plugin-manifest.md` (Extensive schema definition)
- `docs/forms/overview.md`, `tools.md`, `examples.md`

## 5. Definition of Done
- Shared Retry framework added to `foundation/`.
- Minimal plugin framework implemented (loader, registry, manifest, context, base).
- Plugin base lifecycle handles `health()`.
- Form Automation plugin implemented using the new framework.
- Deterministic detection and separated validation in place.
- Base response model enforced across tools.
- HTML test fixtures updated and > 90% coverage achieved.
- Documentation created.
