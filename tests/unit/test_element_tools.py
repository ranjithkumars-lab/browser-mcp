"""Tests for the ElementToolkit and its MCP tool bindings."""

from __future__ import annotations

import pytest
from tests.fakes import FakeElement
from tests.helpers import build_runtime

from browser_mcp.tools.elements import TOOL_NAMESPACE, ElementToolkit, build_element_tools
from enterprise_mcp.tools.decorators import get_tool_metadata
from enterprise_mcp.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit

EXPECTED_TOOLS = frozenset({"find", "find_all", "state", "text", "html", "attribute"})


def _toolkit(runtime: dict) -> ElementToolkit:
    return ElementToolkit(runtime["engine"])


async def test_registers_all_six_tools() -> None:
    registry = ToolRegistry()
    _toolkit(await build_runtime()).register(registry)
    names = {m.name for m in registry.list()}
    dotted = {f"{TOOL_NAMESPACE}.{name}" for name in EXPECTED_TOOLS}
    underscored = {f"{TOOL_NAMESPACE}_{name}" for name in EXPECTED_TOOLS}
    assert names == dotted | underscored


async def test_build_element_tools_returns_tool_calls() -> None:
    tools = build_element_tools((await build_runtime())["engine"])
    assert {t.__name__ for t in tools} == EXPECTED_TOOLS


async def test_every_tool_has_metadata() -> None:
    toolkit = _toolkit(await build_runtime())
    for name in EXPECTED_TOOLS:
        metadata = get_tool_metadata(getattr(toolkit, name))
        assert metadata is not None, name
        assert metadata.name == f"{TOOL_NAMESPACE}.{name}"
        assert metadata.returns == "json"


async def test_find_tool_success() -> None:
    runtime = await build_runtime()
    result = await _toolkit(runtime).find(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "#heading"
    )
    assert result["success"] is True
    assert result["element_id"].startswith("element_")
    assert "timestamp" in result


async def test_find_tool_error_is_structured() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#nope", [])
    result = await _toolkit(runtime).find(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "#nope"
    )
    assert result["success"] is False
    assert "not found" in result["error"]


async def test_find_tool_invalid_strategy_error() -> None:
    runtime = await build_runtime()
    result = await _toolkit(runtime).find(
        runtime["session_id"], runtime["page_handle"].page_id, "bogus", "#a"
    )
    assert result["success"] is False
    assert "strategy" in result["error"]


async def test_find_tool_accepts_empty_frame_id() -> None:
    runtime = await build_runtime()
    result = await _toolkit(runtime).find(
        runtime["session_id"],
        runtime["page_handle"].page_id,
        "css",
        "#heading",
        frame_id="",
    )
    assert result["success"] is True
    assert result["frame_id"] is None


async def test_registry_resolves_underscore_alias() -> None:
    runtime = await build_runtime()
    registry = ToolRegistry()
    _toolkit(runtime).register(registry)
    result = await registry.call(
        "browser.element_find",
        session_id=runtime["session_id"],
        page_id=runtime["page_handle"].page_id,
        strategy="css",
        value="#heading",
    )
    assert result["success"] is True


async def test_find_all_tool_success() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("li", [FakeElement(text="a"), FakeElement(text="b")])
    result = await _toolkit(runtime).find_all(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "li"
    )
    assert result["success"] is True
    assert result["count"] == 2
    assert len(result["elements"]) == 2


async def test_text_tool_success() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#msg", [FakeElement(text="hello")])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#msg"
        )
    )["element_id"]
    result = await _toolkit(runtime).text(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    assert result["success"] is True
    assert result["text"] == "hello"


async def test_html_tool_outer_flag() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#p", [FakeElement(text="x", tag="p")])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#p"
        )
    )["element_id"]
    result = await _toolkit(runtime).html(
        runtime["session_id"], runtime["page_handle"].page_id, element_id, outer=True
    )
    assert result["success"] is True
    assert result["html"] == "<p>x</p>"


async def test_attribute_tool_success() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#a", [FakeElement(attrs={"data-x": "42"})])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    result = await _toolkit(runtime).attribute(
        runtime["session_id"], runtime["page_handle"].page_id, element_id, "data-x"
    )
    assert result["success"] is True
    assert result["value"] == "42"


async def test_state_tool_success() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#input", [FakeElement(editable=True, enabled=True)])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#input"
        )
    )["element_id"]
    result = await _toolkit(runtime).state(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    assert result["success"] is True
    assert result["exists"] is True
    assert result["editable"] is True


async def test_registry_call_through_toolkit() -> None:
    runtime = await build_runtime()
    registry = ToolRegistry()
    _toolkit(runtime).register(registry)
    result = await registry.call(
        "browser.element.find",
        session_id=runtime["session_id"],
        page_id=runtime["page_handle"].page_id,
        strategy="css",
        value="#heading",
    )
    assert result["success"] is True
