"""Plugin Manifest Schema Documentation."""

# Plugin Manifest Schema

Each plugin must include a manifest file (`manifest.yaml` or `manifest.json`)
in its directory. The manifest defines the plugin's identity, permissions,
and capabilities.

## Schema

```yaml
name: string          # Required. Unique plugin identifier.
version: string       # Optional. Semantic version (default: "0.1.0").
description: string   # Optional. Human-readable description.
permissions:          # Optional. List of required permissions.
  - string
category: string      # Optional. Plugin category.
tools:                # Optional. List of tool names provided.
  - string
entrypoint: string    # Required. Module path and class name.
```

## Example

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
  - "browser.form.check"
  - "browser.form.uncheck"
  - "browser.form.select"
  - "browser.form.submit"
entrypoint: "browser_mcp.plugins.forms.tools:FormToolkit"
```

## Field Reference

### `name`

The unique identifier for the plugin. It should follow the reverse-domain
convention (e.g. `browser.form`, `enterprise.scraper`).

### `version`

The semantic version of the plugin. Defaults to `0.1.0` if omitted.

### `description`

A short human-readable description of what the plugin does.

### `permissions`

A list of permission strings the plugin requires. These are checked by
the framework before the plugin is initialised.

### `category`

The plugin category used for grouping and discovery. Common values:
`automation`, `utility`, `integration`, `security`.

### `tools`

The list of MCP tool names this plugin provides. Used for documentation
and discovery.

### `entrypoint`

The Python import path to the plugin class, in the format
`module.path:ClassName`. The class must implement the `Plugin` protocol.