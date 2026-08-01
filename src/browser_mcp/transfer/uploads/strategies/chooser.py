from __future__ import annotations

from typing import Any

from browser_mcp.transfer.provider import TransferProvider
from browser_mcp.transfer.uploads.strategies.base import BaseUploadStrategy


class ChooserUploadStrategy(BaseUploadStrategy):
    name = "chooser"
    def __init__(self, provider: TransferProvider) -> None: self._provider = provider
    async def execute(self, page: Any, *, selector: str, files: list[str], frame_id: str | None = None) -> None:
        chooser = await self._provider.trigger_filechooser(page, selector, frame_id=frame_id)
        await self._provider.set_chooser_files(chooser, files)
