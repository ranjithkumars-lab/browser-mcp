"""Download / Upload Engine package.

Provides high-reliability, async file transfer management for the Browser MCP
platform.  The engine is a *Browser Core service* injected into
:class:`~browser_mcp.plugins.context.PluginContext` so that every plugin
(Forms, Scraper, future plugins) can leverage unified download and upload
capabilities.

Public surface
--------------
- :class:`~browser_mcp.transfer.manager.TransferManager` – top-level facade.
- :class:`~browser_mcp.transfer.models.TransferResponse` – standardised result.
- :class:`~browser_mcp.transfer.errors.TransferError` – error hierarchy.
"""

from __future__ import annotations

from browser_mcp.transfer.errors import (
    DownloadCanceledError,
    DownloadError,
    DownloadTimeoutError,
    DragDropFailedError,
    FileSizeExceededError,
    IntegrityVerificationError,
    InvalidMimeTypeError,
    TransferError,
    UploadError,
)
from browser_mcp.transfer.events import (
    emit_download_completed,
    emit_download_failed,
    emit_download_progress,
    emit_download_started,
    emit_upload_completed,
    emit_upload_failed,
    emit_upload_progress,
    emit_upload_started,
    TransferEvent,
)
from browser_mcp.transfer.models import (
    ChecksumAlgorithm,
    ChecksumResult,
    CollisionStrategy,
    CleanupPolicy,
    DownloadStrategy,
    TransferItem,
    TransferProgress,
    TransferResponse,
    TransferStatus,
    UploadStrategy,
)
from browser_mcp.transfer.provider import PlaywrightTransferProvider, TransferProvider
from browser_mcp.transfer.state import TransferRecord, TransferStateManager, TransferState
from browser_mcp.transfer.manager import TransferManager

__all__ = [
    # errors
    "DownloadCanceledError",
    "DownloadError",
    "DownloadTimeoutError",
    "DragDropFailedError",
    "FileSizeExceededError",
    "IntegrityVerificationError",
    "InvalidMimeTypeError",
    "TransferError",
    "UploadError",
    # events
    "TransferEvent",
    "emit_download_completed",
    "emit_download_failed",
    "emit_download_progress",
    "emit_download_started",
    "emit_upload_completed",
    "emit_upload_failed",
    "emit_upload_progress",
    "emit_upload_started",
    # models
    "ChecksumAlgorithm",
    "ChecksumResult",
    "CollisionStrategy",
    "CleanupPolicy",
    "DownloadStrategy",
    "TransferItem",
    "TransferProgress",
    "TransferResponse",
    "TransferStatus",
    "UploadStrategy",
    # provider
    "PlaywrightTransferProvider",
    "TransferProvider",
    # state
    "TransferRecord",
    "TransferStateManager",
    "TransferState",
    # manager
    "TransferManager",
]
