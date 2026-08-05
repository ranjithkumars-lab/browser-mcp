"""Artifact management lifecycle and registry."""

from __future__ import annotations

import json
from uuid import uuid4
from typing import Any, cast
from pydantic import BaseModel
from browser_mcp.api.screenshots import ScreenshotStore

class Artifact(BaseModel):
    artifact_id: str
    filename: str
    mime_type: str
    size: int
    original_path: str


class ArtifactManager:
    """Manages the lifecycle of artifacts generated during chat sessions."""
    
    def __init__(self, screenshot_store: ScreenshotStore) -> None:
        self._screenshots = screenshot_store
        self._artifacts: dict[str, Artifact] = {}

    def get_artifact(self, artifact_id: str) -> Artifact | None:
        return self._artifacts.get(artifact_id)

    def process_tool_result(self, name: str, content: str) -> str:
        """Parse tool results and convert them to artifacts if they contain files."""
        if name not in ("browser.screenshot", "browser.download"):
            return content
            
        try:
            raw = json.loads(content)
        except (TypeError, ValueError):
            return content
            
        if not isinstance(raw, dict):
            return content
            
        if name == "browser.screenshot":
            path = raw.get("screenshot_path")
            if not path:
                return content
                
            filename = ScreenshotStore.filename_from_path(str(path))
            mime_type = raw.get("mime_type", "image/png")
            size = raw.get("file_size_bytes", 0)
            
            artifact_id = uuid4().hex[:8]
            artifact = Artifact(
                artifact_id=artifact_id,
                filename=filename,
                mime_type=mime_type,
                size=int(size),
                original_path=str(path)
            )
            self._artifacts[artifact_id] = artifact
            
            # Return a summarized preview for the LLM
            return json.dumps({
                "artifact_id": artifact_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": size,
                "message": f"Saved. You MUST cite this artifact in your response using markdown: ![Screenshot](artifact:{artifact_id})"
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
                artifact_id=artifact_id,
                filename=filename,
                mime_type=mime_type,
                size=int(size),
                original_path=str(path)
            )
            self._artifacts[artifact_id] = artifact
            
            return json.dumps({
                "artifact_id": artifact_id,
                "filename": filename,
                "mime_type": mime_type,
                "size": size,
                "message": f"Downloaded successfully. You MUST cite this artifact in your response using a markdown link: [{filename}](artifact:{artifact_id})"
            }, ensure_ascii=False)

