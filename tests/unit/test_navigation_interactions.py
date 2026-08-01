"""Tests for InteractionManager and LocatorResolver."""

from __future__ import annotations

import pytest
from tests.fakes import FakeFrame, FakeLocator, FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.interactions import InteractionManager, LocatorResolver
from browser_mcp.errors import InteractionError

pytestmark = pytest.mark.unit


async def test_click_success() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.click(session_id, page_id, "#click-me")
    assert result["action"] == "click"
    assert result["selector"] == "#click-me"
    assert "duration_ms" in result
    locator = page.locator("#click-me")
    assert locator.clicks == 1


async def test_click_with_options() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await interactions.click(session_id, page_id, "#a", button="right", click_count=1)
    await interactions.click(session_id, page_id, "#b", timeout_ms=2_000)


async def test_click_failure_raises_interaction_error() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id
    locator = page.locator("#bad")
    locator.fail_next = True

    with pytest.raises(InteractionError):
        await interactions.click(session_id, page_id, "#bad")


async def test_double_click_success() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.double_click(session_id, page_id, "#dbl")
    assert result["action"] == "double_click"
    assert page.locator("#dbl").dblclicks == 1


async def test_right_click_success() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.right_click(session_id, page_id, "#rc")
    assert result["action"] == "right_click"
    assert page.locator("#rc").clicks == 1


async def test_hover_success() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.hover(session_id, page_id, "#hv")
    assert result["action"] == "hover"
    assert page.locator("#hv").hovers == 1


async def test_scroll_to_evaluates() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.scroll_to(session_id, page_id, 10, 20)
    assert result["action"] == "scroll_to"
    assert result["x"] == 10
    assert result["y"] == 20
    assert page.evaluations[-1][0] == "(args) => window.scrollTo(args.x, args.y)"
    assert page.evaluations[-1][1] == {"x": 10, "y": 20}


async def test_scroll_by_evaluates() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.scroll_by(session_id, page_id, -5, 15)
    assert result["action"] == "scroll_by"
    assert page.evaluations[-1][0] == "(args) => window.scrollBy(args.x, args.y)"


async def test_scroll_element_success() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    page: FakePage = runtime["page"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    result = await interactions.scroll_element(session_id, page_id, "#el")
    assert result["action"] == "scroll_element"
    assert page.locator("#el").scrolled == 1


async def test_empty_selector_rejected() -> None:
    runtime = await build_runtime()
    interactions: InteractionManager = runtime["interactions"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    with pytest.raises(InteractionError):
        await interactions.click(session_id, page_id, "   ")


async def test_locator_resolver_targets_frame() -> None:
    inner = FakeFrame(name="inner", url="https://inner.example/")
    main = FakeFrame(url="https://main.example/")
    page = FakePage(url="https://main.example/", frames=[main, inner])
    runtime = await build_runtime(page=page)
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await runtime["frames"].sync_frames(session_id, page_id)
    inner_frame = next(s for s in runtime["state"].list_frames(page_id) if not s.is_main)

    resolver: LocatorResolver = LocatorResolver(runtime["frames"])
    locator = await resolver.resolve(session_id, page_id, "#inside", frame_id=inner_frame.frame_id)
    assert isinstance(locator, FakeLocator)
    assert locator.frame is not None
    assert locator.selector == "#inside"


async def test_locator_resolver_page_target() -> None:
    runtime = await build_runtime()
    resolver: LocatorResolver = LocatorResolver(runtime["frames"])
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    locator = await resolver.resolve(session_id, page_id, "#main")
    assert isinstance(locator, FakeLocator)
    assert locator.frame is None
