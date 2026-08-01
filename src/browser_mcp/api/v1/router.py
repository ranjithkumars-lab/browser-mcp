from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from browser_mcp.api.dependencies import get_engine, require_api_key
from browser_mcp.api.v1.routes.dashboard import router as dashboard_router
from browser_mcp.api.v1.routes.ws import router as ws_router

router = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
router.include_router(dashboard_router)
router.include_router(ws_router)

EngineDep = Annotated[Any, Depends(get_engine)]


@router.get("/jobs/{job_id}")
async def job(job_id: str, engine: EngineDep):
    try:
        return engine.jobs.get(job_id)
    except KeyError as exc:
        raise HTTPException(404, "job not found") from exc


@router.delete("/jobs/{job_id}", status_code=202)
async def cancel(job_id: str, engine: EngineDep):
    return await engine.jobs.cancel(job_id)


@router.post("/plugins/run", status_code=202)
async def plugin_run(body: dict[str, Any], engine: EngineDep):
    return await engine.submit_tool(
        "browser.plugins.execute", {"name": body["name"], "payload": body.get("payload", {})}
    )


@router.post("/browser/{operation}", status_code=202)
async def browser_operation(
    operation: str, body: dict[str, Any], engine: EngineDep
):
    return await engine.submit_tool(f"browser.{operation}", body)


@router.get("/plugins")
async def plugins(engine: EngineDep):
    return await engine.context.tools.call("browser.plugins.list")
