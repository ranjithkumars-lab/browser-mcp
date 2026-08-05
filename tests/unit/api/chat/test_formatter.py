import pytest
import json
from browser_mcp.api.chat.formatter import ResponseFormatter
from browser_mcp.api.artifacts import Artifact, ArtifactManager

@pytest.fixture
def formatter():
    return ResponseFormatter()

def test_formatter_formats_artifact_success(formatter):
    tool_output = json.dumps({
        "success": True,
        "artifact_id": "test-id",
        "mime_type": "image/png",
        "url": "http://localhost/artifacts/test-id/download"
    })
    
    result = formatter.format_tool_result("browser.screenshot", tool_output, False)
    
    assert result.role == "artifact"
    assert result.artifact_id == "test-id"
    assert result.url == "http://localhost/artifacts/test-id/download"
    assert result.artifact_type == "image/png"

def test_formatter_formats_error(formatter):
    tool_output = "Traceback error: Failed to find element"
    
    result = formatter.format_tool_result("browser.click", tool_output, True)
    
    assert result.role == "error"
    assert result.error.message == "Tool 'browser.click' failed during execution."

def test_formatter_formats_status(formatter):
    tool_output = json.dumps({
        "success": True,
        "url": "https://example.com"
    })
    
    result = formatter.format_tool_result("browser.navigate", tool_output, False)
    
    assert result.role == "status"
    assert result.content == "Navigated to https://example.com."
