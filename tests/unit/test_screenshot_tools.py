"""Unit tests for the ScreenshotToolkit and ScreenshotManager."""

from __future__ import annotations

from pathlib import Path

import pytest
from tests.fakes import FakePage
from tests.helpers import build_runtime, default_settings

from browser_mcp.browser.screenshot import (
    ScreenshotManager,
    _image_dimensions,
    _jpeg_dimensions,
    _png_dimensions,
)
from browser_mcp.tools.screenshot import (
    TOOL_NAMESPACE,
    ScreenshotToolkit,
    build_screenshot_tools,
)
from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit

PNG_1X1 = bytes.fromhex(
    "89504e470d0a1a0a"
    "0000000d49484452000000010000000108060000001f15c489"
    "0000000a49444154789c63000100000500010d0a2db40000000049454e44ae426082"
)

JPEG_100X200 = bytes.fromhex(
    "ffd8ffe000104a4649460001010100000100010000ffc0000b0800c8006401011100ffd9"
)


async def _build_manager(
    tmp_path: Path, **settings_overrides: object
) -> tuple[ScreenshotManager, dict[str, object]]:
    settings = default_settings(
        screenshot={"directory": str(tmp_path), "default_format": "png"},
        **settings_overrides,
    )
    runtime = await build_runtime(settings=settings, page=FakePage(url="https://example.com"))
    manager = ScreenshotManager(runtime["state"], settings)
    return manager, runtime


class TestScreenshotToolkit:
    def test_tool_namespace(self) -> None:
        assert TOOL_NAMESPACE == "browser"

    def test_screenshot_tool_has_metadata(self) -> None:
        toolkit = ScreenshotToolkit(None)  # type: ignore[arg-type]
        metadata = get_tool_metadata(toolkit.screenshot)
        assert metadata is not None
        assert metadata.name == "browser.screenshot"
        assert metadata.returns == "json"

    def test_register_calls_registry(self) -> None:
        toolkit = ScreenshotToolkit(None)  # type: ignore[arg-type]
        registry = ToolRegistry()
        toolkit.register(registry)
        names = {m.name for m in registry.list()}
        assert names == {"browser.screenshot"}

    def test_build_returns_single_tool(self) -> None:
        tools = build_screenshot_tools(None)  # type: ignore[arg-type]
        assert [t.__name__ for t in tools] == ["screenshot"]

    @pytest.mark.asyncio
    async def test_registry_call_through_toolkit(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_bytes = PNG_1X1
        registry = ToolRegistry()
        ScreenshotToolkit(manager).register(registry)
        result = await registry.call(
            "browser.screenshot",
            session_id=runtime["session_id"],
            page_id=runtime["page_handle"].page_id,
        )
        assert result["success"] is True
        assert result["format"] == "png"
        assert Path(result["screenshot_path"]).exists()


class TestScreenshotManager:
    @pytest.mark.asyncio
    async def test_capture_page_png(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_bytes = PNG_1X1
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"], runtime["page_handle"].page_id
        )
        assert result["success"] is True
        assert result["format"] == "png"
        assert result["mime_type"] == "image/png"
        assert result["width"] == 1
        assert result["height"] == 1
        assert result["file_size_bytes"] == len(PNG_1X1)
        assert result["url"] == "https://example.com"
        assert Path(result["screenshot_path"]).exists()

    @pytest.mark.asyncio
    async def test_capture_full_page_flag(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_bytes = PNG_1X1
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"], runtime["page_handle"].page_id, full_page=True
        )
        assert result["full_page"] is True
        assert runtime["page"].last_screenshot is not None
        assert runtime["page"].last_screenshot["full_page"] is True

    @pytest.mark.asyncio
    async def test_capture_selector(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        locator = runtime["page"].locator("#hero")
        locator.screenshot_bytes = PNG_1X1
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"], runtime["page_handle"].page_id, selector="#hero"
        )
        assert result["success"] is True
        assert result["selector"] == "#hero"
        assert locator.last_screenshot is not None
        assert locator.last_screenshot["type"] == "png"

    @pytest.mark.asyncio
    async def test_capture_jpeg_with_quality(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_bytes = JPEG_100X200
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"],
            runtime["page_handle"].page_id,
            output_format="jpeg",
            quality=80,
        )
        assert result["success"] is True
        assert result["mime_type"] == "image/jpeg"
        assert result["width"] == 100
        assert result["height"] == 200
        assert runtime["page"].last_screenshot["quality"] == 80

    @pytest.mark.asyncio
    async def test_capture_error_is_structured(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_error = RuntimeError("boom")
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"], runtime["page_handle"].page_id
        )
        assert result["success"] is False
        assert "boom" in result["error"]

    @pytest.mark.asyncio
    async def test_capture_unsupported_format(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"],
            runtime["page_handle"].page_id,
            output_format="webp",
        )
        assert result["success"] is False
        assert "unsupported" in result["error"]

    @pytest.mark.asyncio
    async def test_capture_unknown_page(self, tmp_path: Path) -> None:
        manager, _ = await _build_manager(tmp_path)
        result = await ScreenshotToolkit(manager).screenshot("s1", "page_missing")
        assert result["success"] is False
        assert "does not belong" in result["error"] or "not found" in result["error"]

    @pytest.mark.asyncio
    async def test_capture_directory_override(self, tmp_path: Path) -> None:
        manager, runtime = await _build_manager(tmp_path)
        runtime["page"].screenshot_bytes = PNG_1X1
        custom = tmp_path / "custom"
        result = await ScreenshotToolkit(manager).screenshot(
            runtime["session_id"],
            runtime["page_handle"].page_id,
            directory=str(custom),
        )
        assert Path(result["screenshot_path"]).parent == custom


class TestImageDimensions:
    def test_png_dimensions(self) -> None:
        assert _png_dimensions(PNG_1X1) == (1, 1)

    def test_png_invalid_header(self) -> None:
        assert _png_dimensions(b"not a png") == (None, None)

    def test_png_too_short(self) -> None:
        assert _png_dimensions(b"\x89PNG\r\n\x1a\n\x00") == (None, None)

    def test_jpeg_dimensions(self) -> None:
        assert _jpeg_dimensions(JPEG_100X200) == (100, 200)

    def test_jpeg_invalid_header(self) -> None:
        assert _jpeg_dimensions(b"garbage") == (None, None)

    def test_image_dimensions_unknown_format(self) -> None:
        assert _image_dimensions(b"", "webp") == (None, None)
