from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from browser_mcp.server.transports.provider import TransportProvider


class StdioTransport(TransportProvider):
    async def start(self) -> None:
        pass

    async def stop(self) -> None:
        pass

    async def close(self) -> None:
        await self.stop()

    async def send(self, payload: dict[str, Any]) -> None:
        sys.stdout.write(json.dumps(payload) + "\n")
        sys.stdout.flush()

    async def receive(self) -> dict[str, Any] | None:
        line = await asyncio.to_thread(sys.stdin.readline)
        return json.loads(line) if line else None
