"""Tests for the screenshot store and its HTTP routes."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from browser_mcp.api.screenshots import ScreenshotRecord, ScreenshotStore
from browser_mcp.api.v1.router import router as v1_router

pytestmark = pytest.mark.unit


def _record(path: str = "/screenshots/a.png", user_id: str | None = "u1") -> ScreenshotRecord:
    return ScreenshotRecord(
        filename=ScreenshotStore.filename_from_path(path),
        path=path,
        user_id=user_id,
        session_id="s1",
        page_id="p1",
        url="https://example.com/",
        title="Example",
        mime_type="image/png",
        width=1280,
        height=720,
    )


def test_store_round_trip() -> None:
    store = ScreenshotStore()
    store.record(_record())
    record = store.get("a.png")
    assert record is not None
    assert record.user_id == "u1"
    assert record.url == "https://example.com/"
    assert record.width == 1280


def test_store_get_missing_returns_none() -> None:
    store = ScreenshotStore()
    assert store.get("missing.png") is None


def test_store_list_filters_by_user() -> None:
    store = ScreenshotStore()
    store.record(_record("/screenshots/a.png", user_id="u1"))
    store.record(_record("/screenshots/b.png", user_id="u2"))
    assert [r["filename"] for r in store.list()] == ["b.png", "a.png"]
    assert [r["filename"] for r in store.list(user_id="u1")] == ["a.png"]
    assert store.list(user_id="u9") == []


def test_store_evicts_oldest_when_full() -> None:
    store = ScreenshotStore(max_records=2)
    store.record(_record("/screenshots/a.png"))
    store.record(_record("/screenshots/b.png"))
    store.record(_record("/screenshots/c.png"))
    assert store.get("a.png") is None
    assert store.get("b.png") is not None
    assert store.get("c.png") is not None


def test_filename_from_path_handles_windows_and_posix() -> None:
    assert ScreenshotStore.filename_from_path("C:/shots/a.png") == "a.png"
    assert ScreenshotStore.filename_from_path("/shots/b.png") == "b.png"


def _app_client() -> TestClient:
    app = FastAPI()
    app.state.screenshot_store = ScreenshotStore()
    app.include_router(v1_router)
    return TestClient(app)


def test_screenshots_route_empty_list() -> None:
    client = _app_client()
    response = client.get("/api/v1/screenshots")
    assert response.status_code == 200
    assert response.json() == []


def test_screenshots_route_lists_and_filters() -> None:
    app = FastAPI()
    app.state.screenshot_store = ScreenshotStore()
    app.include_router(v1_router)
    store = app.state.screenshot_store
    store.record(_record("/screenshots/a.png", user_id="u1"))
    store.record(_record("/screenshots/b.png", user_id="u2"))
    client = TestClient(app)
    payload = client.get("/api/v1/screenshots").json()
    assert [item["filename"] for item in payload] == ["b.png", "a.png"]
    filtered = client.get("/api/v1/screenshots", params={"user_id": "u1"}).json()
    assert [item["filename"] for item in filtered] == ["a.png"]


def test_screenshot_file_route_serves_recorded_path(tmp_path) -> None:
    target = tmp_path / "a.png"
    target.write_bytes(b"png-bytes")
    app = FastAPI()
    app.state.screenshot_store = ScreenshotStore()
    app.include_router(v1_router)
    app.state.screenshot_store.record(_record(str(target), user_id="u1"))
    client = TestClient(app)
    response = client.get("/api/v1/screenshots/a.png")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"


def test_screenshot_file_route_404_for_unknown() -> None:
    client = _app_client()
    response = client.get("/api/v1/screenshots/missing.png")
    assert response.status_code == 404
