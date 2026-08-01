from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

from browser_mcp.api.jobs.models import JobModel, JobState


class JobManager:
    def __init__(self, retention_minutes: int = 60) -> None:
        self._jobs: dict[str, JobModel] = {}
        self._tasks: dict[str, asyncio.Task[Any]] = {}
        self._retention = retention_minutes

    async def submit(self, type: str, operation: Callable[[], Any]) -> JobModel:
        job = JobModel(type=type)
        self._jobs[job.job_id] = job

        async def work() -> None:
            started = time.perf_counter()
            job.state = JobState.RUNNING
            job.started_at = datetime.now(UTC)
            try:
                value = operation()
                job.result = await value if inspect.isawaitable(value) else value
                job.state = JobState.COMPLETED
                job.progress = 100
            except asyncio.CancelledError:
                job.state = JobState.CANCELLED
                raise
            except Exception as exc:
                job.state = JobState.FAILED
                job.error = str(exc)
            finally:
                job.completed_at = datetime.now(UTC)
                job.duration_ms = (time.perf_counter() - started) * 1000

        self._tasks[job.job_id] = asyncio.create_task(work())
        return job

    def get(self, job_id: str) -> JobModel:
        return self._jobs[job_id]

    async def cancel(self, job_id: str) -> JobModel:
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
        return self.get(job_id)

    def cleanup(self) -> int:
        cutoff = datetime.now(UTC) - timedelta(minutes=self._retention)
        ids = [k for k, v in self._jobs.items() if v.completed_at and v.completed_at < cutoff]
        for key in ids:
            self._jobs[key].state = JobState.EXPIRED
        return len(ids)
