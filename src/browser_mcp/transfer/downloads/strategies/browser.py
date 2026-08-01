from __future__ import annotations

from pathlib import Path
from typing import Any

from browser_mcp.transfer.downloads.strategies.base import BaseDownloadStrategy
from browser_mcp.transfer.provider import TransferProvider


class BrowserDownloadStrategy(BaseDownloadStrategy):
    """Captures the next browser download and persists it to a destination."""

    name = "browser"

    def __init__(self, provider: TransferProvider) -> None:
        self._provider = provider

    async def execute(self, page: Any, **options: Any) -> dict[str, Any]:
        download = options.get("download")
        if download is None:
            download = await self._provider.expect_download(
                page, timeout_ms=options.get("timeout_ms")
            )
        suggested = (
            getattr(download, "suggested_filename", None) or options.get("file_name") or "download"
        )
        destination = Path(options["destination"])
        path = await self._provider.save_download(download, str(destination))
        return {"file_name": Path(suggested).name, "file_path": path}
