"""Top-level transfer facade coordinating strategies, state, and events."""

from __future__ import annotations

import time
from typing import Any

from browser_mcp.transfer.downloads.manager import DownloadManager
from browser_mcp.transfer.events import (
    emit_download_completed,
    emit_download_failed,
    emit_download_started,
    emit_upload_completed,
    emit_upload_failed,
    emit_upload_started,
)
from browser_mcp.transfer.models import TransferResponse, TransferStatus
from browser_mcp.transfer.state import TransferStateManager
from browser_mcp.transfer.uploads.manager import UploadManager


class TransferManager:
    def __init__(
        self,
        downloads: DownloadManager,
        uploads: UploadManager,
        state: TransferStateManager,
        event_bus: Any,
    ) -> None:
        self._downloads, self._uploads, self._state, self._events = (
            downloads,
            uploads,
            state,
            event_bus,
        )

    async def download(
        self,
        page: Any,
        *,
        session_id: str | None = None,
        browser_id: str | None = None,
        context_id: str | None = None,
        page_id: str | None = None,
        **options: Any,
    ) -> TransferResponse:
        transfer_id = await self._state.register(
            "browser.download",
            metadata={
                "session_id": session_id,
                "browser_id": browser_id,
                "context_id": context_id,
                "page_id": page_id,
            },
        )
        started = time.perf_counter()
        await self._state.transition(transfer_id, TransferStatus.RUNNING)
        await emit_download_started(
            self._events,
            transfer_id=transfer_id,
            session_id=session_id,
            browser_id=browser_id,
            context_id=context_id,
            page_id=page_id,
            file_name=options.get("file_name"),
            strategy=options.get("strategy", "browser"),
        )
        try:
            data = await self._downloads.download(page, **options)
            await self._state.update_progress(
                transfer_id,
                transferred_bytes=data["file_size_bytes"],
                total_bytes=data["file_size_bytes"],
            )
            await self._state.transition(transfer_id, TransferStatus.COMPLETED)
            duration = (time.perf_counter() - started) * 1000
            await emit_download_completed(
                self._events,
                transfer_id=transfer_id,
                file_name=data["file_name"],
                file_path=data["file_path"],
                file_size_bytes=data["file_size_bytes"],
                mime_type=data["mime_type"],
                checksum=data["checksum"].model_dump(mode="json"),
                duration_ms=duration,
            )
            return TransferResponse(
                success=True,
                transfer_id=transfer_id,
                tool_name="browser.download",
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                status=TransferStatus.COMPLETED,
                progress_percentage=100,
                duration_ms=duration,
                **data,
            )
        except Exception as exc:
            await self._state.transition(transfer_id, TransferStatus.FAILED, error=str(exc))
            duration = (time.perf_counter() - started) * 1000
            await emit_download_failed(
                self._events, transfer_id=transfer_id, error=str(exc), duration_ms=duration
            )
            return TransferResponse(
                success=False,
                transfer_id=transfer_id,
                tool_name="browser.download",
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                status=TransferStatus.FAILED,
                duration_ms=duration,
                error=str(exc),
            )

    async def upload(
        self,
        page: Any,
        *,
        selector: str,
        files: list[str],
        session_id: str | None = None,
        browser_id: str | None = None,
        context_id: str | None = None,
        page_id: str | None = None,
        strategy: str = "input",
        frame_id: str | None = None,
    ) -> TransferResponse:
        transfer_id = await self._state.register(
            "browser.upload",
            metadata={
                "session_id": session_id,
                "browser_id": browser_id,
                "context_id": context_id,
                "page_id": page_id,
            },
        )
        started = time.perf_counter()
        await self._state.transition(transfer_id, TransferStatus.RUNNING)
        await emit_upload_started(
            self._events,
            transfer_id=transfer_id,
            session_id=session_id,
            browser_id=browser_id,
            context_id=context_id,
            page_id=page_id,
            strategy=strategy,
        )
        try:
            items = await self._uploads.upload(
                page, selector=selector, files=files, strategy=strategy, frame_id=frame_id
            )
            size = sum(int(item["file_size_bytes"]) for item in items)
            await self._state.update_progress(transfer_id, transferred_bytes=size, total_bytes=size)
            await self._state.transition(transfer_id, TransferStatus.COMPLETED)
            duration = (time.perf_counter() - started) * 1000
            first = items[0] if items else {}
            await emit_upload_completed(
                self._events,
                transfer_id=transfer_id,
                file_name=str(first.get("file_name", "")),
                file_size_bytes=size,
                mime_type=first.get("mime_type")
                if isinstance(first.get("mime_type"), str)
                else None,
                duration_ms=duration,
            )
            return TransferResponse(
                success=True,
                transfer_id=transfer_id,
                tool_name="browser.upload",
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                file_name=first.get("file_name")
                if isinstance(first.get("file_name"), str)
                else None,
                file_path=first.get("file_path")
                if isinstance(first.get("file_path"), str)
                else None,
                file_size_bytes=size,
                mime_type=first.get("mime_type")
                if isinstance(first.get("mime_type"), str)
                else None,
                status=TransferStatus.COMPLETED,
                progress_percentage=100,
                duration_ms=duration,
                metadata={"files": items},
            )
        except Exception as exc:
            await self._state.transition(transfer_id, TransferStatus.FAILED, error=str(exc))
            duration = (time.perf_counter() - started) * 1000
            await emit_upload_failed(
                self._events, transfer_id=transfer_id, error=str(exc), duration_ms=duration
            )
            return TransferResponse(
                success=False,
                transfer_id=transfer_id,
                tool_name="browser.upload",
                session_id=session_id,
                browser_id=browser_id,
                context_id=context_id,
                page_id=page_id,
                status=TransferStatus.FAILED,
                duration_ms=duration,
                error=str(exc),
            )

    async def status(self, transfer_id: str) -> TransferResponse:
        record = await self._state.get_record(transfer_id)
        current = await self._state.get(transfer_id)
        progress = current.to_progress()
        meta = record.metadata
        return TransferResponse(
            success=record.status is TransferStatus.COMPLETED,
            transfer_id=record.transfer_id,
            tool_name=record.tool_name,
            session_id=meta.get("session_id"),
            browser_id=meta.get("browser_id"),
            context_id=meta.get("context_id"),
            page_id=meta.get("page_id"),
            status=record.status,
            progress_percentage=progress.percentage,
            duration_ms=current.duration_ms(),
            error=record.error,
            metadata=meta,
        )

    async def cancel(self, transfer_id: str) -> TransferResponse:
        cancelled = await self._state.cancel(transfer_id)
        response = await self.status(transfer_id)
        return response.model_copy(
            update={"success": cancelled, "error": None if cancelled else response.error}
        )
