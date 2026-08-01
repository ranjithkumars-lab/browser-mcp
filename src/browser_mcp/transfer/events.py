"""Domain event helpers for the Download / Upload Engine.

Events are thin :class:`~enterprise_mcp.events.types.DomainEvent` subclasses
with the ``event_name`` fixed at the class level.  The ``payload`` carries
structured data for downstream consumers (logging, observability, plugins).
"""

from __future__ import annotations

from typing import Any

from enterprise_mcp.events.bus import EventBus
from enterprise_mcp.events.types import DomainEvent

__all__ = [
    "TransferEvent",
    "emit_download_completed",
    "emit_download_failed",
    "emit_download_progress",
    "emit_download_started",
    "emit_upload_completed",
    "emit_upload_failed",
    "emit_upload_progress",
    "emit_upload_started",
]


class TransferEvent(DomainEvent):
    """Base :class:`DomainEvent` for transfer engine events."""


async def emit_download_started(
    events: EventBus,
    *,
    transfer_id: str,
    session_id: str | None = None,
    browser_id: str | None = None,
    context_id: str | None = None,
    page_id: str | None = None,
    file_name: str | None = None,
    strategy: str | None = None,
) -> None:
    """Publish ``transfer.download.started``."""
    await events.publish(
        TransferEvent(
            "transfer.download.started",
            {
                "transfer_id": transfer_id,
                "session_id": session_id,
                "browser_id": browser_id,
                "context_id": context_id,
                "page_id": page_id,
                "file_name": file_name,
                "strategy": strategy,
            },
        )
    )


async def emit_download_progress(
    events: EventBus,
    *,
    transfer_id: str,
    transferred_bytes: int,
    total_bytes: int | None,
    percentage: float,
    speed_bps: float,
    eta_seconds: float | None,
) -> None:
    """Publish ``transfer.download.progress``."""
    await events.publish(
        TransferEvent(
            "transfer.download.progress",
            {
                "transfer_id": transfer_id,
                "transferred_bytes": transferred_bytes,
                "total_bytes": total_bytes,
                "percentage": round(percentage, 2),
                "speed_bps": round(speed_bps, 2),
                "eta_seconds": round(eta_seconds, 2) if eta_seconds is not None else None,
            },
        )
    )


async def emit_download_completed(
    events: EventBus,
    *,
    transfer_id: str,
    file_name: str,
    file_path: str,
    file_size_bytes: int,
    mime_type: str | None = None,
    checksum: dict[str, Any] | None = None,
    duration_ms: float,
) -> None:
    """Publish ``transfer.download.completed``."""
    await events.publish(
        TransferEvent(
            "transfer.download.completed",
            {
                "transfer_id": transfer_id,
                "file_name": file_name,
                "file_path": file_path,
                "file_size_bytes": file_size_bytes,
                "mime_type": mime_type,
                "checksum": checksum,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_download_failed(
    events: EventBus,
    *,
    transfer_id: str,
    error: str,
    duration_ms: float,
) -> None:
    """Publish ``transfer.download.failed``."""
    await events.publish(
        TransferEvent(
            "transfer.download.failed",
            {
                "transfer_id": transfer_id,
                "error": error,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_upload_started(
    events: EventBus,
    *,
    transfer_id: str,
    session_id: str | None = None,
    browser_id: str | None = None,
    context_id: str | None = None,
    page_id: str | None = None,
    file_name: str | None = None,
    strategy: str | None = None,
) -> None:
    """Publish ``transfer.upload.started``."""
    await events.publish(
        TransferEvent(
            "transfer.upload.started",
            {
                "transfer_id": transfer_id,
                "session_id": session_id,
                "browser_id": browser_id,
                "context_id": context_id,
                "page_id": page_id,
                "file_name": file_name,
                "strategy": strategy,
            },
        )
    )


async def emit_upload_progress(
    events: EventBus,
    *,
    transfer_id: str,
    transferred_bytes: int,
    total_bytes: int | None,
    percentage: float,
    speed_bps: float,
    eta_seconds: float | None,
) -> None:
    """Publish ``transfer.upload.progress``."""
    await events.publish(
        TransferEvent(
            "transfer.upload.progress",
            {
                "transfer_id": transfer_id,
                "transferred_bytes": transferred_bytes,
                "total_bytes": total_bytes,
                "percentage": round(percentage, 2),
                "speed_bps": round(speed_bps, 2),
                "eta_seconds": round(eta_seconds, 2) if eta_seconds is not None else None,
            },
        )
    )


async def emit_upload_completed(
    events: EventBus,
    *,
    transfer_id: str,
    file_name: str,
    file_size_bytes: int,
    mime_type: str | None = None,
    duration_ms: float,
) -> None:
    """Publish ``transfer.upload.completed``."""
    await events.publish(
        TransferEvent(
            "transfer.upload.completed",
            {
                "transfer_id": transfer_id,
                "file_name": file_name,
                "file_size_bytes": file_size_bytes,
                "mime_type": mime_type,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )


async def emit_upload_failed(
    events: EventBus,
    *,
    transfer_id: str,
    error: str,
    duration_ms: float,
) -> None:
    """Publish ``transfer.upload.failed``."""
    await events.publish(
        TransferEvent(
            "transfer.upload.failed",
            {
                "transfer_id": transfer_id,
                "error": error,
                "duration_ms": round(duration_ms, 3),
            },
        )
    )
