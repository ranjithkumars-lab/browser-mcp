"""Response Formatter for translating raw tool outputs into Unified Message Models."""

import json
from typing import Any
from browser_mcp.api.chat.schemas import (
    ArtifactMessage,
    StatusMessage,
    ErrorMessage,
    TypedError
)

class ResponseFormatter:
    """Formats raw tool executions into clean, UI-ready Message Models."""

    def format_tool_result(self, name: str, content: str, error: bool) -> ArtifactMessage | StatusMessage | ErrorMessage:
        """Parse a tool execution result into a unified message."""
        if error:
            return ErrorMessage(
                error=TypedError(
                    type="ToolError",
                    message=f"Tool '{name}' failed during execution.",
                    details={"raw": content}
                )
            )

        # Attempt to parse JSON content from the tool
        try:
            data = json.loads(content)
        except (TypeError, ValueError):
            # Not JSON, return as a generic status message
            return StatusMessage(content=f"Action '{name}' completed successfully.")

        if not isinstance(data, dict):
            return StatusMessage(content=f"Action '{name}' completed.")

        # If this tool produced an artifact (handled by ArtifactManager)
        if "artifact_id" in data:
            return ArtifactMessage(
                artifact_id=data["artifact_id"],
                artifact_type=data.get("mime_type", "application/octet-stream"),
                url=data.get("url", ""),
                metadata=data
            )

        # For regular browser actions (clicks, fills, navigation)
        if name == "browser.navigate":
            url = data.get("url", "the page")
            return StatusMessage(content=f"Navigated to {url}.")
        
        if name in ("browser.element_fill", "browser.element_click", "browser.element_hover"):
            return StatusMessage(content=f"Interacted with element successfully.")
            
        if name == "browser.scrape.text":
            return StatusMessage(content=f"Scraped page content successfully.")

        return StatusMessage(content=f"Tool '{name}' completed successfully.")

