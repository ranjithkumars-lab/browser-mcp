import pytest
from unittest.mock import AsyncMock, MagicMock
from browser_mcp.browser.orchestration.planner import ExecutionPlanner
from browser_mcp.browser.orchestration.executor import BrowserExecutor
from browser_mcp.browser.orchestration.forms import FormEngine
from browser_mcp.browser.navigation.manager import NavigationManager
from browser_mcp.browser.screenshot import ScreenshotManager
from browser_mcp.browser.elements.engine import ElementEngine

@pytest.fixture
def mock_deps():
    nav = AsyncMock(spec=NavigationManager)
    screenshot = AsyncMock(spec=ScreenshotManager)
    screenshot.capture_viewport.return_value = {"type": "artifact", "id": "test_artifact"}
    elements = AsyncMock(spec=ElementEngine)
    form = FormEngine(elements)
    
    # Mock finding elements and HTML for the form engine
    elements.find.side_effect = [{"element_id": "username_id"}, {"element_id": "password_id"}, {"element_id": "submit_id"}]
    elements.html.return_value = {"html": "<input type='text' />"}
    
    executor = BrowserExecutor(nav, screenshot, form)
    # mock verification to avoid sleeping in tests
    executor.verify_success = AsyncMock() 
    return nav, screenshot, elements, form, executor

@pytest.mark.asyncio
async def test_execution_planner_login(mock_deps):
    nav, screenshot, elements, form, executor = mock_deps
    planner = ExecutionPlanner(executor)
    
    params = {
        "url": "https://example.com/login",
        "username": "admin",
        "password": "123"
    }
    
    result = await planner.execute_task("sess1", "page1", "login", params)
    
    nav.navigate.assert_called_once_with("sess1", "page1", "https://example.com/login")
    assert elements.fill.call_count == 2
    elements.click.assert_called_once()
    
    executor.verify_success.assert_called_once_with("sess1", "page1")
    screenshot.capture_viewport.assert_called_once_with("sess1", "page1")
    
    assert result["success"] is True
    assert result["screenshot"] == {"type": "artifact", "id": "test_artifact"}

@pytest.mark.asyncio
async def test_execution_planner_register(mock_deps):
    nav, screenshot, elements, form, executor = mock_deps
    planner = ExecutionPlanner(executor)
    
    params = {
        "url": "https://example.com/register",
        "name": "John",
        "email": "john@example.com"
    }
    
    # Adjust mock to return correctly for 2 fields + 1 submit
    elements.find.side_effect = [{"element_id": "name_id"}, {"element_id": "email_id"}, {"element_id": "submit_id"}]
    
    result = await planner.execute_task("sess1", "page1", "register", params)
    
    nav.navigate.assert_called_once_with("sess1", "page1", "https://example.com/register")
    assert elements.fill.call_count == 2
    elements.click.assert_called_once()
    
    assert result["success"] is True
