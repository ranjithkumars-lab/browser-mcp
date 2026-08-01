from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends

from browser_mcp.api.dependencies import get_engine
from browser_mcp.api.gateways.dashboard import DashboardGateway

router = APIRouter(tags=["dashboard"])

EngineDep = Annotated[Any, Depends(get_engine)]


@router.get("/dashboard")
async def dashboard(engine: EngineDep) -> dict[str, Any]:
    return await DashboardGateway(engine.context, engine).summary()
