"""Execution Planner for browser automation.

The Execution Planner receives high-level tasks and plans a deterministic 
sequence of Browser Executor steps to complete them, avoiding the need for 
the LLM to act as a browser engine.
"""

import asyncio
from typing import Any
from browser_mcp.browser.orchestration.executor import BrowserExecutor

class ExecutionPlanner:
    def __init__(self, executor: BrowserExecutor):
        self.executor = executor

    async def execute_task(self, session_id: str, page_id: str, task: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Plan and execute a high-level task."""
        if task == "login":
            return await self._plan_login(session_id, page_id, parameters)
        elif task == "register":
            return await self._plan_registration(session_id, page_id, parameters)
        else:
            raise ValueError(f"Unknown high-level task: {task}")

    async def _plan_login(self, session_id: str, page_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Deterministic login workflow."""
        url = parameters.get("url")
        if url:
            await self.executor.navigate_and_wait(session_id, page_id, url)
        
        credentials = {k: v for k, v in parameters.items() if k != "url"}
        await self.executor.form_engine.fill_and_submit(session_id, page_id, credentials)
        await self.executor.verify_success(session_id, page_id)
        
        screenshot_result = await self.executor.screenshot.capture_viewport(session_id, page_id)
        return {
            "success": True,
            "message": "Login successful.",
            "screenshot": screenshot_result
        }

    async def _plan_registration(self, session_id: str, page_id: str, parameters: dict[str, Any]) -> dict[str, Any]:
        """Deterministic registration workflow with dependent dropdown support."""
        url = parameters.get("url")
        if url:
            await self.executor.navigate_and_wait(session_id, page_id, url)
        
        fields = {k: v for k, v in parameters.items() if k != "url"}
        await self.executor.form_engine.fill_and_submit(session_id, page_id, fields)
        await self.executor.verify_success(session_id, page_id)
        
        screenshot_result = await self.executor.screenshot.capture_viewport(session_id, page_id)
        return {
            "success": True,
            "message": "Registration successful.",
            "screenshot": screenshot_result
        }
