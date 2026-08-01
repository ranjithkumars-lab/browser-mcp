from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PluginPermission(BaseModel):
    resource: str = Field(min_length=1)
    action: str = Field(min_length=1)
    scope: str = "*"

    def allows(self, resource: str, action: str, scope: str = "*") -> bool:
        return self.resource == resource and self.action == action and (self.scope in ("*", scope))


class PluginState(StrEnum):
    DISCOVERED = "discovered"
    INSTALLED = "installed"
    VALIDATED = "validated"
    LOADED = "loaded"
    ACTIVATED = "activated"
    DEACTIVATED = "deactivated"
    ERROR = "error"


class PluginManifestV2(BaseModel):
    manifest_version: int = 2
    api_version: str = "1"
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str | None = None
    category: str = "utility"
    entrypoint: str
    tools: list[str] = Field(default_factory=list)
    permissions: list[PluginPermission] = Field(default_factory=lambda: [])
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    signature: str | None = None
