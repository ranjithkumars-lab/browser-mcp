"""Orchestration toolkit.

Exposes high-level execution planning tools to the LLM.
"""

from typing import Any, Callable
from enterprise_mcp.tools.decorators import tool
from browser_mcp.browser.orchestration.planner import ExecutionPlanner
from browser_mcp.tools.aliases import register_underscore_alias

TOOL_NAMESPACE = "browser.automation"

def _ok(**fields: Any) -> dict[str, Any]:
    return {"success": True, **fields}

def _err(error: str, **fields: Any) -> dict[str, Any]:
    return {"success": False, "error": error, **fields}

class OrchestrationToolkit:
    def __init__(self, planner: ExecutionPlanner):
        self._planner = planner

    @tool(
        name=f"{TOOL_NAMESPACE}.execute",
        description=(
            "Deterministically execute a high-level browser workflow without manual DOM inspection. "
            "task can be 'login' or 'register'. parameters is a dictionary of fields to fill "
            "(e.g., {'url': 'https://example.com/login', 'username': 'admin', 'password': '123'})."
        ),
        returns="json",
    )
    async def execute_task(
        self,
        session_id: str,
        page_id: str,
        task: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a predefined high-level task."""
        try:
            result = await self._planner.execute_task(session_id, page_id, task, parameters)
            return _ok(**result)
        except Exception as exc:
            return _err(str(exc), session_id=session_id, page_id=page_id)

    def register(self, registry: Any) -> None:
        """Register tools with the registry."""
        registry.register(self.execute_task)
        register_underscore_alias(registry, self.execute_task, TOOL_NAMESPACE, "execute")


def build_orchestration_tools(planner: ExecutionPlanner) -> list[Callable[..., Any]]:
    toolkit = OrchestrationToolkit(planner)
    return [toolkit.execute_task]
