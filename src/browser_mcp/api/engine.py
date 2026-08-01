from __future__ import annotations
from typing import Any
from browser_mcp.api.jobs.manager import JobManager
class ApiEngine:
    def __init__(self, context: Any, jobs: JobManager) -> None: self.context, self.jobs=context, jobs
    async def submit_tool(self, tool_name: str, arguments: dict[str, Any]) -> object:
        return await self.jobs.submit(tool_name, lambda: self.context.tools.call(tool_name, **arguments))
