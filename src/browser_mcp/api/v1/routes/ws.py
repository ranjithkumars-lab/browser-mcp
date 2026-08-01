from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from browser_mcp.api.ui.provider import FastAPIWebSocketProvider

router = APIRouter()


@router.websocket("/dashboard/ws")
async def dashboard_ws(socket: WebSocket) -> None:
    provider = FastAPIWebSocketProvider(socket)
    await provider.accept()
    try:
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        return
