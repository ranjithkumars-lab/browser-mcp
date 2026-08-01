"""Tests for the NavigationToolkit and its MCP tool bindings."""

from __future__ import annotations

import pytest
from tests.fakes import FakePage
from tests.helpers import build_runtime, default_settings

from browser_mcp.tools.navigation import (
    TOOL_NAMESPACE,
    NavigationToolkit,
    build_navigation_tools,
)
from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit

EXPECTED_TOOLS = frozenset(
    {
        "goto",
        "back",
        "forward",
        "reload",
        "wait_timeout",
        "wait_navigation",
        "wait_popup",
        "wait_download",
        "wait_url",
        "scroll_to",
        "scroll_by",
        "scroll_element",
        "click",
        "hover",
        "double_click",
        "right_click",
        "list_frames",
        "list_windows",
        "close_popup",
        "activate_window",
    }
)


def _build_toolkit() -> NavigationToolkit:
    return NavigationToolkit(
        navigation=None,  # type: ignore[arg-type]
        history=None,  # type: ignore[arg-type]
        frames=None,  # type: ignore[arg-type]
        windows=None,  # type: ignore[arg-type]
        interactions=None,  # type: ignore[arg-type]
        waiting=None,  # type: ignore[arg-type]
    )


async def test_registers_all_twenty_tools() -> None:
    registry = ToolRegistry()
    _build_toolkit().register(registry)
    names = {m.name for m in registry.list()}
    assert names == {f"{TOOL_NAMESPACE}.{name}" for name in EXPECTED_TOOLS}


async def test_build_navigation_tools_returns_tool_calls() -> None:
    tools = build_navigation_tools(None, None, None, None, None, None)  # type: ignore[arg-type]
    assert {t.__name__ for t in tools} == EXPECTED_TOOLS


async def test_every_tool_has_metadata() -> None:
    toolkit = _build_toolkit()
    for name in EXPECTED_TOOLS:
        metadata = get_tool_metadata(getattr(toolkit, name))
        assert metadata is not None, name
        assert metadata.name == f"{TOOL_NAMESPACE}.{name}"
        assert metadata.returns == "json"


async def test_goto_tool_success() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.goto(
        runtime["session_id"], runtime["page_handle"].page_id, "https://example.com"
    )
    assert result["success"] is True
    assert result["url"] == "https://example.com"
    assert "timestamp" in result


async def test_goto_tool_error_is_structured() -> None:
    runtime = await build_runtime(
        settings=default_settings(navigation={"blocked_domains": ["example.com"]})
    )
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.goto(
        runtime["session_id"], runtime["page_handle"].page_id, "https://example.com"
    )
    assert result["success"] is False
    assert "blocked" in result["error"]
    assert result["session_id"] == "s1"


async def test_registry_call_through_toolkit() -> None:
    runtime = await build_runtime()
    registry = ToolRegistry()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    toolkit.register(registry)
    result = await registry.call(
        "browser.goto",
        session_id=runtime["session_id"],
        page_id=runtime["page_handle"].page_id,
        url="https://example.com",
    )
    assert result["success"] is True


async def test_click_tool_success() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.click(runtime["session_id"], runtime["page_handle"].page_id, "#click-me")
    assert result["success"] is True
    assert result["action"] == "click"


async def test_list_frames_tool() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.list_frames(runtime["session_id"], runtime["page_handle"].page_id)
    assert result["success"] is True
    assert result["frames"]
    assert result["frames"][0]["is_main"] is True


async def test_wait_timeout_tool() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.wait_timeout(runtime["session_id"], runtime["page_handle"].page_id, 5)
    assert result["success"] is True
    assert result["waited_ms"] == 5


async def test_wait_popup_tool() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    context = runtime["page"].context
    context.emit_page(FakePage(url="https://popup.example/"))
    result = await toolkit.wait_popup(runtime["session_id"], runtime["page_handle"].page_id)
    assert result["success"] is True
    assert result["popup_id"]


async def test_list_windows_tool() -> None:
    runtime = await build_runtime()
    toolkit = NavigationToolkit(
        runtime["navigation"],
        runtime["history"],
        runtime["frames"],
        runtime["windows"],
        runtime["interactions"],
        runtime["waiting"],
    )
    result = await toolkit.list_windows(runtime["session_id"], runtime["page_handle"].page_id)
    assert result["success"] is True
    assert len(result["windows"]) == 1
    assert result["windows"][0]["is_popup"] is False
