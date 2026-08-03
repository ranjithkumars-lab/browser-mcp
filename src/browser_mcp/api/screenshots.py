"""In-memory registry of screenshots captured through the chat API.

Each entry ties a captured screenshot file to the ``user_id`` that requested
it, so the web UI can render the image and attribute it to a chat user.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path


@dataclass
class ScreenshotRecord:
    """A single captured screenshot and its owning chat user."""

    filename: str
    path: str
    user_id: str | None = None
    session_id: str | None = None
    page_id: str | None = None
    url: str | None = None
    title: str | None = None
    mime_type: str = "image/png"
    width: int | None = None
    height: int | None = None
    captured_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def as_dict(self) -> dict[str, object]:
        return {
            "filename": self.filename,
            "path": self.path,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "page_id": self.page_id,
            "url": self.url,
            "title": self.title,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "captured_at": self.captured_at,
        }


class ScreenshotStore:
    """Thread-safe registry keyed by screenshot filename."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: dict[str, ScreenshotRecord] = {}
        self._lock = threading.Lock()
        self._max_records = max_records

    def record(self, record: ScreenshotRecord) -> None:
        with self._lock:
            if len(self._records) >= self._max_records and record.filename not in self._records:
                oldest = next(iter(self._records))
                self._records.pop(oldest, None)
            self._records[record.filename] = record

    def get(self, filename: str) -> ScreenshotRecord | None:
        with self._lock:
            return self._records.get(filename)

    def list(self, user_id: str | None = None) -> list[dict[str, object]]:
        with self._lock:
            records = self._records.values()
            if user_id is not None:
                records = [record for record in records if record.user_id == user_id]
            ordered = sorted(records, key=lambda record: record.captured_at, reverse=True)
            return [record.as_dict() for record in ordered]

    @staticmethod
    def filename_from_path(path: str) -> str:
        """Return the basename of a screenshot path (safe for URL lookups)."""
        return Path(path).name
