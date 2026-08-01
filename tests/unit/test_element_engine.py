"""Tests for the ElementEngine facade and element_id caching."""

from __future__ import annotations

import pytest
from tests.fakes import FakeElement, FakePage
from tests.helpers import build_runtime

from browser_mcp.errors import (
    ElementNotFoundError,
    ElementStateError,
    StaleElementReferenceError,
)

pytestmark = pytest.mark.unit


async def test_find_returns_structured_record() -> None:
    runtime = await build_runtime()
    result = await runtime["engine"].find(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "#heading"
    )
    assert "success" not in result  # plain engine record, not an MCP envelope
    assert result["element_id"].startswith("element_")
    assert result["session_id"] == "s1"
    assert result["browser_id"] == "b1"
    assert result["context_id"] == runtime["context_id"]
    assert result["page_id"] == runtime["page_handle"].page_id
    assert result["strategy"] == "css"
    assert result["value"] == "#heading"
    assert result["count"] == 1
    assert result["duration_ms"] >= 0


async def test_find_emits_resolved_and_found_events() -> None:
    runtime = await build_runtime()
    seen: list[str] = []
    runtime["events"].subscribe("element.resolved", _collect("element.resolved", seen))
    runtime["events"].subscribe("element.found", _collect("element.found", seen))

    await runtime["engine"].find(runtime["session_id"], runtime["page_handle"].page_id, "css", "#a")
    assert seen == ["element.resolved", "element.found"]


async def test_find_not_found_raises_and_emits() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#missing", [])
    seen: list[str] = []
    runtime["events"].subscribe("element.not_found", _collect("element.not_found", seen))

    with pytest.raises(ElementNotFoundError):
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#missing"
        )
    assert seen == ["element.not_found"]


async def test_find_strict_multiple_matches_raises() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#dup", [FakeElement(), FakeElement()])
    with pytest.raises(ElementStateError):
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#dup"
        )


async def test_find_all_returns_indexed_element_ids() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements(
        "li",
        [FakeElement(text="a"), FakeElement(text="b"), FakeElement(text="c")],
    )
    result = await runtime["engine"].find_all(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "li"
    )
    assert result["count"] == 3
    assert [entry["index"] for entry in result["elements"]] == [0, 1, 2]
    assert all(entry["element_id"].startswith("element_") for entry in result["elements"])


async def test_find_all_nth_element_text() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements(
        "li",
        [FakeElement(text="first"), FakeElement(text="second"), FakeElement(text="third")],
    )
    result = await runtime["engine"].find_all(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "li"
    )
    element_id = result["elements"][1]["element_id"]
    text = await runtime["engine"].text(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    assert text["text"] == "second"


async def test_text_returns_rendered_text() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#msg", [FakeElement(text="hello world")])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#msg"
        )
    )["element_id"]
    result = await runtime["engine"].text(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    assert result["text"] == "hello world"


async def test_html_inner_and_outer() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements(
        "#block", [FakeElement(text="x", tag="p", attrs={"data-html": "<b>hi</b>"})]
    )
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#block"
        )
    )["element_id"]

    inner = await runtime["engine"].html(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    outer = await runtime["engine"].html(
        runtime["session_id"], runtime["page_handle"].page_id, element_id, outer=True
    )
    assert inner["html"] == "<b>hi</b>"
    assert outer["html"] == "<p>x</p>"


async def test_attribute_returns_value_and_none() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements("#link", [FakeElement(attrs={"href": "https://example.com"})])
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#link"
        )
    )["element_id"]

    present = await runtime["engine"].attribute(
        runtime["session_id"], runtime["page_handle"].page_id, element_id, "href"
    )
    missing = await runtime["engine"].attribute(
        runtime["session_id"], runtime["page_handle"].page_id, element_id, "title"
    )
    assert present["value"] == "https://example.com"
    assert missing["value"] is None


async def test_state_returns_snapshot_and_emits_event() -> None:
    runtime = await build_runtime()
    runtime["page"].set_elements(
        "#input",
        [FakeElement(attrs={"type": "text"}, editable=True, enabled=True, visible=True)],
    )
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#input"
        )
    )["element_id"]
    seen: list[str] = []
    runtime["events"].subscribe("element.state_changed", _collect("element.state_changed", seen))

    result = await runtime["engine"].state(
        runtime["session_id"], runtime["page_handle"].page_id, element_id
    )
    assert result["exists"] is True
    assert result["visible"] is True
    assert result["enabled"] is True
    assert result["editable"] is True
    assert result["checked"] is False
    assert seen == ["element.state_changed"]


async def test_unknown_element_id_raises() -> None:
    runtime = await build_runtime()
    with pytest.raises(ElementNotFoundError):
        await runtime["engine"].text(
            runtime["session_id"], runtime["page_handle"].page_id, "element_unknown"
        )


async def test_element_id_for_wrong_page_raises() -> None:
    runtime = await build_runtime()
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    other = await runtime["pool"].register_page(runtime["context_id"], FakePage())
    with pytest.raises(ElementNotFoundError):
        await runtime["engine"].text(runtime["session_id"], other.page_id, element_id)


async def test_stale_element_after_page_close_raises() -> None:
    runtime = await build_runtime()
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    await runtime["pool"].remove_page(runtime["page_handle"].page_id)
    with pytest.raises(StaleElementReferenceError):
        await runtime["engine"].text(
            runtime["session_id"], runtime["page_handle"].page_id, element_id
        )


async def test_release_drops_cached_element() -> None:
    runtime = await build_runtime()
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    runtime["engine"].release(element_id)
    with pytest.raises(ElementNotFoundError):
        await runtime["engine"].text(
            runtime["session_id"], runtime["page_handle"].page_id, element_id
        )


async def test_drop_page_clears_refs() -> None:
    runtime = await build_runtime()
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    runtime["engine"].drop_page(runtime["page_handle"].page_id)
    assert runtime["engine"].cache_stats() == {"cached_elements": 0}
    with pytest.raises(ElementNotFoundError):
        await runtime["engine"].text(
            runtime["session_id"], runtime["page_handle"].page_id, element_id
        )


async def test_resolve_locator_returns_raw_locator_without_caching() -> None:
    runtime = await build_runtime()
    locator = await runtime["engine"].resolve_locator(
        runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
    )
    assert locator.selector == "#a"
    assert runtime["engine"].cache_stats() == {"cached_elements": 0}


async def test_cache_stats_tracks_cached_elements() -> None:
    runtime = await build_runtime()
    await runtime["engine"].find(runtime["session_id"], runtime["page_handle"].page_id, "css", "#a")
    await runtime["engine"].find(runtime["session_id"], runtime["page_handle"].page_id, "css", "#b")
    assert runtime["engine"].cache_stats() == {"cached_elements": 2}


async def test_locator_for_resolves_cached_element() -> None:
    runtime = await build_runtime()
    element_id = (
        await runtime["engine"].find(
            runtime["session_id"], runtime["page_handle"].page_id, "css", "#a"
        )
    )["element_id"]
    locator = await runtime["engine"].locator_for(element_id, runtime["page_handle"].page_id)
    assert locator.selector == "#a"


def _collect(name: str, store: list[str]):
    async def handler(event: object) -> None:
        store.append(name)

    return handler
