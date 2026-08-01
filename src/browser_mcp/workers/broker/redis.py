from __future__ import annotations
import asyncio
from typing import Any
from browser_mcp.workers.broker.provider import BrokerProvider
class RedisBrokerProvider(BrokerProvider):
    """In-memory compatible Redis-shaped provider; swap transport without callers changing."""
    def __init__(self) -> None: self._queues={k: asyncio.Queue[dict[str, Any]]() for k in ("high","default","low")}; self.dlq: list[dict[str, Any]]=[]
    async def enqueue(self,payload:dict[str,Any],priority:str="default")->None: await self._queues.get(priority,self._queues["default"]).put(payload)
    async def dequeue(self)->dict[str,Any]|None:
        for name in ("high","default","low"):
            if not self._queues[name].empty(): return self._queues[name].get_nowait()
        return None
    async def ack(self,job_id:str)->None: pass
    async def nack(self,payload:dict[str,Any])->None: self.dlq.append(payload)
