"""Tests for the central StateManager."""

from __future__ import annotations

import pytest
from tests.fakes import FakeFrame
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.state import FrameState, PopupState, StateManager
from browser_mcp.errors import FrameError, PopupError, SessionError

pytestmark = pytest.mark.unit


async def test_hierarchy_lookups() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    assert state.session(runtime["session_id"]).session_id == "s1"
    assert state.browser("b1").browser_id == "b1"
    assert state.context(runtime["context_id"]).context_id == runtime["context_id"]
    assert state.page(runtime["page_handle"].page_id).page_id == runtime["page_handle"].page_id


async def test_page_in_session_ownership() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    handle = state.page_in_session("s1", runtime["page_handle"].page_id)
    assert handle.page_id == runtime["page_handle"].page_id
    with pytest.raises(SessionError):
        state.page_in_session("other-session", runtime["page_handle"].page_id)


async def test_context_in_session_ownership() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    handle = state.context_in_session("s1", runtime["context_id"])
    assert handle.context_id == runtime["context_id"]
    with pytest.raises(SessionError):
        state.context_in_session("other-session", runtime["context_id"])


async def test_frame_registry() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    page_id = runtime["page_handle"].page_id

    state.register_frame(
        FrameState(
            frame_id="f1",
            page_id=page_id,
            context_id=runtime["context_id"],
            browser_id="b1",
            parent_frame_id=None,
            is_main=True,
        )
    )
    state.register_frame(
        FrameState(
            frame_id="f2",
            page_id=page_id,
            context_id=runtime["context_id"],
            browser_id="b1",
            parent_frame_id="f1",
        )
    )

    frames = state.list_frames(page_id)
    assert {f.frame_id for f in frames} == {"f1", "f2"}
    assert state.main_frame(page_id).frame_id == "f1"
    assert state.has_frame("f1")
    assert not state.has_frame("nope")
    with pytest.raises(FrameError):
        state.frame("nope")


async def test_unregister_page_frames() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    page_id = runtime["page_handle"].page_id
    state.register_frame(
        FrameState(
            frame_id="f1",
            page_id=page_id,
            context_id=runtime["context_id"],
            browser_id="b1",
        )
    )
    state.unregister_page_frames(page_id)
    assert state.list_frames(page_id) == []


async def test_frame_guid_binding() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    frame = FakeFrame(url="https://x.example")
    guid = frame._impl_obj._guid
    state.bind_frame_object("f1", guid, frame)
    assert state.frame_id_for_guid(guid) == "f1"
    assert state.frame_object("f1") is frame
    state.drop_frame("f1")
    assert state.frame_id_for_guid(guid) is None
    with pytest.raises(FrameError):
        state.frame_object("f1")


async def test_popup_registry() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    state.register_popup(
        PopupState(
            popup_id="p1",
            origin_page_id=runtime["page_handle"].page_id,
            context_id=runtime["context_id"],
            browser_id="b1",
        )
    )
    assert [p.popup_id for p in state.popups()] == ["p1"]
    assert state.popup("p1").origin_page_id == runtime["page_handle"].page_id
    state.close_popup("p1")
    assert state.popups() == []
    with pytest.raises(PopupError):
        state.popup("p1")


async def test_metrics() -> None:
    runtime = await build_runtime()
    state: StateManager = runtime["state"]
    metrics = state.metrics()
    assert metrics["browsers"] == 1
    assert metrics["contexts"] == 1
    assert metrics["pages"] == 1
    assert metrics["frames"] == 0
    assert metrics["popups"] == 0
    assert metrics["sessions"] == 1
