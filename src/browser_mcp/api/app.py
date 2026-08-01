from __future__ import annotations
from fastapi import FastAPI
from typing import Any
from browser_mcp.config.models import ApiConfig
from browser_mcp.api.engine import ApiEngine
from browser_mcp.api.jobs.manager import JobManager
from browser_mcp.api.v1.router import router
def create_api_app(context: Any, settings: ApiConfig | None = None) -> FastAPI:
    config = settings or context.settings.api
    app=FastAPI(title="Browser MCP REST API", docs_url="/docs" if config.enable_docs else None, redoc_url="/redoc" if config.enable_redoc else None)
    app.state.api_config=config; app.state.api_engine=ApiEngine(context, JobManager(config.job_retention_minutes))
    app.include_router(router)
    return app
