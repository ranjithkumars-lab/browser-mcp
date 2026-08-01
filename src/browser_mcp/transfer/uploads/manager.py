from __future__ import annotations

from typing import Any

from browser_mcp.transfer.uploads.strategies.registry import UploadStrategyRegistry
from browser_mcp.transfer.uploads.validator import FileValidator


class UploadManager:
    def __init__(self, registry: UploadStrategyRegistry, validator: FileValidator) -> None:
        self._registry, self._validator = registry, validator

    async def upload(
        self,
        page: Any,
        *,
        selector: str,
        files: list[str],
        strategy: str = "input",
        frame_id: str | None = None,
    ) -> list[dict[str, Any]]:
        metadata = self._validator.validate(files)
        await self._registry.get(strategy).execute(
            page,
            selector=selector,
            files=[str(row["file_path"]) for row in metadata],
            frame_id=frame_id,
        )
        return metadata
