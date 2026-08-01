from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from browser_mcp.transfer.downloads.integrity import ChecksumVerifier
from browser_mcp.transfer.downloads.naming import FileNamingStrategy
from browser_mcp.transfer.downloads.strategies.registry import DownloadStrategyRegistry
from browser_mcp.transfer.models import ChecksumAlgorithm, CollisionStrategy


class DownloadManager:
    def __init__(self, registry: DownloadStrategyRegistry, naming: FileNamingStrategy, verifier: ChecksumVerifier, *, directory: str, collision_strategy: CollisionStrategy | str, checksum_algorithm: ChecksumAlgorithm | str) -> None:
        self._registry, self._naming, self._verifier = registry, naming, verifier
        self._directory, self._collision_strategy, self._checksum_algorithm = directory, collision_strategy, checksum_algorithm

    async def download(self, page: Any, *, strategy: str = "browser", file_name: str | None = None, expected_checksum: str | None = None, timeout_ms: int | None = None, download: Any = None) -> dict[str, Any]:
        # Browser suggested filenames are unavailable until the event fires;
        # callers may provide one to make collision handling deterministic.
        destination = self._naming.destination(self._directory, file_name or "download", collision_strategy=self._collision_strategy)
        info = await self._registry.get(strategy).execute(page, destination=str(destination), file_name=file_name, timeout_ms=timeout_ms, download=download)
        saved = Path(info["file_path"])
        if file_name is None and info["file_name"] != destination.name:
            final = self._naming.destination(self._directory, str(info["file_name"]), collision_strategy=self._collision_strategy)
            saved.replace(final)
            saved, info["file_path"], info["file_name"] = final, str(final), final.name
        info["file_size_bytes"] = saved.stat().st_size
        info["mime_type"] = mimetypes.guess_type(saved.name)[0] or "application/octet-stream"
        info["checksum"] = self._verifier.verify(saved, algorithm=self._checksum_algorithm, expected=expected_checksum)
        return info
