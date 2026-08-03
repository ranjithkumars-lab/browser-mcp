from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse

from browser_mcp.api.chat.routes import router as chat_router
from browser_mcp.api.dependencies import get_engine
from browser_mcp.api.screenshots import ScreenshotStore
from browser_mcp.api.v1.routes.dashboard import router as dashboard_router
from browser_mcp.api.v1.routes.ws import router as ws_router

router = APIRouter(prefix="/api/v1")
router.include_router(dashboard_router)
router.include_router(ws_router)
router.include_router(chat_router)

EngineDep = Annotated[Any, Depends(get_engine)]


def _get_screenshot_store(request: Request) -> ScreenshotStore:
    return request.app.state.screenshot_store


ScreenshotStoreDep = Annotated[ScreenshotStore, Depends(_get_screenshot_store)]


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
async def browser_operation(operation: str, body: dict[str, Any], engine: EngineDep):
    return await engine.submit_tool(f"browser.{operation}", body)


@router.get("/plugins")
async def plugins(engine: EngineDep):
    return await engine.context.tools.call("browser.plugins.list")


@router.get("/screenshots")
async def screenshots(
    store: ScreenshotStoreDep, user_id: str | None = None
) -> list[dict[str, object]]:
    """List captured screenshots, optionally filtered by owning user."""
    return store.list(user_id=user_id)


@router.get("/screenshots/{filename}")
async def screenshot_file(filename: str, store: ScreenshotStoreDep) -> FileResponse:
    """Serve a captured screenshot file by its basename."""
    record = store.get(filename)
    if record is None:
        raise HTTPException(status_code=404, detail="screenshot not found")
    path = record.path
    return FileResponse(path, media_type=record.mime_type)
