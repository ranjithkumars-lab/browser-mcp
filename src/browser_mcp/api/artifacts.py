"""Artifact management lifecycle and registry."""

from __future__ import annotations

import json
from uuid import uuid4
from typing import Any, cast
from pydantic import BaseModel
from browser_mcp.api.screenshots import ScreenshotStore

class Artifact(BaseModel):
    id: str
    type: str
    mime: str
    thumbnail: str | None = None
    download_url: str | None = None
    preview_url: str | None = None
    status: str = "ready"
    original_path: str
    size: int


class ArtifactManager:
    """Manages the lifecycle of artifacts generated during chat sessions."""
    
    def __init__(self, screenshot_store: ScreenshotStore) -> None:
        self._screenshots = screenshot_store
        self._artifacts: dict[str, Artifact] = {}

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def process_tool_result(self, name: str, content: str) -> str:
        """Parse tool results and convert them to artifacts if they contain files."""
        if not (name.startswith("browser.screenshot") or name == "browser.download"):
            return content
            
        try:
            raw = json.loads(content)
        except (TypeError, ValueError):
            return content
            
        if not isinstance(raw, dict):
            return content
            
        if name.startswith("browser.screenshot"):
            path = raw.get("screenshot_path")
            if not path:
                return content
                
            filename = ScreenshotStore.filename_from_path(str(path))
            mime_type = raw.get("mime_type", "image/png")
            size = raw.get("file_size_bytes", 0)
            
            artifact_id = uuid4().hex[:8]
            artifact = Artifact(
                id=artifact_id,
                type="image",
                mime=mime_type,
                size=int(size),
                original_path=str(path),
                preview_url=f"/api/v1/artifacts/{artifact_id}"
            )
            self._artifacts[artifact_id] = artifact
            
            return json.dumps({
                "artifact_id": artifact_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": size,
                "url": artifact.preview_url,
                "message": "Screenshot saved successfully."
            }, ensure_ascii=False)
            
        if name == "browser.download":
            path = raw.get("file_path")
            if not path:
                return content
                
            filename = raw.get("file_name", "downloaded_file")
            mime_type = raw.get("mime_type", "application/octet-stream")
            size = raw.get("file_size_bytes", 0)
            
            artifact_id = uuid4().hex[:8]
            artifact = Artifact(
                id=artifact_id,
                type="file",
                mime=mime_type,
                size=int(size),
                original_path=str(path),
                download_url=f"/api/v1/artifacts/{artifact_id}"
            )
            self._artifacts[artifact_id] = artifact
            
            return json.dumps({
                "artifact_id": artifact_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": size,
                "url": artifact.download_url,
                "message": "File downloaded successfully."
            }, ensure_ascii=False)

