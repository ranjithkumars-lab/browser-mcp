from __future__ import annotations

from collections.abc import Awaitable, Callable
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def _spa_fallback(root: Path, index: Path) -> Callable[[Request], Awaitable[FileResponse]]:
    async def _handler(request: Request) -> FileResponse:
        candidate = root / request.path_params.get("path", "")
        return FileResponse(candidate if candidate.is_file() else index)

    return _handler


def mount_spa(app: FastAPI, directory: str) -> None:
    root = Path(directory)
    if not root.is_dir():
        return
    assets = root / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="ui-assets")
    index = root / "index.html"
    if index.exists():
        app.add_api_route(
            "/{path:path}",
            _spa_fallback(root, index),
            include_in_schema=False,
            methods=["GET"],
        )
