"""Response Formatter for translating raw tool outputs into Unified Message Models."""

import json
from pathlib import Path
from typing import Any
from browser_mcp.api.chat.schemas import (
    ArtifactMessage,
    StatusMessage,
    WorkflowMessage,
    ErrorMessage,
    TypedError
)

class PresentationGateway:
    """Formats raw tool executions into clean, UI-ready Message Models (Presentation Gateway)."""

    def format_tool_result(self, name: str, content: str, error: bool) -> ArtifactMessage | StatusMessage | WorkflowMessage | ErrorMessage:
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
            return StatusMessage(content=f"Action '{name}' completed successfully.")

        if not isinstance(data, dict):
            return StatusMessage(content=f"Action '{name}' completed.")

        # Generic Artifact Resolver
        # Look for any known artifact paths
        artifact_path = data.get("screenshot_path") or data.get("download_path") or data.get("pdf_path")
        if artifact_path:
            filename = data.get("filename") or Path(artifact_path).name
            mime_type = data.get("mime_type")
            if not mime_type:
                if "screenshot" in name:
                    mime_type = "image/png"
                elif "download" in name:
                    mime_type = "application/octet-stream"
            
            # Map artifact to API endpoint
            url = f"/api/v1/screenshots/{filename}" if "screenshot" in name else f"/api/v1/artifacts/{filename}"

            return ArtifactMessage(
                artifact_id=filename,
                artifact_type=mime_type,
                url=url,
                metadata=data
            )

        if "artifact_id" in data:
            return ArtifactMessage(
                artifact_id=data["artifact_id"],
                artifact_type=data.get("mime_type", "application/octet-stream"),
                url=data.get("url", f"/api/v1/artifacts/{data['artifact_id']}"),
                metadata=data
            )

        # Workflow/Status Emission
        if name == "browser.navigate":
            url = data.get("url", "the page")
            return WorkflowMessage(
                workflow_type="Navigation",
                status="success",
                details=f"Loaded {url}"
            )
        
        if name in ("browser.element_fill", "browser.element_click", "browser.element_hover", "browser.form.fill"):
            return WorkflowMessage(
                workflow_type="Interaction",
                status="success",
                details=f"Interacted with element successfully"
            )
            
        if name == "browser.scrape.text":
            return WorkflowMessage(
                workflow_type="Scraping",
                status="success",
                details="Scraped page content"
            )

        return StatusMessage(content=f"Tool '{name}' completed successfully.")

    def filter_hallucinations(self, text: str, has_artifacts: bool, has_workflows: bool) -> str:
        """Filter out hallucinated claims if evidence is missing."""
        if not text:
            return text
            
        import re
        
        # Claims about artifacts (screenshots, downloads, files)
        artifact_claims = [
            r"screenshot attached", r"taken a screenshot", r"captured a screenshot",
            r"download completed", r"file downloaded",
            r"file uploaded", r"pdf generated"
        ]
        
        # Claims about workflows
        workflow_claims = [
            r"browser opened", r"login succeeded", r"logged in successfully"
        ]
        
        filtered = text
        if not has_artifacts:
            for claim in artifact_claims:
                # Replace hallucinated sentences with neutral or empty
                # Using a simple case-insensitive regex to remove the sentence containing the claim
                pattern = re.compile(r'[^.!?]*\b' + claim + r'\b[^.!?]*[.!?]', re.IGNORECASE)
                filtered = pattern.sub('', filtered)
                
        if not has_workflows:
            for claim in workflow_claims:
                pattern = re.compile(r'[^.!?]*\b' + claim + r'\b[^.!?]*[.!?]', re.IGNORECASE)
                filtered = pattern.sub('', filtered)
                
        return filtered.strip()
