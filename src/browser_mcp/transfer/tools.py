"""MCP tool bindings for the transfer facade."""

from __future__ import annotations

from typing import Any

from browser_mcp.transfer.manager import TransferManager
from enterprise_mcp.tools.decorators import tool


class TransferToolkit:
    def __init__(self, manager: TransferManager, pool: Any, sessions: Any) -> None:
        self._manager, self._pool, self._sessions = manager, pool, sessions

    def _page(self, session_id: str, page_id: str) -> tuple[Any, str, str]:
        browser_id = self._sessions.session_browser_id(session_id)
        handle = self._pool.get_page(page_id)
        if handle.browser_id != browser_id:
            raise ValueError(f"page '{page_id}' does not belong to session '{session_id}'")
        return handle.page, handle.context_id, browser_id

    @tool(name="browser.download", description="Capture and save the next browser download.", returns="json")
    async def download(self, session_id: str, page_id: str, file_name: str | None = None, expected_checksum: str | None = None, timeout_ms: int | None = None) -> dict[str, Any]:
        try:
            page, context_id, browser_id = self._page(session_id, page_id)
            return (await self._manager.download(page, session_id=session_id, browser_id=browser_id, context_id=context_id, page_id=page_id, file_name=file_name, expected_checksum=expected_checksum, timeout_ms=timeout_ms)).to_dict()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @tool(name="browser.upload", description="Upload local files through an input, chooser, or drag-and-drop target.", returns="json")
    async def upload(self, session_id: str, page_id: str, selector: str, files: list[str], strategy: str = "input", frame_id: str | None = None) -> dict[str, Any]:
        try:
            page, context_id, browser_id = self._page(session_id, page_id)
            return (await self._manager.upload(page, selector=selector, files=files, strategy=strategy, frame_id=frame_id, session_id=session_id, browser_id=browser_id, context_id=context_id, page_id=page_id)).to_dict()
        except Exception as exc:
            return {"success": False, "error": str(exc)}

    @tool(name="browser.transfer.status", description="Get transfer lifecycle state and progress.", returns="json")
    async def status(self, transfer_id: str) -> dict[str, Any]:
        try: return (await self._manager.status(transfer_id)).to_dict()
        except Exception as exc: return {"success": False, "error": str(exc), "transfer_id": transfer_id}

    @tool(name="browser.transfer.cancel", description="Cancel an active transfer.", returns="json")
    async def cancel(self, transfer_id: str) -> dict[str, Any]:
        try: return (await self._manager.cancel(transfer_id)).to_dict()
        except Exception as exc: return {"success": False, "error": str(exc), "transfer_id": transfer_id}

    def register(self, registry: Any) -> None:
        for name in ("download", "upload", "status", "cancel"):
            registry.register(getattr(self, name))
