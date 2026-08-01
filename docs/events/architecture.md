# Events Architecture
- `BrowserEventManager`: The central facade for event dispatching.
- `EventBus`: The underlying pub/sub mechanism.
- `EventHistoryStore`: An in-memory/Redis backed store for historical events.
- `EventStreamAdapter`: Bridges internal events to external HTTP/SSE endpoints.
