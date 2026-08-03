"""Tests for the API screenshot store wiring and MCP-direct serving."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from browser_mcp.api.app import _screenshot_store
from browser_mcp.api.screenshots import ScreenshotRecord, ScreenshotStore
from browser_mcp.api.v1.router import router as v1_router

pytestmark = pytest.mark.unit


class _FakeManager:
    def __init__(self, store: ScreenshotStore) -> None:
        self.store = store


class _FakeContainer:
    def __init__(self, manager: Any | None = None) -> None:
        self._manager = manager

    def has(self, name: str) -> bool:
        return name == "screenshot_manager" and self._manager is not None

    def resolve(self, name: str) -> Any:
        if self._manager is None:
            raise KeyError(name)
        return self._manager


def test_screenshot_store_prefers_manager_store() -> None:
    store = ScreenshotStore()
    context = SimpleNamespace(container=_FakeContainer(_FakeManager(store)))
    assert _screenshot_store(context) is store


def test_screenshot_store_falls_back_to_new_store() -> None:
    context = SimpleNamespace(container=_FakeContainer())
    store = _screenshot_store(context)
    assert isinstance(store, ScreenshotStore)


def test_screenshot_store_handles_no_context() -> None:
    assert isinstance(_screenshot_store(None), ScreenshotStore)


def test_mcp_capture_is_servable_via_api(tmp_path) -> None:
    """A screenshot captured through the MCP tool (not chat) is served by the API."""
    target = tmp_path / "page_e28403baa2a7_20260803T142319Z_9e547664.png"
    target.write_bytes(b"png-bytes")
    store = ScreenshotStore()
    store.record(
        ScreenshotRecord(
            filename=target.name,
            path=str(target),
            session_id="session_427ac08df02b",
            page_id="page_e28403baa2a7",
            url="https://www.example.com/",
            title="Example Domain",
            mime_type="image/png",
        )
    )
    app = FastAPI()
    app.state.screenshot_store = store
    app.include_router(v1_router)
    client = TestClient(app)
    response = client.get(f"/api/v1/screenshots/{target.name}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert response.content == b"png-bytes"
