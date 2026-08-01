"""Plugin Framework Documentation."""

# Creating a Plugin

Every plugin in browser-mcp follows a simple protocol and is discovered
automatically at startup.

## Plugin Protocol

A plugin is any class that implements the :class:`~browser_mcp.plugins.base.Plugin`
protocol:

```python
from browser_mcp.plugins.base import Plugin

class MyPlugin(Plugin):
    async def initialize(self, context: PluginContext) -> None:
        ...

    def register_tools(self, registry: Any) -> None:
        ...

    async def health(self) -> dict[str, Any]:
        return {"healthy": True}

    async def shutdown(self) -> None:
        ...
```

## Lifecycle

1. **Discovery** — The `PluginLoader` scans the plugins directory for
   `manifest.yaml` files.
2. **Instantiation** — The entrypoint class is imported and instantiated.
3. **Initialisation** — `initialize(context)` is called with the plugin context.
4. **Tool Registration** — `register_tools(registry)` registers MCP tools.
5. **Ready** — The plugin is now active and its tools are available.

## Plugin Context

Every plugin receives a `PluginContext` providing access to:

- `app_context` — The runtime application context.
- `container` — The dependency injection container.
- `browser_manager` — Browser lifecycle management.
- `browser_pool` — The browser resource pool.
- `session_manager` — Session lifecycle management.
- `element_engine` — Element finding and state queries.
- `state_manager` — Navigation state management.
- `event_bus` — The async pub/sub event bus.
- `settings` — The effective configuration.
- `tools` — The tool registry for registering new tools.
- `logger` — A structured logger.

## Manifest

Each plugin directory must contain a `manifest.yaml` or `manifest.json`:

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
entrypoint: "browser_mcp.plugins.forms.tools:FormToolkit"
```

### Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique plugin identifier (e.g. `browser.form`). |
| `version` | No | Semantic version (default: `0.1.0`). |
| `description` | No | Human-readable description. |
| `permissions` | No | List of permission strings the plugin requires. |
| `category` | No | Plugin category (e.g. `automation`, `utility`). |
| `tools` | No | List of tool names provided by this plugin. |
| `entrypoint` | Yes | `module.path:ClassName` of the plugin class. |