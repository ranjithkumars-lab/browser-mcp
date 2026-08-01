"""Transfer error hierarchy.

All transfer-specific failures derive from :class:`TransferError`, which itself
inherits from :class:`~browser_mcp.errors.BrowserError`.  The download and
upload sub-hierarchies preserve backward compatibility with the pre-existing
``DownloadError`` defined in :mod:`browser_mcp.errors`.
"""

from __future__ import annotations

from browser_mcp.errors import BrowserError, DownloadError as _BrowserDownloadError

__all__ = [
    "DownloadCanceledError",
    "DownloadError",
    "DownloadTimeoutError",
    "DragDropFailedError",
    "FileSizeExceededError",
    "IntegrityVerificationError",
    "InvalidMimeTypeError",
    "TransferError",
    "UploadError",
]


class TransferError(BrowserError):
    """Base class for all download / upload engine failures."""


class DownloadError(TransferError, _BrowserDownloadError):
    """Raised when a browser download cannot be awaited, captured, or resolved.

    Inherits from both :class:`TransferError` (the transfer hierarchy root)
    and the pre-existing :class:`browser_mcp.errors.DownloadError` so that
    existing ``except DownloadError`` handlers continue to work.
    """


class DownloadTimeoutError(DownloadError):
    """Raised when a download does not complete within the configured timeout."""


class DownloadCanceledError(DownloadError):
    """Raised when a download is cancelled by the caller or the browser."""


class IntegrityVerificationError(DownloadError):
    """Raised when a downloaded file's checksum does not match the expected value."""


class UploadError(TransferError):
    """Base class for all upload engine failures."""


class FileNotFoundError(UploadError):
    """Raised when a source file for upload does not exist on disk."""


class FileSizeExceededError(UploadError):
    """Raised when a file exceeds the configured maximum transfer size."""


class InvalidMimeTypeError(UploadError):
    """Raised when a file's MIME type is not in the allowed whitelist."""


class DragDropFailedError(UploadError):
    """Raised when a synthetic drag-and-drop upload event cannot be dispatched."""
