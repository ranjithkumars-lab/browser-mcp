"""Local upload file validation."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from browser_mcp.transfer.errors import (
    FileNotFoundError,
    FileSizeExceededError,
    InvalidMimeTypeError,
)


class FileValidator:
    def __init__(
        self,
        *,
        max_file_size_bytes: int,
        allowed_extensions: list[str] | None = None,
        allowed_mime_types: list[str] | None = None,
    ) -> None:
        self.max_file_size_bytes = max_file_size_bytes
        self.allowed_extensions = {item.lower().lstrip(".") for item in allowed_extensions or []}
        self.allowed_mime_types = set(allowed_mime_types or [])

    def validate(self, files: list[str]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for value in files:
            path = Path(value).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"upload file '{path}' does not exist")
            size = path.stat().st_size
            if size > self.max_file_size_bytes:
                raise FileSizeExceededError(
                    f"upload file '{path.name}' exceeds {self.max_file_size_bytes} bytes"
                )
            extension = path.suffix.lower().lstrip(".")
            if self.allowed_extensions and extension not in self.allowed_extensions:
                raise InvalidMimeTypeError(f"file extension '.{extension}' is not allowed")
            mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
            if self.allowed_mime_types and mime not in self.allowed_mime_types:
                raise InvalidMimeTypeError(f"MIME type '{mime}' is not allowed")
            result.append(
                {
                    "file_name": path.name,
                    "file_path": str(path.resolve()),
                    "file_size_bytes": size,
                    "mime_type": mime,
                }
            )
        return result
