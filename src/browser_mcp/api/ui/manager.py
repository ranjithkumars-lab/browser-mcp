from browser_mcp.api.ui.adapter import WebSocketAdapter
from browser_mcp.api.ui.provider import WebSocketProvider
class UiManager:
    def adapter(self, provider: WebSocketProvider) -> WebSocketAdapter: return WebSocketAdapter(provider)
