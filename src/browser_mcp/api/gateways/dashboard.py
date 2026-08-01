from __future__ import annotations

import contextlib
import logging
from typing import Any

logger = logging.getLogger(__name__)


class DashboardGateway:
    def __init__(self, context: Any, engine: Any) -> None:
        self.context, self.engine = context, engine

    async def summary(self) -> dict[str, Any]:
        plugins = await self.context.tools.call("browser.plugins.list")
        workers: dict[str, Any] = {"available": False}
        with contextlib.suppress(Exception):
            workers = await self.context.container.resolve("worker_manager").status()
        try:
            jobs = list(self.engine.jobs._jobs.values())
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("failed to read job state", exc_info=exc)
            jobs = []
        return {
            "jobs": {
                "total": len(jobs),
                "running": sum(job.state.value == "running" for job in jobs),
                "failed": sum(job.state.value == "failed" for job in jobs),
            },
            "workers": workers,
            "plugins": plugins,
        }
