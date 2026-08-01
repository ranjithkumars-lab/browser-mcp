from __future__ import annotations
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
def mount_spa(app: FastAPI, directory: str) -> None:
    root = Path(directory)
    if not root.is_dir():
        return
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="ui-assets") if (root / "assets").is_dir() else None
    index = root / "index.html"
    if index.exists():
        @app.get("/", include_in_schema=False)
        @app.get("/{path:path}", include_in_schema=False)
        async def spa(path: str = "") -> FileResponse:
            candidate = root / path
            return FileResponse(candidate if candidate.is_file() else index)
