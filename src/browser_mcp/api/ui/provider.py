from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any
class WebSocketProvider(ABC):
    @abstractmethod
    async def accept(self) -> None: ...
    @abstractmethod
    async def send_json(self, value: dict[str, Any]) -> None: ...
    @abstractmethod
    async def close(self) -> None: ...
class FastAPIWebSocketProvider(WebSocketProvider):
    def __init__(self, socket: Any) -> None: self.socket=socket
    async def accept(self)->None: await self.socket.accept()
    async def send_json(self,value:dict[str,Any])->None: await self.socket.send_json(value)
    async def close(self)->None: await self.socket.close()
