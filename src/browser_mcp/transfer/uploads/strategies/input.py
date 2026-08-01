from __future__ import annotations

from typing import Any

from browser_mcp.transfer.provider import TransferProvider
from browser_mcp.transfer.uploads.strategies.base import BaseUploadStrategy


class InputUploadStrategy(BaseUploadStrategy):
    name = "input"

    def __init__(self, provider: TransferProvider) -> None:
        self._provider = provider

    async def execute(
        self, page: Any, *, selector: str, files: list[str], frame_id: str | None = None
    ) -> None:
        await self._provider.set_file_input(page, selector, files, frame_id=frame_id)
