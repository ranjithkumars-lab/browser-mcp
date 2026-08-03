"""Screenshot capture for live browser pages.

:class:`ScreenshotManager` resolves a page through the :class:`StateManager`
and captures a PNG or JPEG image of either the full viewport, the full
scrollable page, or an element matched by a CSS selector. The image is written
to the configured screenshot directory and metadata (path, size, dimensions,
format) is returned to the caller.
"""

from __future__ import annotations

import struct
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal, cast
from uuid import uuid4

import structlog

from browser_mcp.browser.navigation.state import StateManager
from browser_mcp.config.models import BrowserSettings
from browser_mcp.errors import ScreenshotError

__all__ = ["ScreenshotManager"]

ScreenshotFormat = Literal["png", "jpeg"]
_MIME_TYPES: dict[str, str] = {"png": "image/png", "jpeg": "image/jpeg"}


class ScreenshotManager:
    """Captures screenshots of pages registered in the browser hierarchy."""

    def __init__(self, state: StateManager, settings: BrowserSettings) -> None:
        self._state = state
        self._settings = settings
        self._logger = structlog.get_logger("browser_mcp.screenshot")

    # -- public API -----------------------------------------------------

    async def capture(
        self,
        session_id: str,
        page_id: str,
        *,
        selector: str | None = None,
        output_format: str = "png",
        full_page: bool | None = None,
        quality: int | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        """Capture a screenshot of ``page_id`` in ``session_id``.

        Parameters
        ----------
        session_id:
            Owning session identifier.
        page_id:
            Page to capture.
        selector:
            Optional CSS selector; when given only the matched element is
            captured instead of the page viewport.
        output_format:
            ``png`` or ``jpeg``.
        full_page:
            When true, capture the entire scrollable page (page-level captures
            only). Falls back to the configured default when ``None``.
        quality:
            Optional JPEG quality (1-100); ignored for PNG.
        directory:
            Override for the configured screenshot directory.
        """
        resolved_format = self._resolve_format(output_format)
        if resolved_format == "jpeg" and quality is None:
            quality = self._settings.screenshot.default_quality
        if quality is not None and (quality < 1 or quality > 100):
            raise ScreenshotError("quality must be between 1 and 100")
        if selector is not None and not selector.strip():
            raise ScreenshotError("selector must not be empty")

        handle = self._state.page_in_session(session_id, page_id)
        page = handle.page
        started = time.perf_counter()

        directory = directory or self._settings.screenshot.directory
        filepath = self._build_path(directory, resolved_format, page_id)

        try:
            if selector is not None:
                data = await page.locator(selector).screenshot(
                    type=resolved_format,
                    quality=quality if resolved_format == "jpeg" else None,
                )
            else:
                resolve_full_page = (
                    self._settings.screenshot.default_full_page if full_page is None else full_page
                )
                data = await page.screenshot(
                    type=resolved_format,
                    quality=quality if resolved_format == "jpeg" else None,
                    full_page=resolve_full_page,
                )
        except Exception as exc:
            raise ScreenshotError(f"screenshot failed: {exc}") from exc

        if not data:
            raise ScreenshotError("screenshot produced no image data")

        filepath.write_bytes(data)
        width, height = _image_dimensions(data, resolved_format)
        duration_ms = (time.perf_counter() - started) * 1000.0

        self._logger.info(
            "screenshot_captured",
            session_id=session_id,
            page_id=page_id,
            format=resolved_format,
            path=str(filepath),
            size_bytes=len(data),
            duration_ms=duration_ms,
        )

        return {
            "session_id": session_id,
            "page_id": page_id,
            "url": page.url,
            "title": await page.title(),
            "format": resolved_format,
            "mime_type": _MIME_TYPES[resolved_format],
            "full_page": (
                self._settings.screenshot.default_full_page if full_page is None else full_page
            ),
            "selector": selector,
            "screenshot_path": str(filepath),
            "file_size_bytes": len(data),
            "width": width,
            "height": height,
            "duration_ms": duration_ms,
        }

    # -- helpers --------------------------------------------------------

    def _resolve_format(self, output_format: str) -> ScreenshotFormat:
        resolved = (output_format or self._settings.screenshot.default_format).lower()
        if resolved not in _MIME_TYPES:
            raise ScreenshotError(
                f"unsupported screenshot format '{output_format}' (use 'png' or 'jpeg')"
            )
        return cast(ScreenshotFormat, resolved)

    def _build_path(self, directory: str, output_format: str, page_id: str) -> Path:
        path = Path(directory).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        filename = f"{page_id}_{timestamp}_{uuid4().hex[:8]}.{output_format}"
        return path / filename


def _image_dimensions(data: bytes, output_format: str) -> tuple[int | None, int | None]:
    """Return ``(width, height)`` parsed from the image header, or ``(None, None)``."""
    if output_format == "png":
        return _png_dimensions(data)
    if output_format == "jpeg":
        return _jpeg_dimensions(data)
    return None, None


def _png_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Parse PNG IHDR for width/height; first 8 bytes are the signature."""
    if len(data) < 24 or not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None, None
    try:
        return struct.unpack(">II", data[16:24])
    except (struct.error, ValueError):
        return None, None


def _jpeg_dimensions(data: bytes) -> tuple[int | None, int | None]:
    """Parse the JPEG SOF marker for width/height."""
    if len(data) < 4 or not data.startswith(b"\xff\xd8"):
        return None, None
    position = 2
    length = len(data)
    while position < length:
        if data[position] != 0xFF:
            position += 1
            continue
        while position < length and data[position] == 0xFF:
            position += 1
        if position >= length:
            return None, None
        marker = data[position]
        position += 1
        if marker in (0xD8, 0x01):
            continue
        if 0xD0 <= marker <= 0xD9:
            continue
        if position + 1 >= length:
            return None, None
        block_length = struct.unpack(">H", data[position : position + 2])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            if position + 5 < length:
                height, width = struct.unpack(">HH", data[position + 3 : position + 7])
                return width, height
            return None, None
        position += block_length
    return None, None
