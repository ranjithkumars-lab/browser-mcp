from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any


class PluginMetadataStore:
    def __init__(self) -> None: self._manifests: dict[str, Any] = {}; self._checksums: dict[str, str] = {}
    def put(self, manifest: Any, path: Path | None = None) -> None:
        self._manifests[manifest.name] = manifest
        if path and path.exists(): self._checksums[manifest.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    def get(self, name: str) -> Any | None: return self._manifests.get(name)
    def checksum(self, name: str) -> str | None: return self._checksums.get(name)
