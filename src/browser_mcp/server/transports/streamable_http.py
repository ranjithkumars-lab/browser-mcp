from __future__ import annotations

import asyncio
from typing import Any

from browser_mcp.server.transports.provider import TransportProvider


class StreamableHttpTransport(TransportProvider):
    def __init__(self, buffer_size: int = 1000) -> None:
        self._in: asyncio.Queue[dict[str, Any]] = asyncio.Queue(buffer_size)
        self._out: asyncio.Queue[dict[str, Any]] = asyncio.Queue(buffer_size)

    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def close(self) -> None:
        await self.stop()

    async def send(self, payload: dict[str, Any]) -> None:
        await self._out.put(payload)

    async def receive(self) -> dict[str, Any] | None:
        return await self._in.get()

    async def feed(self, payload: dict[str, Any]) -> None:
        await self._in.put(payload)

    async def next_response(self) -> dict[str, Any]:
        return await self._out.get()
