from __future__ import annotations
from typing import Any
class DashboardGateway:
    def __init__(self, context: Any, engine: Any) -> None: self.context,self.engine=context,engine
    async def summary(self) -> dict[str, Any]:
        plugins = await self.context.tools.call("browser.plugins.list")
        workers = {"available": False}
        try: workers = await self.context.container.resolve("worker_manager").status()
        except Exception: pass
        jobs = list(self.engine.jobs._jobs.values())
        return {
            "jobs": {"total": len(jobs), "running": sum(job.state.value == "running" for job in jobs),
                     "failed": sum(job.state.value == "failed" for job in jobs)},
            "workers": workers,
            "plugins": plugins,
        }
