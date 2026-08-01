"""Tests for FrameManager frame discovery and resolution."""

from __future__ import annotations

import pytest
from tests.fakes import FakeFrame, FakePage
from tests.helpers import build_runtime

from browser_mcp.browser.navigation.frames import FrameManager
from browser_mcp.errors import FrameError

pytestmark = pytest.mark.unit


def _page_with_frames() -> FakePage:
    main = FakeFrame(url="https://main.example/")
    return FakePage(
        url="https://main.example/",
        frames=[main, FakeFrame(name="inner", url="https://child.example/", parent=main)],
    )


async def test_sync_frames_discovers_hierarchy() -> None:
    page = _page_with_frames()
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    snapshots = await frames.sync_frames(session_id, page_id)
    assert len(snapshots) == 2
    main = next(s for s in snapshots if s.is_main)
    inner = next(s for s in snapshots if not s.is_main)
    assert main.name == ""
    assert inner.name == "inner"
    assert inner.parent_frame_id == main.frame_id
    assert inner.url == "https://child.example/"
    assert main.url == "https://main.example/"


async def test_sync_preserves_frame_ids() -> None:
    page = _page_with_frames()
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    first = await frames.sync_frames(session_id, page_id)
    second = await frames.sync_frames(session_id, page_id)
    assert {s.frame_id for s in first} == {s.frame_id for s in second}


async def test_sync_emits_attached_events() -> None:
    page = _page_with_frames()
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    events = runtime["events"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    received: list[tuple[str, str]] = []

    async def handler(event: object) -> None:
        received.append((event.event_name, event.payload["action"]))

    events.subscribe("frame.changed", handler)
    await frames.sync_frames(session_id, page_id)
    assert ("frame.changed", "attached") in received
    assert len([a for _, a in received if a == "attached"]) == 2


async def test_sync_drops_detached_frames() -> None:
    main = FakeFrame(url="https://main.example/")
    page = FakePage(
        url="https://main.example/",
        frames=[main, FakeFrame(name="inner", url="https://child.example/", parent=main)],
    )
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    await frames.sync_frames(session_id, page_id)
    assert len(await frames.sync_frames(session_id, page_id)) == 2

    page._frames = [main]
    remaining = await frames.sync_frames(session_id, page_id)
    assert len(remaining) == 1
    assert remaining[0].is_main
    with pytest.raises(FrameError):
        await frames.frame_object_for(session_id, page_id, "frame_not_present")


async def test_frame_object_for_resolves() -> None:
    page = _page_with_frames()
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    snapshots = await frames.sync_frames(session_id, page_id)
    inner = next(s for s in snapshots if not s.is_main)
    obj = await frames.frame_object_for(session_id, page_id, inner.frame_id)
    assert obj.name == "inner"


async def test_list_frames_payload() -> None:
    page = _page_with_frames()
    runtime = await build_runtime(page=page)
    frames: FrameManager = runtime["frames"]
    session_id, page_id = runtime["session_id"], runtime["page_handle"].page_id

    payloads = await frames.list_frames(session_id, page_id)
    assert len(payloads) == 2
    for payload in payloads:
        assert set(payload) == {
            "frame_id",
            "page_id",
            "parent_frame_id",
            "name",
            "url",
            "is_main",
        }
