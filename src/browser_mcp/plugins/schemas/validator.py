from __future__ import annotations

from typing import Any

from browser_mcp.plugins.errors import PluginSchemaValidationError


class PluginSchemaValidator:
    def validate(self, value: Any, schema: dict[str, Any]) -> None:
        if not schema:
            return
        if schema.get("type") == "object" and not isinstance(value, dict):
            raise PluginSchemaValidationError("value must be an object")
        if isinstance(value, dict):
            for key in schema.get("required", []):
                if key not in value:
                    raise PluginSchemaValidationError(f"required field '{key}' is missing")
            for key, spec in schema.get("properties", {}).items():
                if (
                    key in value
                    and spec.get("type") == "string"
                    and not isinstance(value[key], str)
                ):
                    raise PluginSchemaValidationError(f"field '{key}' must be a string")
