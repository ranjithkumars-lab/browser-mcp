from pathlib import Path
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

def _get_artifact_manager(request: Request) -> Any:
    return request.app.state.artifact_manager

ScreenshotStoreDep = Annotated[ScreenshotStore, Depends(_get_screenshot_store)]
ArtifactManagerDep = Annotated[Any, Depends(_get_artifact_manager)]


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
    if not filename or filename != Path(filename).name:
        raise HTTPException(status_code=400, detail="invalid screenshot filename")
    record = store.get(filename)
    if record is None:
        raise HTTPException(status_code=404, detail="screenshot not found")
    return FileResponse(
        record.path,
        media_type=record.mime_type,
        headers={"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"},
    )

@router.get("/artifacts/{artifact_id}")
async def artifact_file(artifact_id: str, manager: ArtifactManagerDep) -> FileResponse:
    """Serve a captured artifact file by its generated artifact_id."""
    artifact = manager.get_artifact(artifact_id)
    if artifact is None:
        raise HTTPException(status_code=404, detail="artifact not found")
    return FileResponse(
        artifact.original_path,
        media_type=artifact.mime,
        headers={"Cache-Control": "public, max-age=3600, stale-while-revalidate=86400"},
    )
