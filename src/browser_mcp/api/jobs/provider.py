from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any
from browser_mcp.api.jobs.models import JobModel
class JobExecutionProvider(ABC):
    @abstractmethod
    async def run(self, job: JobModel, operation: Callable[[], Any]) -> Any: ...
class InMemoryJobProvider(JobExecutionProvider):
    async def run(self, job: JobModel, operation: Callable[[], Any]) -> Any:
        value = operation()
        if hasattr(value, "__await__"): return await value  # type: ignore[misc]
        return value
