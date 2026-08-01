"""Plugin Lifecycle Documentation."""

# Plugin Lifecycle

This document describes the full lifecycle of a plugin in browser-mcp.

## Discovery

At startup, the `PluginLoader` scans the configured plugins directory
recursively for `manifest.yaml` and `manifest.json` files. Each manifest
is parsed and validated.

```
plugins_dir/
├── forms/
│   └── manifest.yaml
├── scraper/
│   └── manifest.yaml
└── auth/
    └── manifest.json
```

## Instantiation

For each discovered manifest, the loader imports the module specified in
the `entrypoint` field and instantiates the class. The entrypoint format
is `module.path:ClassName`.

## Initialisation

After instantiation, `initialize(context)` is called. The plugin receives
a `PluginContext` containing all the services it needs. This is where the
plugin should set up any internal state, register event handlers, or
perform one-time setup.

## Tool Registration

The `register_tools(registry)` method is called so the plugin can expose
MCP tools. The registry is the same `ToolRegistry` used by the core
server.

## Health Checking

The `health()` method is called periodically (or on demand) to report the
plugin's status. It should return a dict with at minimum a `healthy` key.

## Shutdown

When the server is stopping, `shutdown()` is called on every plugin. This
is where the plugin should clean up resources, close connections, and
persist any state.

## Error Handling

If a plugin fails during any lifecycle phase, the error is logged and the
remaining plugins continue to load. A failing plugin does not prevent other
plugins from operating.