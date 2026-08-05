from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from browser_mcp.api.chat.agent import ChatAgent
from browser_mcp.api.dependencies import get_engine
from browser_mcp.api.engine import ApiEngine
from browser_mcp.api.jobs.manager import JobManager
from browser_mcp.api.screenshots import ScreenshotStore
from browser_mcp.api.artifacts import ArtifactManager
from browser_mcp.api.static import mount_spa
from browser_mcp.api.v1.router import router
from browser_mcp.config.models import ApiConfig, BrowserSettings


def _screenshot_store(context: Any) -> ScreenshotStore:
    """Return the shared screenshot store from the wired browser context.

    The :class:`ScreenshotManager` records every capture (MCP tool, REST job,
    chat agent) into its own store; the API serves from that same store so all
    screenshots are reachable at ``/api/v1/screenshots``.
    """
    if context is not None and context.container.has("screenshot_manager"):
        manager = context.container.resolve("screenshot_manager")
        store = getattr(manager, "store", None)
        if store is not None:
            return store
    return ScreenshotStore()


def _run_browser_lifespan(context: Any) -> Any:
    """Wrap ``context.start()``/``context.stop()`` in a FastAPI lifespan.

    The browser core registers ``factory.start`` as a startup hook, so its
    lifecycle must run or the browser tools fail with "factory not started".
    """

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        if context is not None and hasattr(context, "start"):
            await context.start()
        try:
            yield
        finally:
            if context is not None and hasattr(context, "stop"):
                await context.stop()

    return lifespan


def create_api_app(
    context: Any,
    settings: ApiConfig | None = None,
    browser_settings: BrowserSettings | None = None,
) -> FastAPI:
    config = settings or ApiConfig()
    browser = browser_settings or BrowserSettings()
    app = FastAPI(
        title="Browser MCP REST API",
        docs_url="/docs" if config.enable_docs else None,
        redoc_url="/redoc" if config.enable_redoc else None,
        lifespan=_run_browser_lifespan(context),
    )
    screenshot_store = _screenshot_store(context)
    app.state.screenshot_store = screenshot_store
    app.state.api_engine = ApiEngine(context)
    app.state.job_manager = JobManager(app.state.api_engine)
    
    artifact_manager = ArtifactManager(screenshot_store)
    app.state.artifact_manager = artifact_manager
    
    app.state.chat_agent = ChatAgent(context.tools, browser.ollama, browser.chat, artifact_manager)
    
    app.include_router(router)
    mount_spa(app, browser.ui.static_directory)
    return app
