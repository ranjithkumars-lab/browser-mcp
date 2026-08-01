from __future__ import annotations
from typing import Any
from browser_mcp.workers.execution.retry import CancellationToken
class WorkerExecutor:
    def __init__(self, context: Any) -> None: self._context=context
    async def execute(self, payload: dict[str, Any], token: CancellationToken) -> Any:
        token.throw_if_cancelled()
        return await self._context.tools.call(payload["tool_name"], **payload.get("arguments", {}))
