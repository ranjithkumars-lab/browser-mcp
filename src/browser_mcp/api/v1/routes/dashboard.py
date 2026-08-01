from __future__ import annotations
from fastapi import APIRouter, Depends
from typing import Any
from browser_mcp.api.dependencies import get_engine
from browser_mcp.api.gateways.dashboard import DashboardGateway
router = APIRouter(tags=["dashboard"])
@router.get("/dashboard")
async def dashboard(engine: Any = Depends(get_engine)) -> dict[str, Any]:
    return await DashboardGateway(engine.context, engine).summary()
