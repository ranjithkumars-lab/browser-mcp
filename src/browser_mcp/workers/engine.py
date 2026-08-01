from __future__ import annotations

from enum import StrEnum
from typing import Any


class WorkerState(StrEnum):
    STARTING = "starting"
    READY = "ready"
    BUSY = "busy"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class WorkerEngine:
    def __init__(
        self, worker_id: str, broker: Any, executor: Any, events: Any | None = None
    ) -> None:
        self.worker_id, self.broker, self.executor, self.events = (
            worker_id,
            broker,
            executor,
            events,
        )
        self.state = WorkerState.STOPPED

    async def start(self) -> None:
        self.state = WorkerState.READY

    async def process_once(self) -> bool:
        payload = await self.broker.dequeue()
        if payload is None:
            return False
        self.state = WorkerState.BUSY
        try:
            await self.executor.execute(payload, payload.get("token"))
            await self.broker.ack(str(payload.get("job_id", "")))
            return True
        except Exception:
            await self.broker.nack(payload)
            self.state = WorkerState.FAILED
            return False
        finally:
            if self.state is WorkerState.BUSY:
                self.state = WorkerState.READY

    async def stop(self) -> None:
        self.state = WorkerState.STOPPED
