import pytest
from browser_mcp.api.chat.formatter import ResponseFormatter
from browser_mcp.api.artifacts import Artifact, ArtifactManager

@pytest.fixture
def formatter():
    # Provide a dummy artifact manager mock
    class DummyArtifactManager:
        def generate_urls(self, artifact_id: str):
            return {"download": f"http://localhost/artifacts/{artifact_id}/download"}
        def get_metadata(self, artifact_id: str):
            return {"size": 1024}

    return ResponseFormatter(DummyArtifactManager())

def test_formatter_formats_artifact_success(formatter):
    tool_output = {
        "success": True,
        "artifact_id": "test-id",
        "mime_type": "image/png"
    }
    
    result = formatter.format("browser.screenshot", tool_output)
    
    assert result["type"] == "message"
    assert result["role"] == "artifact"
    assert result["artifact_id"] == "test-id"
    assert result["url"] == "http://localhost/artifacts/test-id/download"
    assert result["metadata"]["size"] == 1024

def test_formatter_formats_error(formatter):
    tool_output = {
        "success": False,
        "error": "Failed to find element"
    }
    
    result = formatter.format("browser.click", tool_output)
    
    assert result["type"] == "message"
    assert result["role"] == "error"
    assert result["error"]["message"] == "Failed to find element"

def test_formatter_formats_status(formatter):
    tool_output = {
        "success": True,
        "status": "Navigation complete"
    }
    
    result = formatter.format("browser.navigate", tool_output)
    
    assert result["type"] == "message"
    assert result["role"] == "status"
    assert result["content"] == "Navigation complete"
