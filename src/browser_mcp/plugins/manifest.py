"""Plugin manifest parser.

Reads ``plugin.yaml`` / ``plugin.json`` manifests and returns a
structured :class:`PluginManifest` object. Supports both YAML and JSON
formats; YAML is preferred when both are present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

__all__ = ["PluginManifest", "parse_manifest"]


class PluginManifest:
    """Parsed plugin manifest."""

    def __init__(
        self,
        name: str,
        version: str,
        description: str,
        permissions: list[str],
        category: str,
        tools: list[str],
        entrypoint: str,
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.permissions = permissions
        self.category = category
        self.tools = tools
        self.entrypoint = entrypoint

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "permissions": self.permissions,
            "category": self.category,
            "tools": self.tools,
            "entrypoint": self.entrypoint,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PluginManifest:
        return cls(
            name=str(data["name"]),
            version=str(data.get("version", "0.1.0")),
            description=str(data.get("description", "")),
            permissions=list(data.get("permissions", [])),
            category=str(data.get("category", "utility")),
            tools=list(data.get("tools", [])),
            entrypoint=str(data["entrypoint"]),
        )


def parse_manifest(path: Path) -> PluginManifest:
    """Parse a manifest file at ``path`` and return a :class:`PluginManifest`.

    Raises
    ------
    FileNotFoundError
        If ``path`` does not exist.
    ValueError
        If the manifest is missing required fields.
    """
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with open(path, encoding="utf-8") as fh:
        if path.suffix in (".yaml", ".yml"):
            raw: dict[str, Any] = yaml.safe_load(fh) or {}
        elif path.suffix == ".json":
            raw = json.load(fh)
        else:
            raise ValueError(f"Unsupported manifest format: {path.suffix}")

    required = ("name", "entrypoint")
    missing = [field for field in required if field not in raw]
    if missing:
        raise ValueError(f"Manifest missing required fields: {', '.join(missing)}")

    return PluginManifest.from_dict(raw)
