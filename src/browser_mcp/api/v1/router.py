from fastapi import APIRouter, Depends, HTTPException
from typing import Any
from browser_mcp.api.dependencies import get_engine, require_api_key
router=APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
@router.get("/jobs/{job_id}")
async def job(job_id: str, engine: Any=Depends(get_engine)):
    try: return engine.jobs.get(job_id)
    except KeyError: raise HTTPException(404, "job not found")
@router.delete("/jobs/{job_id}", status_code=202)
async def cancel(job_id: str, engine: Any=Depends(get_engine)): return await engine.jobs.cancel(job_id)
@router.post("/plugins/run", status_code=202)
async def plugin_run(body: dict[str, Any], engine: Any=Depends(get_engine)): return await engine.submit_tool("browser.plugins.execute", {"name": body["name"], "payload": body.get("payload", {})})
@router.post("/browser/{operation}", status_code=202)
async def browser_operation(operation: str, body: dict[str, Any], engine: Any=Depends(get_engine)): return await engine.submit_tool(f"browser.{operation}", body)
@router.get("/plugins")
async def plugins(engine: Any=Depends(get_engine)): return await engine.context.tools.call("browser.plugins.list")
