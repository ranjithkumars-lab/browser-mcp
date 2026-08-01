from __future__ import annotations
from typing import Any
class WorkerManager:
    def __init__(self, engine: Any) -> None:self.engine=engine
    async def start(self)->None:await self.engine.start()
    async def stop(self)->None:await self.engine.stop()
    async def status(self)->dict[str,str]:return {"worker_id":self.engine.worker_id,"state":self.engine.state.value}
