"""Domain models for the Download / Upload Engine.

All models are Pydantic :class:`~pydantic.BaseModel` instances so they
serialise cleanly to JSON for MCP tool responses and event payloads.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

__all__ = [
    "ChecksumAlgorithm",
    "ChecksumResult",
    "CleanupPolicy",
    "CollisionStrategy",
    "DownloadStrategy",
    "TransferItem",
    "TransferProgress",
    "TransferResponse",
    "TransferStatus",
    "UploadStrategy",
    "new_transfer_id",
]


def new_transfer_id() -> str:
    """Return a new unique transfer identifier."""
    return f"xfers_{uuid4().hex[:12]}"


class TransferStatus(StrEnum):
    """Lifecycle states for a transfer."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadStrategy(StrEnum):
    """Supported download strategy identifiers."""

    BROWSER = "browser"
    HTTP = "http"
    BLOB = "blob"


class UploadStrategy(StrEnum):
    """Supported upload strategy identifiers."""

    INPUT = "input"
    CHOOSER = "chooser"
    DRAG_DROP = "drag_drop"
    BUFFER = "buffer"


class CollisionStrategy(StrEnum):
    """How to handle a destination filename that already exists."""

    AUTO_RENAME = "auto_rename"
    OVERWRITE = "overwrite"
    REJECT = "reject"


class CleanupPolicy(StrEnum):
    """When temporary transfer files are removed."""

    ON_COMPLETION = "on_completion"
    ON_FAILURE = "on_failure"
    MANUAL = "manual"


class ChecksumAlgorithm(StrEnum):
    """Supported checksum algorithms for integrity verification."""

    SHA256 = "sha256"
    SHA1 = "sha1"
    MD5 = "md5"


class ChecksumResult(BaseModel):
    """Result of a checksum computation / verification."""

    algorithm: ChecksumAlgorithm = Field(
        default=ChecksumAlgorithm.SHA256,
        description="Hash algorithm used.",
    )
    hash: str = Field(description="Hex-encoded digest of the file content.")
    verified: bool = Field(
        default=False,
        description="Whether the computed hash matched the expected value.",
    )
    expected: str | None = Field(
        default=None,
        description="Expected hash value, if one was provided for verification.",
    )


class TransferProgress(BaseModel):
    """Progress snapshot for an in-flight transfer."""

    transferred_bytes: int = Field(
        default=0,
        ge=0,
        description="Number of bytes transferred so far.",
    )
    total_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Total bytes expected, or ``None`` when unknown.",
    )
    percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage (0–100).",
    )
    speed_bps: float = Field(
        default=0.0,
        ge=0.0,
        description="Current transfer speed in bytes per second.",
    )
    eta_seconds: float | None = Field(
        default=None,
        ge=0.0,
        description="Estimated seconds remaining, or ``None`` when unknown.",
    )


class TransferItem(BaseModel):
    """A single file involved in a transfer."""

    file_name: str = Field(description="Base name of the file.")
    file_path: str | None = Field(
        default=None,
        description="Absolute path where the file was saved (downloads) or read from (uploads).",
    )
    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
        description="Size of the file in bytes, or ``None`` when unknown.",
    )
    mime_type: str | None = Field(
        default=None,
        description="MIME type of the file, or ``None`` when unknown.",
    )
    checksum: ChecksumResult | None = Field(
        default=None,
        description="Checksum result if integrity verification was performed.",
    )


class TransferResponse(BaseModel):
    """Standardised JSON response returned by every transfer MCP tool."""

    success: bool = Field(description="Whether the operation succeeded.")
    transfer_id: str = Field(description="Unique identifier for this transfer.")
    tool_name: str = Field(description="Name of the MCP tool that initiated the transfer.")
    session_id: str | None = Field(default=None, description="Browser session id, if applicable.")
    browser_id: str | None = Field(default=None, description="Browser id, if applicable.")
    context_id: str | None = Field(default=None, description="Browser context id, if applicable.")
    page_id: str | None = Field(default=None, description="Browser page id, if applicable.")
    file_name: str | None = Field(default=None, description="Base name of the transferred file.")
    file_path: str | None = Field(default=None, description="Absolute path of the transferred file.")
    file_size_bytes: int | None = Field(default=None, ge=0, description="File size in bytes.")
    mime_type: str | None = Field(default=None, description="MIME type of the file.")
    checksum: ChecksumResult | None = Field(
        default=None,
        description="Checksum result if integrity verification was performed.",
    )
    status: TransferStatus = Field(description="Final lifecycle status of the transfer.")
    progress_percentage: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage at the time of the response.",
    )
    duration_ms: float | None = Field(
        default=None,
        ge=0.0,
        description="Total elapsed time in milliseconds.",
    )
    error: str | None = Field(default=None, description="Error message when ``success`` is False.")
    metadata: dict[str, Any] = Field(
        default_factory=dict[str, Any],
        description="Arbitrary strategy-specific metadata.",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when the transfer was initiated.",
    )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable dict (dates as ISO strings)."""
        return self.model_dump(mode="json")
